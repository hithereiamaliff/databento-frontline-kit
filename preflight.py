"""
preflight: check a customer's Databento request before anyone downloads data.

It answers the questions a frontline engineer asks first:
  - Does the key work? (without ever printing it)
  - Do the dataset and schema exist, and is the window inside what's available?
  - Is any day in the window flagged as degraded, pending or missing?
  - Do the symbols resolve for those dates, and did a continuous symbol roll?
  - What does the window look like in UTC, in the customer's time zone and in exchange time?
  - What will it cost, and how many records will come back?

Only metadata and symbology calls are made, so no market data is downloaded.

Example (a customer in Penang asking about Monday's hourly ES bars):
  python preflight.py --dataset GLBX.MDP3 --schema ohlcv-1h --symbols ES.c.0 \
      --stype-in continuous --start 2026-11-23 --end 2026-11-24 --tz Asia/Kuala_Lumpur

Exit codes: 0 if nothing blocking was found, 1 if a check failed, 2 for bad arguments.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import databento as db

from frontline import checks, keys, report

HERE = Path(__file__).resolve().parent


def time_zone(name: str) -> str:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise argparse.ArgumentTypeError(f'unknown time zone "{name}" (use a name like Asia/Kuala_Lumpur)')
    return name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a Databento request before downloading anything.")
    parser.add_argument("--dataset", required=True, help="for example GLBX.MDP3")
    parser.add_argument("--schema", required=True, help="for example trades, ohlcv-1h, mbp-1")
    parser.add_argument("--symbols", required=True, help="comma-separated, for example ES.c.0,NQ.c.0")
    parser.add_argument(
        "--stype-in",
        default="raw_symbol",
        choices=["raw_symbol", "parent", "continuous", "instrument_id"],
        help="the symbol type the customer used (default: raw_symbol, as in the client)",
    )
    parser.add_argument("--start", required=True, help="exactly as the customer wrote it")
    parser.add_argument("--end", help="exactly as the customer wrote it; leave out if they did")
    parser.add_argument("--tz", type=time_zone, default="UTC", help="the customer's time zone, for example Asia/Kuala_Lumpur")
    parser.add_argument("--no-cost", action="store_true", help="skip the cost estimate")
    parser.add_argument("--env-file", default=str(HERE / ".env"), help="where to look for DATABENTO_API_KEY")
    args = parser.parse_args(argv)

    request = checks.Request(
        dataset=args.dataset.strip(),
        schema=args.schema.strip(),
        symbols=[s.strip() for s in args.symbols.split(",") if s.strip()],
        stype_in=args.stype_in,
        start=args.start,
        end=args.end,
        customer_tz=args.tz,
    )

    raw, source = keys.find_key(Path(args.env_file))
    problems = keys.shape_problems(raw, Path(args.env_file))
    if raw is None or not raw.strip():
        result = checks.Result(findings=[checks.Finding(checks.FAIL, problems[0])])
        print(report.render(request, result))
        return 1

    # Fixable shape problems (spaces, quotes) are reported, then cleaned so the rest can run.
    key = keys.clean(raw)
    client = db.Historical(key)
    result = checks.run(client, request, key=key, estimate_cost=not args.no_cost)
    notes = [f"Key from {source}: {p}" for p in problems]
    print(keys.scrub(report.render(request, result, notes), raw, key))
    return 1 if result.failed else 0


if __name__ == "__main__":
    sys.exit(main())
