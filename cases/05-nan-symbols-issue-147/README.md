# 05. "to_df() gives me NaN symbols" (issue #147)

**Kind:** a bug in databento-python, open as [#147](https://github.com/databento/databento-python/issues/147) since 24 Nov 2026. It affects versions 0.68.1 to 0.90.0.

## The question

> I request ES.c.0 and ES.v.0 together, and some rows come back with `symbol` as NaN. When I re-run the cell it's sometimes fine. What's going on?

## The reply I'd send

> Hi! Thanks for the clear report. It's a known bug in the Python client, not a problem with your data: [issue #147 on GitHub](https://github.com/databento/databento-python/issues/147). When two of your symbols point at the same contract on some days, the client can lose the label for those rows. Whether it happens depends on an internal ordering that changes from one call to the next, which is why re-running sometimes "fixes" it.
>
> Until there's a fix, request each symbol separately and combine the results:
>
> ```python
> import pandas as pd
>
> frames = [
>     client.timeseries.get_range(
>         dataset="GLBX.MDP3", schema="ohlcv-1d", stype_in="continuous",
>         symbols=[symbol], start="2026-09-14", end="2026-09-24",
>     ).to_df()
>     for symbol in ["ES.c.0", "ES.v.0"]
> ]
> df = pd.concat(frames).sort_index()
> ```
>
> Each symbol then gets its own rows, so days when both pointed at the same contract appear twice, once per symbol. Those shared days are downloaded twice, so it costs slightly more. You can follow the fix on the issue.

## What the runs showed

From [transcript.md](transcript.md), recorded 26 Nov 2026:

- **Offline, with no key** (`offline_repro.py`): the mapping from the issue loses the symbol on 4 of 6 dates when ES.c.0 is listed first, and on none when ES.v.0 is listed first.
- **Live, the issue's own request** (daily bars, 14 to 24 Sep 2026):
  - In those dates, ES.c.0 and ES.v.0 both pointed at instrument 42140870, the September contract, until volume rolled to December on the 16th.
  - One download, converted with `to_df()` ten times, lost 3 of 12 symbols on 5 of the 10 calls. The lost rows are 16, 17 and 18 Sep, the same as in the issue.
- **Why it comes and goes:**
  - `store.metadata.mappings` came back in a different order on different reads of the same file: ES.v.0 first 21 times out of 40, ES.c.0 first 19 times.
  - `to_df()` adds those mappings to the client's symbol map every time it's called.
  - The lookup bug in #147 only bites in one of the orders.
- **The workaround:** one request per symbol gave 18 of 18 rows labelled.
- **By design, not part of the bug:** with both symbols in one request, each contract-day comes back once (12 rows) with one label, even when nothing goes wrong. Separate requests give 18 rows.
- Cost of the runs: under US$0.001.

## A note for the maintainers (not posted)

> One detail that may help with #147: users see it intermittently. `databento_dbn.Metadata.mappings` comes back in a different order on different reads (40 reads of one downloaded file: ES.v.0 first 21 times, ES.c.0 first 19 times). `DBNStore.to_df()` calls `insert_metadata` on every call, so the same store gives NaN symbols on some calls and not others (5 of 10 here). The fix proposed in the issue, falling back to an earlier interval that still covers the date, removes the order dependence. Separately, because `to_df()` inserts the metadata again on every call, the map collects duplicate intervals.

## Run it

```text
python cases/05-nan-symbols-issue-147/offline_repro.py   # no key needed
python cases/05-nan-symbols-issue-147/run.py
```
