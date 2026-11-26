"""
Case 3: "My bill was higher than I expected."

Prices one day of futures data several ways with metadata.get_cost, which
returns an estimate and downloads nothing. The one download (section 4) is a
15-minute slice of ES trades, to compare an estimate with what's sent.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common  # noqa: E402

BASE = dict(dataset="GLBX.MDP3", start="2026-11-23", end="2026-11-24")
TRADE_RECORD_BYTES = 48  # each trades record is 48 bytes uncompressed


def header() -> None:
    print(f"{'request':<40}{'records':>12}{'billable bytes':>16}{'estimate':>16}")


def row(hist, label: str, **query) -> None:
    q = {**BASE, **query}
    cost = hist.metadata.get_cost(**q)
    size = hist.metadata.get_billable_size(**q)
    records = hist.metadata.get_record_count(**q)
    print(f"{label:<40}{records:>12,}{size:>16,}{'US$' + format(cost, ',.6f'):>16}")


def main() -> None:
    hist = _common.client()

    _common.heading("1. One day of ES.c.0, by schema (how much detail you ask for)")
    header()
    for schema in ["ohlcv-1h", "ohlcv-1m", "trades", "mbp-1", "mbo", "mbp-10"]:
        row(hist, schema, symbols=["ES.c.0"], stype_in="continuous", schema=schema)

    _common.heading("2. Front month versus every contract and spread (a parent symbol)")
    header()
    for root, schema in [("ES", "trades"), ("ES", "mbo"), ("CL", "mbo")]:
        row(hist, f"{root}.c.0 {schema}", symbols=[f"{root}.c.0"], stype_in="continuous", schema=schema)
        row(hist, f"{root}.FUT {schema}", symbols=[f"{root}.FUT"], stype_in="parent", schema=schema)

    _common.heading("3. Ten-minute boundaries: ES.c.0 trades from 14:00 UTC to ...")
    header()
    for end in ["14:10", "14:15", "14:20"]:
        row(hist, f"... {end}", symbols=["ES.c.0"], stype_in="continuous", schema="trades",
            start="2026-11-23T14:00", end=f"2026-11-23T{end}")

    _common.heading("4. The 14:00 to 14:15 slice, downloaded: estimate versus what's sent")
    query = dict(dataset="GLBX.MDP3", symbols=["ES.c.0"], stype_in="continuous", schema="trades",
                 start="2026-11-23T14:00", end="2026-11-23T14:15")
    _common.priced(hist, **query)
    records = len(hist.timeseries.get_range(**query).to_df())
    print(f"Records actually sent: {records:,} ({records * TRADE_RECORD_BYTES:,} bytes uncompressed)")


if __name__ == "__main__":
    main()
