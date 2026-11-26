# Transcript: daily bars dont match

Recorded 2026-11-26 04:06 UTC with databento 0.90.0, pandas 3.1.1 and Python 3.13.7 on Windows 11. Produced by `python cases/record.py`; nothing here was edited by hand.

`python cases/01-daily-bars-dont-match/run.py` (exit code 0)

```text

1. Databento's daily bars for ESZ6 (ohlcv-1d)
---------------------------------------------
Estimated cost before downloading: US$0.000059 for 6 records
.\cases\01-daily-bars-dont-match\run.py:39: BentoWarning: The streaming request contained one or more days which have reduced quality: 2026-11-15 (degraded). See: https://databento.com/docs/api-reference-historical/metadata/metadata-get-dataset-condition
  daily = hist.timeseries.get_range(schema="ohlcv-1d", **QUERY).to_df()
                              open     high      low    close   volume symbol
ts_event                                                                     
2026-11-15 00:00:00+00:00  7577.25  7614.25  7577.25  7610.75    18573   ESZ6
2026-11-16 00:00:00+00:00  7610.50  7613.00  7420.25  7445.00  1878486   ESZ6
2026-11-17 00:00:00+00:00  7445.25  7456.75  7308.00  7412.50  2181170   ESZ6
2026-11-18 00:00:00+00:00  7412.50  7415.50  7305.25  7372.25  1978740   ESZ6
2026-11-19 00:00:00+00:00  7372.50  7440.50  7167.75  7190.25  2486154   ESZ6
2026-11-20 00:00:00+00:00  7190.00  7216.75  6898.00  6966.75  2833183   ESZ6

2. The same week as hourly bars (ohlcv-1h)
------------------------------------------
Estimated cost before downloading: US$0.001140 for 115 records
.\cases\01-daily-bars-dont-match\run.py:44: BentoWarning: The streaming request contained one or more days which have reduced quality: 2026-11-15 (degraded). See: https://databento.com/docs/api-reference-historical/metadata/metadata-get-dataset-condition
  hourly = hist.timeseries.get_range(schema="ohlcv-1h", **QUERY).to_df()
115 hourly bars, from 2026-11-15 23:00:00+00:00 to 2026-11-20 21:00:00+00:00 (bar open times, UTC)

3. Check: hourly bars grouped by UTC day give back ohlcv-1d exactly
-------------------------------------------------------------------
ohlcv-1d equals hourly bars grouped by UTC day: True

4. The same week, rebuilt as CME sessions and as Penang days
------------------------------------------------------------
            UTC day close (ohlcv-1d)  CME session close  Penang day close  UTC day volume  CME session volume  Penang day volume
date                                                                                                                            
2026-11-15                   7610.75                NaN               NaN         18573.0                 NaN                NaN
2026-11-16                   7445.00            7438.50           7507.75       1878486.0           1883300.0           793662.0
2026-11-17                   7412.50            7366.50           7352.50       2181170.0           2167332.0          2054622.0
2026-11-18                   7372.25            7340.25           7344.00       1978740.0           1988423.0          2158172.0
2026-11-19                   7190.25            7182.50           7327.75       2486154.0           2484589.0          2050791.0
2026-11-20                   6966.75            6966.75           7110.25       2833183.0           2852662.0          2562126.0
2026-11-21                       NaN                NaN           6966.75             NaN                 NaN          1756933.0

5. Where each kind of day ends, in Penang time (November, US standard time)
---------------------------------------------------------------------------
CME session ends   16:00 Chicago = 22:00 UTC = 06:00 Penang the next morning
UTC day ends       00:00 UTC     = 08:00 Penang the next morning
Penang day ends    00:00 Penang  = 16:00 UTC = 10:00 Chicago
```
