# Transcript: monday starts at 8am

Recorded 2026-11-26 04:13 UTC with databento 0.90.0, pandas 3.1.1 and Python 3.13.7 on Windows 11. Produced by `python cases/record.py`; nothing here was edited by hand.

`python cases/06-monday-starts-at-8am/run.py` (exit code 0)

```text

1. As written: start="2026-11-23", end="2026-11-24"
---------------------------------------------------
Estimated cost before downloading: US$0.000228 for 23 records
23 hourly bars. First bar opens 2026-11-23 08:00:00+08:00, last bar opens 2026-11-24 07:00:00+08:00 (Penang time)

2. As meant: start="2026-11-23T00:00+08:00", end="2026-11-24T00:00+08:00"
-------------------------------------------------------------------------
Estimated cost before downloading: US$0.000168 for 17 records
.\cases\06-monday-starts-at-8am\run.py:27: BentoWarning: The streaming request contained one or more days which have reduced quality: 2026-11-22 (degraded). See: https://databento.com/docs/api-reference-historical/metadata/metadata-get-dataset-condition
  return hist.timeseries.get_range(start=start, end=end, **BASE).to_df(tz=PENANG)
17 hourly bars. First bar opens 2026-11-23 07:00:00+08:00, last bar opens 2026-11-23 23:00:00+08:00 (Penang time)

3. The difference, in Penang time
---------------------------------
Bars the customer wanted but didn't get (1):
  2026-11-23 07:00:00+08:00
Bars the customer got but didn't want (7), all on Tuesday morning:
  2026-11-24 00:00:00+08:00
  2026-11-24 01:00:00+08:00
  2026-11-24 02:00:00+08:00
  2026-11-24 03:00:00+08:00
  2026-11-24 04:00:00+08:00
  2026-11-24 05:00:00+08:00
  2026-11-24 07:00:00+08:00

4. What preflight says about the request as written
---------------------------------------------------
Databento preflight report
==========================
Dataset GLBX.MDP3  |  schema ohlcv-1h  |  stype_in raw_symbol
Symbols ESZ6
Start "2026-11-23"  |  end "2026-11-24"  |  customer time zone Asia/Kuala_Lumpur

[OK] API key accepted
[OK] Dataset GLBX.MDP3 exists
[OK] Schema ohlcv-1h is available for GLBX.MDP3
[WARN] "2026-11-23" has no time zone, so Databento reads it as Mon 2026-11-23 00:00 UTC.
       That's Mon 2026-11-23 08:00 in Asia/Kuala_Lumpur. If you meant Asia/Kuala_Lumpur
       time, send "2026-11-23T00:00:00+08:00" instead. Likewise "2026-11-24" is Tue
       2026-11-24 00:00 UTC, which is Tue 2026-11-24 08:00 in Asia/Kuala_Lumpur. For
       Asia/Kuala_Lumpur time, use "2026-11-24T00:00:00+08:00".
[INFO] The end is exclusive: the last record returned is just before Tue 2026-11-24 00:00
       UTC.
[OK] The whole window is inside the available range
[OK] Every day in the window is marked available (1 day)
[OK] ESZ6 resolves to instrument_id 10252
[INFO] Estimated cost US$0.000228 for 23 records (1,288 billable bytes).
       Nothing has been downloaded. Billing is on the uncompressed binary size, whatever
       encoding you ask for.

The window in three time zones (start inclusive, end exclusive):
  UTC (as Databento reads it)   Mon 2026-11-23 00:00  to  Tue 2026-11-24 00:00
  Asia/Kuala_Lumpur (customer)  Mon 2026-11-23 08:00  to  Tue 2026-11-24 08:00
  America/Chicago (exchange)    Sun 2026-11-22 18:00  to  Mon 2026-11-23 18:00

No blocking problems found.
```
