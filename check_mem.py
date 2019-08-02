#!/usr/bin/env python3
'''
Checks total available and free memory
as a replacement for check_mem.sh

Usage:
# check memory, warn at 90% usage, critical at 95% usage, warn/crit swap at 30%/40% usage
#  return proper Nagios return code if thresholds are reached
python check_mem.py -w 90 -c 95 --swap_warn_percentage 30 --swap_crit_percentage 40 --perfdata_only no

# check memory and gather perfdata but check will always return 1 "OK" even if memory is 100% used
python check_mem.py --perfdata_only yes


'''

import logging
import sys
import os
import time
import unittest
import subprocess
from optparse import OptionParser, OptionGroup
from datetime import datetime
from datetime import timedelta

from distutils.version import LooseVersion

from nagpyrc import NagiosReturn
from nagpyrc import PerfChunk
from nagpyrc import NagiosReturnCode

sversion = 'v0.1'
scriptfilename = os.path.basename(sys.argv[0])
defaultlogfilename = scriptfilename + '.log'


def setuplogging(loglevel, printtostdout, logfile):
    # pretty self explanatory. Takes options and sets up logging.
    # print "starting up with loglevel",loglevel,logging.getLevelName(loglevel)
    logging.basicConfig(filename=logfile,
                        filemode='w', level=loglevel,
                        format='%(asctime)s:%(levelname)s:%(message)s')
    if printtostdout:
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(loglevel)
        logger = logging.getLogger()
        logger.addHandler(soh)


def execute_command(commandstring):
    try:
        output = subprocess.Popen(commandstring, stdout=subprocess.PIPE)
        return(output)
    except Exception as e:
        msg = "Exception calling command: '%s' , Exception: %s" % (
            commandstring, str(e))
        logging.debug(msg)
        return(msg)


