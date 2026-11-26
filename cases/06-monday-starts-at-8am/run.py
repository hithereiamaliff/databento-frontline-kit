"""
Case 6: "I asked for Monday, but my data starts at 8am."

A customer in Penang asks for Monday 23 November 2026 as "2026-11-23" to
"2026-11-24". Databento reads those as UTC, so the window is 08:00 Monday to
08:00 Tuesday in Penang. This runs the request as written and as meant, and
shows the difference in Penang time. Cost: about 40 hourly bars, priced first.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common  # noqa: E402

import databento as db  # noqa: E402

from frontline import checks, report  # noqa: E402

PENANG = "Asia/Kuala_Lumpur"
BASE = dict(dataset="GLBX.MDP3", schema="ohlcv-1h", symbols=["ESZ6"], stype_in="raw_symbol")


def fetch(hist, start: str, end: str):
    _common.priced(hist, start=start, end=end, **BASE)
    try:
        return hist.timeseries.get_range(start=start, end=end, **BASE).to_df(tz=PENANG)
    except db.BentoClientError as exc:
        print(f"Error: {_common.safe(exc)}")
        return None


def summary(df) -> None:
    print(f"{len(df)} hourly bars. First bar opens {df.index[0]}, last bar opens {df.index[-1]} (Penang time)")


def main() -> None:
    hist = _common.client()

    _common.heading('1. As written: start="2026-11-23", end="2026-11-24"')
    as_written = fetch(hist, "2026-11-23", "2026-11-24")
    summary(as_written)

    _common.heading('2. As meant: start="2026-11-23T00:00+08:00", end="2026-11-24T00:00+08:00"')
    as_meant = fetch(hist, "2026-11-23T00:00+08:00", "2026-11-24T00:00+08:00")
    if as_meant is not None:
        summary(as_meant)

        _common.heading("3. The difference, in Penang time")
        only_meant = as_meant.index.difference(as_written.index)
        only_written = as_written.index.difference(as_meant.index)
        print(f"Bars the customer wanted but didn't get ({len(only_meant)}):")
        for ts in only_meant:
            print(f"  {ts}")
        print(f"Bars the customer got but didn't want ({len(only_written)}), all on Tuesday morning:")
        for ts in only_written:
            print(f"  {ts}")

    _common.heading("4. What preflight says about the request as written")
    request = checks.Request(
        dataset=BASE["dataset"], schema=BASE["schema"], symbols=BASE["symbols"], stype_in=BASE["stype_in"],
        start="2026-11-23", end="2026-11-24", customer_tz=PENANG,
    )
    print(_common.safe(report.render(request, checks.run(hist, request, key=_common.key()))))


if __name__ == "__main__":
    main()
