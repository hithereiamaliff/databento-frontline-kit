# 06. "I asked for Monday, but my data starts at 8am"

**Kind:** user error; documented ("All dates and times used as parameters are in UTC by default"). The most common APAC-hours question I'd expect.

## The question

> I'm in Penang. I asked for `start="2026-11-23", end="2026-11-24"` to get Monday's hourly ES bars. The first bar is at 8am, and I'm also getting bars from Tuesday morning. Where's the start of my Monday?

## The reply I'd send

> Hi! Databento reads dates and times as UTC unless you say otherwise, and "2026-11-23" means midnight UTC, which is 8am in Penang. So your window ran from 8am Monday to 8am Tuesday, Penang time. That's why you got Tuesday's early hours and missed Monday's first bar at 7am, when CME opened for the week (17:00 on Sunday in Chicago).
>
> To ask for your own day, add your UTC offset. You can also have `to_df` show the times in Penang time:
>
> ```python
> df = client.timeseries.get_range(
>     dataset="GLBX.MDP3", schema="ohlcv-1h", symbols=["ESZ6"],
>     start="2026-11-23T00:00+08:00", end="2026-11-24T00:00+08:00",
> ).to_df(tz="Asia/Kuala_Lumpur")
> ```
>
> The end is exclusive, so that stops just before midnight.

## What the run showed

From [transcript.md](transcript.md), recorded 26 Nov 2026:

| | As written (`2026-11-23` to `2026-11-24`) | As meant (`+08:00`) |
|---|---|---|
| Bars | 23 | 17 |
| First bar (Penang time) | Mon 08:00 | Mon 07:00 |
| Last bar (Penang time) | Tue 07:00 | Mon 23:00 |

- **Missed:** Monday's 07:00 bar, which is the weekly open.
- **Unwanted:** seven Tuesday-morning bars, 00:00 to 07:00. There's no 06:00 bar, because that's CME's daily break (16:00 to 17:00 in Chicago).
- **The API accepts offsets** such as `+08:00`, although the docs' examples only show UTC.
- **preflight** caught the request as written. It gave a WARN with the exact strings to send instead, and a table of the window in UTC, Penang time and Chicago time.
- **The data-quality flag:** the "as meant" window reaches back into Sunday 22 Nov in UTC, so the client warned that the day is flagged "degraded". See [known issues](../known-issues.md#every-sunday-in-november-is-flagged-degraded-on-glbxmdp3).
- Cost: US$0.000396 for both downloads.

## Run it

```text
python cases/06-monday-starts-at-8am/run.py
python preflight.py --dataset GLBX.MDP3 --schema ohlcv-1h --symbols ESZ6 --start 2026-11-23 --end 2026-11-24 --tz Asia/Kuala_Lumpur
```