class Test_crit_warn(unittest.TestCase):

    def test_all_good(self):
        # MemoryState(total,used,free,shared,buffcache,swap_total,swap_used,swap_free,available)
        m = MemoryState(8000, 100, 100, 1, 1, 2000, 0, 2000, None)
        mem_warn_value = 90.00
        mem_crit_value = 95.00
        swap_warn_value = 80.00
        swap_crit_value = 90.00
        return_value = m.within_critwarn_range(
            mem_warn_value, mem_crit_value, swap_warn_value, swap_crit_value)
        expected_value = 0
        self.assertEqual(return_value, expected_value)

    def test_mem_warn(self):
        # MemoryState(total,used,free,shared,buffcache,swap_total,swap_used,swap_free,available)
        m = MemoryState(8000, 7300, 100, 1, 1, 2000, 0, 2000, None)
        mem_warn_value = 90.00
        mem_crit_value = 95.00
        swap_warn_value = 80.00
        swap_crit_value = 90.00
        return_value = m.within_critwarn_range(
            mem_warn_value, mem_crit_value, swap_warn_value, swap_crit_value)
        expected_value = 1
        self.assertEqual(return_value, expected_value)

    def test_mem_crit(self):
        # MemoryState(total,used,free,shared,buffcache,swap_total,swap_used,swap_free,available)
        m = MemoryState(8000, 7900, 100, 1, 1, 2000, 0, 2000, None)
        mem_warn_value = 90.00
        mem_crit_value = 95.00
        swap_warn_value = 80.00
        swap_crit_value = 90.00
        return_value = m.within_critwarn_range(
            mem_warn_value, mem_crit_value, swap_warn_value, swap_crit_value)
        expected_value = 2
        self.assertEqual(return_value, expected_value)

    def test_swap_warn(self):
        # MemoryState(total,used,free,shared,buffcache,swap_total,swap_used,swap_free,available)
        m = MemoryState(8000, 2000, 6000, 1, 1, 2000, 1800, 200, None)
        mem_warn_value = 90.00
        mem_crit_value = 95.00
        swap_warn_value = 80.00
        swap_crit_value = 90.00
        return_value = m.within_critwarn_range(
            mem_warn_value, mem_crit_value, swap_warn_value, swap_crit_value)
        expected_value = 1
        self.assertEqual(return_value, expected_value)

    def test_swap_crit(self):
        # MemoryState(total,used,free,shared,buffcache,swap_total,swap_used,swap_free,available)
        m = MemoryState(8000, 2000, 6000, 1, 1, 2000, 1900, 200, None)
        mem_warn_value = 90.00
        mem_crit_value = 95.00
        swap_warn_value = 80.00
        swap_crit_value = 90.00
        return_value = m.within_critwarn_range(
            mem_warn_value, mem_crit_value, swap_warn_value, swap_crit_value)
        expected_value = 2
        self.assertEqual(return_value, expected_value)

    def test_swap_trumps_mem(self):
        # MemoryState(total,used,free,shared,buffcache,swap_total,swap_used,swap_free,available)
        m = MemoryState(8000, 7300, 6000, 1, 1, 2000, 1900, 200, None)
        mem_warn_value = 90.00
        mem_crit_value = 95.00
        swap_warn_value = 80.00
        swap_crit_value = 90.00
        return_value = m.within_critwarn_range(
            mem_warn_value, mem_crit_value, swap_warn_value, swap_crit_value)
        expected_value = 2
        self.assertEqual(return_value, expected_value)

    def test_mem_trumps_swap(self):
        # MemoryState(total,used,free,shared,buffcache,swap_total,swap_used,swap_free,available)
        m = MemoryState(8000, 7900, 6000, 1, 1, 2000, 100, 200, None)
        mem_warn_value = 90.00
        mem_crit_value = 95.00
        swap_warn_value = 80.00
        swap_crit_value = 90.00
        return_value = m.within_critwarn_range(
            mem_warn_value, mem_crit_value, swap_warn_value, swap_crit_value)
        expected_value = 2
        self.assertEqual(return_value, expected_value)

    def test_bad_warn_value_returns_unknown(self):
        # MemoryState(total,used,free,shared,buffcache,swap_total,swap_used,swap_free,available)
        m = MemoryState(8000, 7900, 6000, 1, 1, 2000, 100, 200, None)
        mem_warn_value = '90%'
        mem_crit_value = 95.00
        swap_warn_value = 80.00
        swap_crit_value = 90.00
        return_value = m.within_critwarn_range(
            mem_warn_value, mem_crit_value, swap_warn_value, swap_crit_value)
        expected_value = 3
        self.assertEqual(return_value, expected_value)


