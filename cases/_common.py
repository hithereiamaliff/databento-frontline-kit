"""
Shared helpers for the case scripts: the client, a cost guard and tidy output.

Every script that downloads data prices the request first, and stops if the
estimate is above MAX_COST_USD. The key is read from .env and never printed.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import databento as db  # noqa: E402

from frontline import keys  # noqa: E402

# databento 0.90.0's to_df() calls set_index(..., inplace=True), which pandas 3.1
# warns about on every call (see cases/known-issues.md). It's hidden here so the
# transcripts stay readable; Databento's own warnings stay on, because they matter.
# This must come after the imports: importing databento turns pandas' warnings back on.
warnings.filterwarnings("ignore", message="The inplace keyword", category=DeprecationWarning)

MAX_COST_USD = 0.50  # no single download in these cases should cost more than this

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_rows", 60)


def key() -> str:
    raw, _ = keys.find_key(ROOT / ".env")
    if not raw or not raw.strip():
        sys.exit("No DATABENTO_API_KEY found. Copy .env.example to .env and paste your key.")
    return keys.clean(raw)


def client() -> db.Historical:
    return db.Historical(key())


def priced(hist: db.Historical, **query) -> float:
    """Print what a request will cost, and stop if it's more than the guard allows."""
    cost = hist.metadata.get_cost(**query)
    records = hist.metadata.get_record_count(**query)
    print(f"Estimated cost before downloading: US${cost:.6f} for {records:,} records")
    if cost > MAX_COST_USD:
        sys.exit(f"Stopping: that's above the US${MAX_COST_USD:.2f} guard in cases/_common.py.")
    return cost


def heading(text: str) -> None:
    print(f"\n{text}\n{'-' * len(text)}")


def safe(text: str) -> str:
    """Remove the key from any text before it's printed."""
    return keys.scrub(str(text), key())
