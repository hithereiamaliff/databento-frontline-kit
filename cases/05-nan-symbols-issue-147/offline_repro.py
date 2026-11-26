"""
Issue #147, reproduced offline: no API key, no data, no cost.

https://github.com/databento/databento-python/issues/147

The client keeps a map of which symbol each instrument ID stood for on each
date. When two requested symbols point at the same instrument for different
spans of dates, the lookup picks the interval that starts latest on or before
the date. If that interval has already ended, it gives up and returns None,
without checking the other interval that still covers the date. In a
DataFrame, None becomes NaN in the `symbol` column.

The mapping below has the same shape the symbology.resolve endpoint returns.
The dates match the issue: in September 2026, ES.c.0 (the calendar front
month) and ES.v.0 (the highest-volume contract) both pointed at the September
contract until volume rolled to December on the 16th.
"""

import datetime as dt
import sys

import databento as db
from databento.common.symbology import InstrumentMap

SEPTEMBER_CONTRACT = "42140870"  # the instrument ID from the issue


def resolve_result(order: list[str]) -> dict:
    """A symbology.resolve answer listing the symbols in the given order."""
    intervals = {
        "ES.c.0": [{"d0": "2026-09-14", "d1": "2026-09-20", "s": SEPTEMBER_CONTRACT}],
        "ES.v.0": [{"d0": "2026-09-14", "d1": "2026-09-16", "s": SEPTEMBER_CONTRACT}],
    }
    return {
        "result": {symbol: intervals[symbol] for symbol in order},
        "symbols": order,
        "stype_in": "continuous",
        "stype_out": "instrument_id",
        "start_date": "2026-09-14",
        "end_date": "2026-09-24",
        "partial": [],
        "not_found": [],
        "message": "OK",
        "status": 0,
    }


def label_on(order: list[str], day: dt.date) -> str | None:
    instrument_map = InstrumentMap()
    instrument_map.insert_json(resolve_result(order))
    return instrument_map.resolve(int(SEPTEMBER_CONTRACT), day)


def main() -> int:
    print(f"databento {db.__version__}")
    print(f"Python {sys.version.split()[0]}\n")
    print("Which symbol does instrument 42140870 carry on each date?")
    print("(ES.c.0 covers 14 to 19 Sep, ES.v.0 covers 14 to 15 Sep; d1 is exclusive)\n")
    print(f"{'date':<12}{'expected':<19}{'ES.c.0 listed first':<22}{'ES.v.0 listed first':<22}{'ES.c.0 alone'}")
    wrong = 0
    for day in [dt.date(2026, 9, d) for d in range(14, 20)]:
        expected = "ES.c.0" if day >= dt.date(2026, 9, 16) else "ES.c.0 or ES.v.0"
        a = label_on(["ES.c.0", "ES.v.0"], day)
        b = label_on(["ES.v.0", "ES.c.0"], day)
        c = label_on(["ES.c.0"], day)
        wrong += a is None
        print(f"{day.isoformat():<12}{expected:<19}{str(a):<22}{str(b):<22}{c}")
    print(f"\nRows that lose their symbol when ES.c.0 is listed first: {wrong} of 6")
    return 0


if __name__ == "__main__":
    sys.exit(main())
