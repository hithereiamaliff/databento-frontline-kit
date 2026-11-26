# Transcript: nan symbols issue 147

Recorded 2026-11-26 04:20 UTC with databento 0.90.0, pandas 3.1.1 and Python 3.13.7 on Windows 11. Produced by `python cases/record.py`; nothing here was edited by hand.

`python cases/05-nan-symbols-issue-147/offline_repro.py` (exit code 0)

```text
databento 0.90.0
Python 3.13.7

Which symbol does instrument 42140870 carry on each date?
(ES.c.0 covers 14 to 19 Sep, ES.v.0 covers 14 to 15 Sep; d1 is exclusive)

date        expected           ES.c.0 listed first   ES.v.0 listed first   ES.c.0 alone
2026-09-14  ES.c.0 or ES.v.0   ES.v.0                ES.c.0                ES.c.0
2026-09-15  ES.c.0 or ES.v.0   ES.v.0                ES.c.0                ES.c.0
2026-09-16  ES.c.0             None                  ES.c.0                ES.c.0
2026-09-17  ES.c.0             None                  ES.c.0                ES.c.0
2026-09-18  ES.c.0             None                  ES.c.0                ES.c.0
2026-09-19  ES.c.0             None                  ES.c.0                ES.c.0

Rows that lose their symbol when ES.c.0 is listed first: 4 of 6
```

`python cases/05-nan-symbols-issue-147/run.py` (exit code 0)

```text

1. What each symbol pointed at (symbology.resolve, free)
--------------------------------------------------------
ES.c.0: instrument 42140870 from 2026-09-14 to 2026-09-20 (end exclusive)
ES.c.0: instrument 10252 from 2026-09-20 to 2026-09-24 (end exclusive)
ES.v.0: instrument 42140870 from 2026-09-14 to 2026-09-16 (end exclusive)
ES.v.0: instrument 10252 from 2026-09-16 to 2026-09-24 (end exclusive)

2. The customer's request: both symbols at once, downloaded once
----------------------------------------------------------------
Estimated cost before downloading: US$0.000178 for 18 records
The same download, converted with to_df() 10 times (like re-running a notebook cell):
  call  1: rows with no symbol: 0 of 12
  call  2: rows with no symbol: 3 of 12
  call  3: rows with no symbol: 0 of 12
  call  4: rows with no symbol: 0 of 12
  call  5: rows with no symbol: 3 of 12
  call  6: rows with no symbol: 3 of 12
  call  7: rows with no symbol: 3 of 12
  call  8: rows with no symbol: 3 of 12
  call  9: rows with no symbol: 0 of 12
  call 10: rows with no symbol: 0 of 12

One of the calls that lost symbols:
                           instrument_id  symbol    close
ts_event                                                 
2026-09-14 00:00:00+00:00       42140870  ES.v.0  7628.50
2026-09-15 00:00:00+00:00       42140870  ES.v.0  7598.50
2026-09-16 00:00:00+00:00          10252  ES.v.0  7657.25
2026-09-16 00:00:00+00:00       42140870     NaN  7590.00
2026-09-17 00:00:00+00:00          10252  ES.v.0  7700.75
2026-09-17 00:00:00+00:00       42140870     NaN  7635.50
2026-09-18 00:00:00+00:00          10252  ES.v.0  7725.00
2026-09-18 00:00:00+00:00       42140870     NaN  7643.25
2026-09-20 00:00:00+00:00          10252  ES.c.0  7734.50
2026-09-21 00:00:00+00:00          10252  ES.c.0  7835.25
2026-09-22 00:00:00+00:00          10252  ES.c.0  7833.50
2026-09-23 00:00:00+00:00          10252  ES.c.0  7768.25

3. Why it comes and goes: the order of store.metadata.mappings, read 40 times
-----------------------------------------------------------------------------
  ES.v.0, ES.c.0: 21 times
  ES.c.0, ES.v.0: 19 times
On every to_df() call, the client adds these mappings to its symbol map in whatever
order they come back. The lookup bug in #147 only bites in one of the orders.

4. Workaround: one request per symbol
-------------------------------------
Estimated cost before downloading: US$0.000089 for 9 records
Estimated cost before downloading: US$0.000089 for 9 records
                           instrument_id  symbol    close
ts_event                                                 
2026-09-14 00:00:00+00:00       42140870  ES.c.0  7628.50
2026-09-14 00:00:00+00:00       42140870  ES.v.0  7628.50
2026-09-15 00:00:00+00:00       42140870  ES.c.0  7598.50
2026-09-15 00:00:00+00:00       42140870  ES.v.0  7598.50
2026-09-16 00:00:00+00:00       42140870  ES.c.0  7590.00
2026-09-16 00:00:00+00:00          10252  ES.v.0  7657.25
2026-09-17 00:00:00+00:00       42140870  ES.c.0  7635.50
2026-09-17 00:00:00+00:00          10252  ES.v.0  7700.75
2026-09-18 00:00:00+00:00       42140870  ES.c.0  7643.25
2026-09-18 00:00:00+00:00          10252  ES.v.0  7725.00
2026-09-20 00:00:00+00:00          10252  ES.c.0  7734.50
2026-09-20 00:00:00+00:00          10252  ES.v.0  7734.50
2026-09-21 00:00:00+00:00          10252  ES.c.0  7835.25
2026-09-21 00:00:00+00:00          10252  ES.v.0  7835.25
2026-09-22 00:00:00+00:00          10252  ES.c.0  7833.50
2026-09-22 00:00:00+00:00          10252  ES.v.0  7833.50
2026-09-23 00:00:00+00:00          10252  ES.c.0  7768.25
2026-09-23 00:00:00+00:00          10252  ES.v.0  7768.25

Rows with no symbol: 0 of 18
```
