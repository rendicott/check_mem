# check_mem
Nagios plugin for checking available memory and swap on a *nix* machine. 

## Prerequisites
Requires custom nagpyrc library for generating the Nagios return codes and perfdata in the right format
```
pip install nagpyrc
```

## Usage

Usage:
Basic check with no arguments, defaults to warn on 90% memory usage and critical on 95% memory usage. Swap warning/critical defaults to 75% and 90% respectively. 
```
[root@SERVER] ~]# python check_mem.py
```
Output
```
OK MEMORY:::: Total: 1840 MB - Used: 148 MB - 8.07% used --- SWAP:::: Used: 1 MB - 0.07% used  ; | 'USED'=155623424B;;;; 'TOTAL'=1929613312B;;;; 'SWAP_USED'=1249280B;;;; 'SWAP_TOTAL'=1719660544B;;;; 'MEM_USED_PCT'=8.07%;;;; 'SWAP_USED_PCT'=0.07%;;;;
```

Check memory, warn at 3% usage, critical at 4% usage return proper Nagios return code if thresholds are reached.
```
[root@DOANTEST07 ~]# python check_mem.py -w 3 -c 4
```
Output
```
CRITICAL MEMORY:::: Total: 1840 MB - Used: 148 MB - 8.09% used --- SWAP:::: Used: 1 MB - 0.07% used  ; | 'USED'=156078080B;;;; 'TOTAL'=1929613312B;;;; 'SWAP_USED'=1249280B;;;; 'SWAP_TOTAL'=1719660544B;;;; 'MEM_USED_PCT'=8.09%;;;; 'SWAP_USED_PCT'=0.07%;;;;
```

check memory and gather perfdata but check will always return 1 "OK" even if threshold is reached
```
[root@DOANTEST07 ~]# python check_mem.py -w 3 -c 4 --perfdata_only yes
```
Output
```
OK MEMORY:::: Total: 1840 MB - Used: 148 MB - 8.08% used --- SWAP:::: Used: 1 MB - 0.07% used  ; | 'USED'=155918336B;;;; 'TOTAL'=1929613312B;;;; 'SWAP_USED'=1249280B;;;; 'SWAP_TOTAL'=1719660544B;;;; 'MEM_USED_PCT'=8.08%;;;; 'SWAP_USED_PCT'=0.07%;;;;

```