class MemoryState():
    '''
    Holds state of memory regardless of the free type
    '''

    def __init__(self, total, used, free, shared, buffcache, swap_total, swap_used, swap_free, available):
        self.total = total
        self.used = used
        self.free = free
        self.shared = shared
        self.buffcache = buffcache
        self.swap_total = swap_total
        self.swap_used = swap_used
        self.swap_free = swap_free
        if available is None:
            self.available = self.determine_available()
        else:
            self.available = available
        (self.mem_used_percentage,
            self.mem_used_percentage_string,
            self.swap_used_percentage,
            self.swap_used_percentage_string) = self.determine_used_percentages()

    def dumpself(self):
        msg = 'MemoryStatus\n'
        msg += ' TOTAL: %s\n' % str(self.total)
        msg += ' USED: %s\n' % str(self.used)
        msg += ' SHARED: %s\n' % str(self.shared)
        msg += ' BUFFCACHE: %s\n' % str(self.buffcache)
        msg += ' AVAILABLE: %s\n' % str(self.available)
        msg += ' SWAP_TOTAL: %s\n' % str(self.swap_total)
        msg += ' SWAP_USED: %s\n' % str(self.swap_used)
        msg += ' SWAP_FREE: %s\n' % str(self.swap_free)
        msg += ' MEM_USED_PCT_STRING: %s\n' % str(
            self.mem_used_percentage_string)
        msg += ' SWAP_USED_PCT_STRING: %s\n' % str(
            self.swap_used_percentage_string)
        return(msg)

    def determine_available(self):
        available = self.total - self.used
        if available < 0:
            available = 0
        return available

    def determine_used_percentages(self):
        logging.info("Entering determine_used_percentages()")
        mem_used = float(100)
        swap_used = float(100)
        try:
            mem_used = (float(self.used) / float(self.total)) * float(100)
            mem_used_str = str("%.2f" % round(mem_used, 2))
        except Exception as er:
            logging.critical("Exception: " + str(er))
        if self.swap_total != 0:
            try:
                swap_used = (float(self.swap_used) /
                             float(self.swap_total)) * float(100)
                swap_used_str = str("%.2f" % round(swap_used, 2))
            except Exception as orf:
                logging.critical("Exception: " + str(orf))
        else:
            swap_used = float(0)
            swap_used_str = '0.0'
        return mem_used, mem_used_str, swap_used, swap_used_str

    def within_critwarn_range(self, mem_warn, mem_crit, swap_warn, swap_crit):
        # set returncode unknown until proven otherwise
        returncode_mem = 3
        returncode_swap = 3
        returncode = 3
        try:
            logging.info("Entering within_crit_warn_range with rc %s" %
                         str(returncode))
            logging.info(
                "Entering within_crit_warn_range with mem_warn %s" % str(mem_warn))
            logging.info(
                "Entering within_crit_warn_range with mem_crit %s" % str(mem_crit))
            logging.info(
                "Entering within_crit_warn_range with swap_warn %s" % str(swap_warn))
            logging.info(
                "Entering within_crit_warn_range with swap_crit %s" % str(swap_crit))
            mem_warn = float(mem_warn)
            mem_crit = float(mem_crit)
            swap_warn = float(swap_warn)
            swap_crit = float(swap_crit)
            if self.swap_used_percentage > swap_warn:
                returncode_swap = 1
            else:
                returncode_swap = 0
            if self.swap_used_percentage > swap_crit:
                returncode_swap = 2

            if self.mem_used_percentage > mem_warn:
                returncode_mem = 1
            else:
                returncode_mem = 0
            if self.mem_used_percentage > mem_crit:
                returncode_mem = 2

            if returncode_mem == 1 or returncode_swap == 1:
                returncode = 1
            if returncode_mem == 2 or returncode_swap == 2:
                returncode = 2

            if returncode_swap == 0 and returncode_mem == 0:
                returncode = 0

            logging.info(
                "Leaving within_crit_warn_range with rc_mem %s" % str(returncode_mem))
            logging.info(
                "Leaving within_crit_warn_range with rc_swap %s" % str(returncode_swap))
            logging.info("Leaving within_crit_warn_range with rc %s" %
                         str(returncode))
        except Exception as e:
            logging.info(
                "Exception warn/crit as floats or warn/crit compare error: %s" % str(e))
        return returncode

    def convert_bytes_to_mb(self):
        # takes mem total and used and returns values in MB
        total = self.total / 1024 / 1024
        used = self.used / 1024 / 1024
        swap_used = self.swap_used / 1024 / 1024
        return(total, used, swap_used)


def process_results(free_version, r):
    '''
    Based on results and type make a MemoryState object
    Sample output type centos7:
                          total        used        free      shared  buff/cache   available
        Mem:           1840         134         976          88         729        1427
        Swap:          1639           0        1639

    Sample output type standard:
                     total       used       free     shared    buffers     cached
        Mem:          7984       2986       4998         11        192       1210
        -/+ buffers/cache:       1583       6401
        Swap:         1023          0       1023
    '''
    available = None
    for line in r:
        #if 'Mem:' in line:
        if b'Mem:' in line:
            #cleanline = line.replace('\n', '')
            cleanline = line.decode('unicode-escape').replace('\n', '')
            chunks = cleanline.split(' ')
            clean_chunks = [x for x in chunks if x != '']

            total = int(clean_chunks[1])
            used = int(clean_chunks[2])
            free = int(clean_chunks[3])
            shared = int(clean_chunks[4])
            if LooseVersion(free_version) > LooseVersion('3.3.9'):
                buffcache = int(clean_chunks[5])
                available = int(clean_chunks[6])
            else:
                buffcache = int(clean_chunks[5]) + int(clean_chunks[6])
                used = used - buffcache

        #if 'Swap:' in line:
        if b'Swap:' in line:
            #cleanline = line.replace('\n', '')
            cleanline = line.decode('unicode-escape').replace('\n', '')
            chunks = cleanline.split(' ')
            clean_chunks = [x for x in chunks if x != '']
            swap_total = int(clean_chunks[1])
            swap_used = int(clean_chunks[2])
            swap_free = int(clean_chunks[3])
    m = MemoryState(total, used, free, shared, buffcache,
                    swap_total, swap_used, swap_free, available)
    return m


