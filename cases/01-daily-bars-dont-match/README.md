# 01. "My daily bars don't match my broker's chart"

**Kind:** documented behaviour, worth an FAQ entry for APAC users.

## The question

> I downloaded `ohlcv-1d` for ESZ6 for last week and compared it with my broker's daily chart. Every close is different, and there's a tiny Sunday bar with almost no volume. Is the data wrong?

## The reply I'd send

> Hi! The data's fine, but it's cut into days differently from your broker's chart.
>
> Databento's `ohlcv-1d` bars are UTC days, 00:00 to 24:00 UTC, which is 8am to 8am in Penang. Futures charts usually show CME trading sessions instead, which run from 17:00 to 16:00 Chicago time (7am to 6am in Penang at the moment). Because the days start and end at different times, the closes differ. On Tuesday 17 November, for example, the UTC-day close for ESZ6 was 7412.50, and the last trade of the CME session was 7366.50.
>
> The tiny Sunday bar is the first hour of Monday's session. CME reopens at 17:00 on Sunday in Chicago, which is 23:00 UTC, so that hour falls inside Sunday's UTC day.
>
> If you'd like session bars, request hourly bars and group them by trading date:
>
> ```python
> import pandas as pd
>
> hourly = client.timeseries.get_range(
>     dataset="GLBX.MDP3", schema="ohlcv-1h", symbols=["ESZ6"],
>     start="2026-11-15", end="2026-11-21",
> ).to_df()
>
> # Adding 7 hours to Chicago time moves the 17:00 open to midnight,
> # so every hour lands on its trading date.
> trading_date = (hourly.index.tz_convert("America/Chicago") + pd.Timedelta(hours=7)).date
> sessions = hourly.groupby(trading_date).agg(
>     open=("open", "first"), high=("high", "max"), low=("low", "min"),
>     close=("close", "last"), volume=("volume", "sum"),
> )
> ```
>
> This works for products that open at 17:00 Chicago time, like ES. One more thing: these are last-trade closes, not CME's official settlement prices, so a chart built on settlements will still differ a little.

## What the run showed

From [transcript.md](transcript.md), recorded 26 Nov 2026:

- Hourly bars grouped by UTC day reproduce Databento's `ohlcv-1d` bars exactly. That matches the docs: "Our ohlcv-1d schema is based on UTC dates."
- The same week gives three different sets of closes:

  | Date | UTC day (`ohlcv-1d`) | CME session | Penang day |
  |---|---|---|---|
  | Mon 16 Nov | 7445.00 | 7438.50 | 7507.75 |
  | Tue 17 Nov | 7412.50 | 7366.50 | 7352.50 |
  | Wed 18 Nov | 7372.25 | 7340.25 | 7344.00 |
  | Thu 19 Nov | 7190.25 | 7182.50 | 7327.75 |
  | Fri 20 Nov | 6966.75 | 6966.75 | 7110.25 |

- The Sunday 15 Nov bar holds 18,573 contracts: the first hour of Monday's session.
- A customer in Penang would even see a "Saturday" with 1,756,933 contracts, because Friday's US session ends at 6am on Saturday in Penang.
- The client warned that Sunday 15 Nov is flagged "degraded". Every Sunday in November carries that flag; see [known issues](../known-issues.md#every-sunday-in-november-is-flagged-degraded-on-glbxmdp3).
- Cost: US$0.001199 for both downloads.

## Run it

```text
python cases/01-daily-bars-dont-match/run.py
```
