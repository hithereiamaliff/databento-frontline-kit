"""
Case 5: "to_df() gives me NaN symbols." (issue #147, live)

Downloads the same request as the issue: daily bars for ES.c.0 and ES.v.0,
14 to 24 September 2026. It converts that one download with to_df() ten
times, because the result changes from call to call: the file's symbol
mappings come back in a different order on different reads, and the
client's lookup bug only bites in one of the orders. Then it shows the
workaround: one request per symbol.
Cost: under US$0.001 in total, priced before downloading.
"""

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common  # noqa: E402

import pandas as pd  # noqa: E402

QUERY = dict(dataset="GLBX.MDP3", schema="ohlcv-1d", stype_in="continuous", start="2026-09-14", end="2026-09-24")
BOTH = ["ES.c.0", "ES.v.0"]
CALLS = 10


def main() -> None:
    hist = _common.client()

    _common.heading("1. What each symbol pointed at (symbology.resolve, free)")
    resolved = hist.symbology.resolve(
        dataset=QUERY["dataset"], symbols=BOTH, stype_in="continuous", stype_out="instrument_id",
        start_date=QUERY["start"], end_date=QUERY["end"],
    )
    for symbol, intervals in resolved["result"].items():
        for i in intervals:
            print(f"{symbol}: instrument {i['s']} from {i['d0']} to {i['d1']} (end exclusive)")

    _common.heading("2. The customer's request: both symbols at once, downloaded once")
    _common.priced(hist, symbols=BOTH, **QUERY)
    store = hist.timeseries.get_range(symbols=BOTH, **QUERY)
    print(f"The same download, converted with to_df() {CALLS} times (like re-running a notebook cell):")
    lost = None
    for call in range(1, CALLS + 1):
        df = store.to_df()
        missing = int(df["symbol"].isna().sum())
        print(f"  call {call:>2}: rows with no symbol: {missing} of {len(df)}")
        if missing and lost is None:
            lost = df
    if lost is not None:
        print("\nOne of the calls that lost symbols:")
        print(lost[["instrument_id", "symbol", "close"]].to_string())

    _common.heading("3. Why it comes and goes: the order of store.metadata.mappings, read 40 times")
    orders = collections.Counter(", ".join(store.metadata.mappings) for _ in range(40))
    for order, count in orders.most_common():
        print(f"  {order}: {count} times")
    print("On every to_df() call, the client adds these mappings to its symbol map in whatever")
    print("order they come back. The lookup bug in #147 only bites in one of the orders.")

    _common.heading("4. Workaround: one request per symbol")
    parts = []
    for symbol in BOTH:
        _common.priced(hist, symbols=[symbol], **QUERY)
        parts.append(hist.timeseries.get_range(symbols=[symbol], **QUERY).to_df())
    separate = pd.concat(parts).sort_index()
    print(separate[["instrument_id", "symbol", "close"]].to_string())
    print(f"\nRows with no symbol: {separate['symbol'].isna().sum()} of {len(separate)}")


if __name__ == "__main__":
    main()
