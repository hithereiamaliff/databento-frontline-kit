# Transcript: bill higher than expected

Recorded 2026-11-26 04:07 UTC with databento 0.90.0, pandas 3.1.1 and Python 3.13.7 on Windows 11. Produced by `python cases/record.py`; nothing here was edited by hand.

`python cases/03-bill-higher-than-expected/run.py` (exit code 0)

```text

1. One day of ES.c.0, by schema (how much detail you ask for)
-------------------------------------------------------------
request                                      records  billable bytes        estimate
ohlcv-1h                                          23           1,288     US$0.000228
ohlcv-1m                                       1,380          77,280     US$0.005038
trades                                       993,810      47,702,880     US$1.243950
mbp-1                                     20,634,389   1,650,751,120     US$2.767287
mbo                                       31,247,145   1,749,840,120     US$2.933398
mbp-10                                    26,109,638   9,608,346,784     US$4.474235

2. Front month versus every contract and spread (a parent symbol)
-----------------------------------------------------------------
request                                      records  billable bytes        estimate
ES.c.0 trades                                993,810      47,702,880     US$1.243950
ES.FUT trades                              1,002,619      48,125,712     US$1.254976
ES.c.0 mbo                                31,247,145   1,749,840,120     US$2.933398
ES.FUT mbo                                34,986,161   1,959,225,016     US$3.284407
CL.c.0 mbo                                 5,750,103     322,005,768     US$0.539804
CL.FUT mbo                                38,051,819   2,130,901,864     US$3.572203

3. Ten-minute boundaries: ES.c.0 trades from 14:00 UTC to ...
-------------------------------------------------------------
request                                      records  billable bytes        estimate
... 14:10                                     33,246       1,595,808     US$0.041614
... 14:15                                     52,161       2,503,728     US$0.065290
... 14:20                                     52,161       2,503,728     US$0.065290

4. The 14:00 to 14:15 slice, downloaded: estimate versus what's sent
--------------------------------------------------------------------
Estimated cost before downloading: US$0.065290 for 52,161 records
Records actually sent: 43,714 (2,098,272 bytes uncompressed)
```
