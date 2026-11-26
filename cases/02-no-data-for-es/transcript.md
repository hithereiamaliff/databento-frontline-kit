# Transcript: no data for es

Recorded 2026-11-26 04:06 UTC with databento 0.90.0, pandas 3.1.1 and Python 3.13.7 on Windows 11. Produced by `python cases/record.py`; nothing here was edited by hand.

`python cases/02-no-data-for-es/run.py` (exit code 0)

```text

1. symbols="ES" on its own (schema ohlcv-1h)
--------------------------------------------
Rows returned: 0, for symbols: none
Warning from the client (BentoWarning): No data found for the request you submitted.
Warning from the client (BentoWarning): The streaming request had one or more symbols which did not resolve: ES.

2. symbols=["ES", "ESZ6"]: one resolves, one doesn't
----------------------------------------------------
Estimated cost before downloading: US$0.000228 for 23 records
Rows returned: 23, for symbols: ['ESZ6']
Warning from the client (BentoWarning): The streaming request had one or more symbols which did not resolve: ES.

3. What preflight says about symbols="ES"
-----------------------------------------
Databento preflight report
==========================
Dataset GLBX.MDP3  |  schema ohlcv-1h  |  stype_in raw_symbol
Symbols ES
Start "2026-11-23"  |  end "2026-11-24"  |  customer time zone UTC

[OK] API key accepted
[OK] Dataset GLBX.MDP3 exists
[OK] Schema ohlcv-1h is available for GLBX.MDP3
[INFO] The end is exclusive: the last record returned is just before Tue 2026-11-24 00:00
       UTC.
[OK] The whole window is inside the available range
[OK] Every day in the window is marked available (1 day)
[FAIL] "ES" didn't resolve to anything between 2026-11-23 and 2026-11-23.
       "ES" looks like a product root, but a raw symbol names one contract, such as ESZ6.
       For every ES contract, use "ES.FUT" with stype_in="parent". For the front month, use
       "ES.c.0" with stype_in="continuous".

The window in three time zones (start inclusive, end exclusive):
  UTC (as Databento reads it)  Mon 2026-11-23 00:00  to  Tue 2026-11-24 00:00
  America/Chicago (exchange)   Sun 2026-11-22 18:00  to  Mon 2026-11-23 18:00

Problems found: see FAIL lines.

4. Four ways to ask for ES on 2026-11-23
----------------------------------------
symbols  stype_in      instruments     1 day of trades
ES       raw_symbol              0           error 422
ESZ6     raw_symbol              1         US$1.243950
ES.c.0   continuous              1         US$1.243950
ES.FUT   parent                 41         US$1.254976

5. What ES.FUT covers on that day
---------------------------------
41 instruments: 21 outright contracts and 20 calendar spreads
Outrights: ESH0, ESH1, ESH7, ESH8, ESH9, ESM0, ESM1, ESM7, ESM8, ESM9, ESU0, ESU1, ESU7, ESU8, ESU9, ESZ0, ESZ1, ESZ6, ESZ7, ESZ8, ESZ9
Spreads, first ten: ESH7-ESH8, ESH7-ESM7, ESH7-ESU7, ESH7-ESZ7, ESH8-ESM8, ESH8-ESU8, ESM7-ESH8, ESM7-ESU7, ESM7-ESZ7, ESM8-ESU8
```
