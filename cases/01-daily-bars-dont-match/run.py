"""
Case 1: "My daily bars don't match my broker's chart."

Downloads one week of the December 2026 E-mini S&P 500 contract (ESZ6) as
Databento's daily bars and as hourly bars, then rebuilds each day three ways:
  - UTC days, which is what ohlcv-1d is
  - CME trading sessions (17:00 to 16:00 Chicago time), which is what a futures broker shows
  - Penang days (UTC+8), which is what a customer here might expect
Cost: a few hundred records, priced before downloading.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common  # noqa: E402

import pandas as pd  # noqa: E402

from frontline import timewin  # noqa: E402

QUERY = dict(dataset="GLBX.MDP3", symbols=["ESZ6"], stype_in="raw_symbol", start="2026-11-15", end="2026-11-21")
PENANG = "Asia/Kuala_Lumpur"
COLUMNS = ["open", "high", "low", "close", "volume"]


def daily_from(hourly: pd.DataFrame, day_of_each_bar) -> pd.DataFrame:
    """Combine hourly bars into daily bars, using a given 'day' for each hour."""
    return hourly.groupby(day_of_each_bar).agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), volume=("volume", "sum")
    )


def main() -> None:
    hist = _common.client()

    _common.heading("1. Databento's daily bars for ESZ6 (ohlcv-1d)")
    _common.priced(hist, schema="ohlcv-1d", **QUERY)
    daily = hist.timeseries.get_range(schema="ohlcv-1d", **QUERY).to_df()
    print(daily[COLUMNS + ["symbol"]].to_string())

    _common.heading("2. The same week as hourly bars (ohlcv-1h)")
    _common.priced(hist, schema="ohlcv-1h", **QUERY)
    hourly = hist.timeseries.get_range(schema="ohlcv-1h", **QUERY).to_df()
    print(f"{len(hourly)} hourly bars, from {hourly.index[0]} to {hourly.index[-1]} (bar open times, UTC)")

    _common.heading("3. Check: hourly bars grouped by UTC day give back ohlcv-1d exactly")
    utc_days = daily_from(hourly, hourly.index.tz_convert("UTC").date)
    utc_days.index = pd.to_datetime(utc_days.index)
    ours = daily.set_index(daily.index.tz_convert("UTC").tz_localize(None).normalize())[COLUMNS]
    same = utc_days[COLUMNS].reindex(ours.index).round(6).equals(ours.round(6))
    print(f"ohlcv-1d equals hourly bars grouped by UTC day: {same}")

    _common.heading("4. The same week, rebuilt as CME sessions and as Penang days")
    sessions = daily_from(hourly, [timewin.cme_trading_date(ts) for ts in hourly.index])
    penang = daily_from(hourly, hourly.index.tz_convert(PENANG).date)
    sessions.index = pd.to_datetime(sessions.index)
    penang.index = pd.to_datetime(penang.index)
    side_by_side = pd.DataFrame(
        {
            "UTC day close (ohlcv-1d)": ours["close"],
            "CME session close": sessions["close"],
            "Penang day close": penang["close"],
            "UTC day volume": ours["volume"],
            "CME session volume": sessions["volume"],
            "Penang day volume": penang["volume"],
        }
    )
    side_by_side.index.name = "date"
    print(side_by_side.to_string())

    _common.heading("5. Where each kind of day ends, in Penang time (November, US standard time)")
    print("CME session ends   16:00 Chicago = 22:00 UTC = 06:00 Penang the next morning")
    print("UTC day ends       00:00 UTC     = 08:00 Penang the next morning")
    print("Penang day ends    00:00 Penang  = 16:00 UTC = 10:00 Chicago")


if __name__ == "__main__":
    main()