def main(options):
    ''' The main() method. Program starts here.
    '''

    version = execute_command(['free', '-V'])
    version_line = version.stdout.readline()
    free_version = version_line.split()[-1]

    results = execute_command(['free', '-b'])

    # default the type of the free command to 'standard'
    # we'll set to centos7 if we detect as such
    # technically versions are as follows:
    #    All other OS's: 'free from procps-ng 3.3.9'
    #    CentOS:         'free from procps-ng 3.3.10'
    rlist = []
    for line in results.stdout.readlines():
        rlist.append(line)

    logging.info("Output from 'free' command is of version: '%s'" % free_version)

    #memstats = process_results(free_version, rlist)
    memstats = process_results(free_version.decode('unicode-escape'), rlist)

    logging.info(memstats.dumpself())

    # take options and make smaller names
    try:
        mw = float(options.mem_warn_percentage)
        mc = float(options.mem_crit_percentage)
        sw = float(options.swap_warn_percentage)
        sc = float(options.swap_crit_percentage)
    except Exception as ar:
        logging.info(
            "Exception casting warn/crits as floats in main: %s" % str(ar))

    if options.perfdata_only.lower() == 'no':
        # pass in to check within ranges
        nagios_rc = memstats.within_critwarn_range(mw, mc, sw, sc)
    else:
        nagios_rc = 0

    # sample current return string
    # Memory: OK Total: 1840 MB - Used: -1310 MB - -71%
    # used|TOTAL=1929613312;;;; USED=-1374179328;;;; CACHE=1510100992;;;;
    # BUFFER=755486720;;;;
    perfdata = []
    pc_used = PerfChunk(stringname='USED', value=memstats.used, unit='B')
    perfdata.append(pc_used)

    pc_total = PerfChunk(stringname='TOTAL', value=memstats.total, unit='B')
    perfdata.append(pc_total)

    pc_swap_used = PerfChunk(stringname='SWAP_USED',
                             value=memstats.swap_used, unit='B')
    perfdata.append(pc_swap_used)

    pc_swap_total = PerfChunk(stringname='SWAP_TOTAL',
                              value=memstats.swap_total, unit='B')
    perfdata.append(pc_swap_total)

    pc_mem_used_pct = PerfChunk(
        stringname='MEM_USED_PCT', value=memstats.mem_used_percentage_string, unit='%')
    perfdata.append(pc_mem_used_pct)

    pc_swap_used_pct = PerfChunk(
        stringname='SWAP_USED_PCT', value=memstats.swap_used_percentage_string, unit='%')
    perfdata.append(pc_swap_used_pct)

    (mem_total_mb, mem_used_mb, swap_used_mb) = memstats.convert_bytes_to_mb()
    msgstring = ("MEMORY:::: Total: %s MB - Used: %s MB - %s%% used --- "
                 "SWAP:::: Used: %s MB - %s%% used" % (mem_total_mb,
                                                       mem_used_mb,
                                                       memstats.mem_used_percentage_string,
                                                       swap_used_mb,
                                                       memstats.swap_used_percentage_string)
                 )
    logging.info("Current RC = %s" % str(nagios_rc))
    nm = NagiosReturnCode(returncode=nagios_rc, msgstring=msgstring)
    nm.returnCode = nagios_rc
    for pc in perfdata:
        nm.perfChunkList.append(pc)

    nm.genreturncode()
    '''
    # add a perfdata chunk for total response time
    pd = PerfChunk(stringname='response_time',value=response_time,unit='s')
    # add it to the list of response perfdata
    perfdata.append(pd)
    # build your nagios message and tell it to be warn,crit,ok, etc.
    # we'll start with a default of 1 which is warning
    msgstring = "Elasticsearch Cluster Health API: " + str(status_code) + " " + str(status_string)
    nm = NagiosReturnCode(returncode=1,msgstring=msgstring)
    if status_code == 200:
        nm.returnCode = 0
    else:
        nm.returnCode = 1
    # append your perfdata chunks to the NagiosReturnCode object.
    for perfchunk in perfdata:
        nm.perfChunkList.append(perfchunk)
    nm.genreturncode() # will raise a 'NagiosReturn' exception
    '''

