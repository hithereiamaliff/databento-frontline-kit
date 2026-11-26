"""
Case 2: "I asked for ES and got nothing."

Runs the request the way customers do, with symbols "ES" and the client's
default stype_in (raw_symbol): first on its own, then mixed with a symbol
that does resolve, which is the quieter way this goes wrong. Then it shows
what preflight says, and resolves four ways of asking for ES on the same day.
Symbol resolution and cost estimates are free; the one download is priced first.
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common  # noqa: E402

import databento as db  # noqa: E402

from frontline import checks, report  # noqa: E402

DAY = dict(dataset="GLBX.MDP3", start="2026-11-23", end="2026-11-24")


def run_and_show(hist, **query) -> None:
    """Run get_range and show exactly what the customer would see: rows, warnings or an error."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            df = hist.timeseries.get_range(**query).to_df()
            print(f"Rows returned: {len(df)}, for symbols: {sorted(df['symbol'].unique()) if len(df) else 'none'}")
        except db.BentoClientError as exc:
            print(f"Error {exc.http_status}:")
            print("  " + _common.safe(exc.message or "").replace("\n", "\n  "))
    for w in caught:
        if str(w.message).startswith("The inplace keyword"):
            continue  # pandas' notice about the client's own code; see cases/known-issues.md
        print(f"Warning from the client ({w.category.__name__}): {_common.safe(w.message)}")


def main() -> None:
    hist = _common.client()

    _common.heading('1. symbols="ES" on its own (schema ohlcv-1h)')
    run_and_show(hist, **DAY, symbols="ES", schema="ohlcv-1h")

    _common.heading('2. symbols=["ES", "ESZ6"]: one resolves, one doesn\'t')
    _common.priced(hist, **DAY, symbols=["ESZ6"], schema="ohlcv-1h")
    run_and_show(hist, **DAY, symbols=["ES", "ESZ6"], schema="ohlcv-1h")

    _common.heading('3. What preflight says about symbols="ES"')
    request = checks.Request(symbols=["ES"], schema="ohlcv-1h", stype_in="raw_symbol", **DAY)
    print(_common.safe(report.render(request, checks.run(hist, request, key=_common.key()))))

    _common.heading("4. Four ways to ask for ES on 2026-11-23")
    attempts = [("ES", "raw_symbol"), ("ESZ6", "raw_symbol"), ("ES.c.0", "continuous"), ("ES.FUT", "parent")]
    print(f"{'symbols':<9}{'stype_in':<13}{'instruments':>12}{'1 day of trades':>20}")
    for symbol, stype_in in attempts:
        resolved = hist.symbology.resolve(
            dataset=DAY["dataset"], symbols=[symbol], stype_in=stype_in, stype_out="instrument_id",
            start_date=DAY["start"], end_date=DAY["end"],
        )
        # A parent's answer is keyed by each child contract, so count across every entry.
        ids = {m["s"] for maps in resolved["result"].values() for m in maps}
        try:
            cost = hist.metadata.get_cost(**DAY, symbols=[symbol], stype_in=stype_in, schema="trades")
            price = "US$" + format(cost, ",.6f")
        except db.BentoClientError as exc:
            price = f"error {exc.http_status}"
        print(f"{symbol:<9}{stype_in:<13}{len(ids):>12}{price:>20}")

    _common.heading("5. What ES.FUT covers on that day")
    parent = hist.symbology.resolve(
        dataset=DAY["dataset"], symbols=["ES.FUT"], stype_in="parent", stype_out="instrument_id",
        start_date=DAY["start"], end_date=DAY["end"],
    )
    raw = sorted(parent["result"])  # the answer is keyed by each child contract's raw symbol
    outrights = [s for s in raw if "-" not in s]
    spreads = [s for s in raw if "-" in s]
    print(f"{len(raw)} instruments: {len(outrights)} outright contracts and {len(spreads)} calendar spreads")
    print("Outrights:", ", ".join(outrights))
    print("Spreads, first ten:", ", ".join(spreads[:10]))


if __name__ == "__main__":
    main()