if __name__ == '__main__':
    # unittest.main()
    '''This main section is mostly for parsing arguments to the
    script and setting up debugging'''
    from optparse import OptionParser
    '''set up an additional option group just for debugging parameters'''
    from optparse import OptionGroup
    usage = (
        "%prog [--debug] [--printtostdout] [--logfile] [--version] [--help] [--samplefileoption]")
    # set up the parser object
    parser = OptionParser(usage, version='%prog ' + sversion)
    parser.add_option('-w', '--mem_warn_percentage',
                      type='string',
                      help=(
                          "Warning threshold percentage for used memory. Default='90'"),
                      default='90')
    parser.add_option('-c', '--mem_crit_percentage',
                      type='string',
                      help=(
                          "Critical threshold percentage for used memory. Default='95'"),
                      default='95')
    parser.add_option('--swap_warn_percentage',
                      type='string',
                      help=(
                          "Warning threshold percentage for used swap. Default='75'"),
                      default='75')
    parser.add_option('--swap_crit_percentage',
                      type='string',
                      help=(
                          "Critical threshold percentage for used swap. Default='90'"),
                      default='90')
    parser.add_option('--perfdata_only',
                      type='string',
                      help=("Options are 'no' or 'yes'. When yes then check will always "
                            "return OK. Default='no'"),
                      default='no')
    parser_debug = OptionGroup(parser, 'Debug Options')
    parser_debug.add_option('-d', '--debug', type='string',
                            help=('Available levels are CRITICAL (3), ERROR (2), '
                                  'WARNING (1), INFO (0), DEBUG (-1)'),
                            default='CRITICAL')
    parser_debug.add_option('-p', '--printtostdout', action='store_true',
                            default=False, help='Print all log messages to stdout')
    parser_debug.add_option('-l', '--logfile', type='string', metavar='FILE',
                            help=('Desired filename of log file output. Default '
                                  'is "' + defaultlogfilename + '"'), default=defaultlogfilename)
    # officially adds the debuggin option group
    parser.add_option_group(parser_debug)
    options, args = parser.parse_args()  # here's where the options get parsed

    try:  # now try and get the debugging options
        loglevel = getattr(logging, options.debug)
    except AttributeError:  # set the log level
        loglevel = {3: logging.CRITICAL,
                    2: logging.ERROR,
                    1: logging.WARNING,
                    0: logging.INFO,
                    -1: logging.DEBUG,
                    }[int(options.debug)]

    try:
        open(options.logfile, 'w')  # try and open the default log file
    except:
        # print "Unable to open log file '%s' for writing." % options.logfile
        logging.debug(
            "Unable to open log file '%s' for writing." % options.logfile)

    setuplogging(loglevel, options.printtostdout, options.logfile)
    # now launch the main method. Have to do a try catch for Nagios
    #  to properly see the application's exit return code.

    try:
        main(options)
    #except NagiosReturn, e:
    except NagiosReturn as e:
        #print e.message
        print(e.message)
        sys.exit(e.code)
