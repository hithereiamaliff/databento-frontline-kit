"""
Time windows, seen three ways: as Databento reads them, as the customer meant
them, and in the exchange's own time.

The rules, from Databento's "Standards and conventions" docs:
- every timestamp parameter is UTC unless it carries an offset
- start is inclusive and end is exclusive
- a missing end is "forward filled": "2026-11-23" alone means that whole UTC day

Customers in Asia usually mean their own local day, and futures traders
usually mean the exchange's trading session. Most "missing data" tickets from
APAC hours come from that gap, so this module puts the three side by side.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta

import pandas as pd

# Exchange time zones, by the venue code before the dot in a dataset name.
EXCHANGE_TZ = {
    "GLBX": "America/Chicago",  # CME Globex
    "XNAS": "America/New_York",  # Nasdaq
    "XNYS": "America/New_York",  # NYSE
    "OPRA": "America/New_York",  # US equity options
    "EQUS": "America/New_York",  # Databento US equities
    "DBEQ": "America/New_York",
    "IFUS": "America/New_York",  # ICE Futures US
    "IFEU": "Europe/London",  # ICE Futures Europe
    "NDEX": "Europe/Amsterdam",  # ICE Endex
    "XEUR": "Europe/Berlin",  # Eurex
}

UTC = "UTC"

# How precise a timestamp string is decides how Databento fills in a missing end.
_PRECISION = [
    (re.compile(r"^\d{4}$"), "year"),
    (re.compile(r"^\d{4}-\d{2}$"), "month"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "day"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}$"), "hour"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}$"), "minute"),
]
_OFFSET = re.compile(r"(Z|[+-]\d{2}:?\d{2})$", re.IGNORECASE)


def exchange_tz(dataset: str) -> str | None:
    """The exchange's time zone for a dataset like "GLBX.MDP3", if known."""
    return EXCHANGE_TZ.get(dataset.split(".")[0].upper())


def _is_nanoseconds(text: str) -> bool:
    """A long run of digits is nanoseconds since 1970. Four digits on their own are a year."""
    return text.isdigit() and len(text) > 4


def has_offset(text: str) -> bool:
    """True if the timestamp says which time zone it's in (Z, +08:00 and so on)."""
    text = text.strip()
    if text.isdigit() or not _OFFSET.search(text):
        return False
    try:
        return pd.Timestamp(text).tzinfo is not None
    except ValueError:
        return False


def _parse_naive(text: str) -> pd.Timestamp:
    """Parse a timestamp with no zone, including short forms like "2026", "2026-11" or "2026-11-23T08"."""
    text = text.strip()
    if re.fullmatch(r"\d{4}", text):
        text += "-01-01"
    elif re.fullmatch(r"\d{4}-\d{2}", text):
        text += "-01"
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}[T ]\d{2}", text):
        text += ":00"
    return pd.Timestamp(text)


def forward_fill(text: str, tz: str) -> pd.Timestamp:
    """The end Databento fills in when only a start is given: the start rounded up.

    Only timestamps given to the minute or coarser are filled in, as the docs say.
    """
    start = _parse_naive(text).tz_localize(tz)
    for pattern, unit in _PRECISION:
        if pattern.match(text.strip()):
            step = {
                "year": pd.DateOffset(years=1),
                "month": pd.DateOffset(months=1),
                "day": pd.DateOffset(days=1),
                "hour": pd.DateOffset(hours=1),
                "minute": pd.DateOffset(minutes=1),
            }[unit]
            return start + step
    raise ValueError(
        f'No end was given, and "{text}" is more precise than a minute, so Databento '
        "won't fill one in. Give an end as well."
    )


def _interpret(text: str, tz: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return (as Databento reads it, as the customer probably meant it), both in UTC."""
    text = text.strip()
    if _is_nanoseconds(text):  # nanoseconds since 1970, always UTC
        ts = pd.Timestamp(int(text), unit="ns", tz=UTC)
        return ts, ts
    if has_offset(text):
        ts = pd.Timestamp(text).tz_convert(UTC)
        return ts, ts
    naive = _parse_naive(text)
    return naive.tz_localize(UTC), naive.tz_localize(tz).tz_convert(UTC)


@dataclass
class Window:
    """A request's time window, both as sent and as meant."""

    start_text: str
    end_text: str | None
    customer_tz: str
    start_as_sent: pd.Timestamp
    end_as_sent: pd.Timestamp
    start_as_meant: pd.Timestamp
    end_as_meant: pd.Timestamp

    @property
    def end_was_filled(self) -> bool:
        return self.end_text is None

    @property
    def reads_differently(self) -> bool:
        """True when Databento will read the window differently from what the customer meant."""
        return (self.start_as_sent, self.end_as_sent) != (self.start_as_meant, self.end_as_meant)


def interpret_window(start: str, end: str | None, customer_tz: str = UTC) -> Window:
    start_sent, start_meant = _interpret(start, customer_tz)
    if end is None:
        if has_offset(start) or _is_nanoseconds(start.strip()):
            raise ValueError("Give an end as well: Databento only fills in an end for plain dates and times.")
        end_sent = forward_fill(start, UTC)
        end_meant = forward_fill(start, customer_tz).tz_convert(UTC)
    else:
        end_sent, end_meant = _interpret(end, customer_tz)
    return Window(start, end, customer_tz, start_sent, end_sent, start_meant, end_meant)


def local(ts: pd.Timestamp, tz: str) -> str:
    """A timestamp in a given zone, with the weekday, e.g. "Mon 2026-11-23 08:00"."""
    t = ts.tz_convert(tz)
    seconds = ":%S" if t.second or t.microsecond or t.nanosecond else ""
    return t.strftime(f"%a %Y-%m-%d %H:%M{seconds}")


def iso_with_offset(ts: pd.Timestamp, tz: str) -> str:
    """The timestamp written in the customer's zone, ready to paste into a request."""
    return ts.tz_convert(tz).isoformat()


def on_ten_minute_boundary(ts: pd.Timestamp) -> bool:
    return ts.minute % 10 == 0 and ts.second == 0 and ts.microsecond == 0 and ts.nanosecond == 0


def cme_weekend_close(start: pd.Timestamp, end: pd.Timestamp) -> bool:
    """True if the whole window falls in CME Globex's weekend close.

    Most CME Globex products stop on Friday at 16:00 Chicago time and reopen
    on Sunday at 17:00. Some products (grains, for example) keep shorter
    hours, and holidays aren't covered here.
    """
    chicago = "America/Chicago"
    s = start.tz_convert(chicago)
    days_since_friday = (s.weekday() - 4) % 7
    friday = (s - pd.Timedelta(days=days_since_friday)).date()
    close_starts = pd.Timestamp(f"{friday} 16:00").tz_localize(chicago)
    reopens = pd.Timestamp(f"{friday + timedelta(days=2)} 17:00").tz_localize(chicago)
    return close_starts <= start and end <= reopens


def weekend_in(start: pd.Timestamp, end: pd.Timestamp, tz: str) -> bool:
    """True if the whole window falls on a Saturday or Sunday in the given zone."""
    s, e = start.tz_convert(tz), (end - pd.Timedelta(1, "ns")).tz_convert(tz)
    whole_days = pd.date_range(s.normalize(), e.normalize(), freq="D")
    return all(day.weekday() >= 5 for day in whole_days)


def cme_trading_date(ts: pd.Timestamp) -> pd.Timestamp:
    """The CME trading date a timestamp belongs to.

    For products that open at 17:00 Chicago time, the session that opens on
    Sunday evening is Monday's trading date. Adding 7 hours to Chicago time
    moves 17:00 to midnight, so the date then reads correctly.
    """
    return (ts.tz_convert("America/Chicago") + pd.Timedelta(hours=7)).normalize().tz_localize(None)


def notes(window: Window, dataset: str, schema: str) -> list[tuple[str, str]]:
    """Plain-English notes about the window, as (level, message) pairs."""
    out: list[tuple[str, str]] = []
    tz = window.customer_tz

    if window.end_as_sent <= window.start_as_sent:
        out.append(("FAIL", "The end isn't after the start, so the request can't return anything."))
        return out

    if window.start_as_sent > pd.Timestamp.now(tz=UTC):
        out.append(("FAIL", "The window starts in the future."))

    if window.reads_differently:
        pieces = []
        if window.start_as_sent != window.start_as_meant:
            pieces.append(
                f'"{window.start_text}" has no time zone, so Databento reads it as '
                f"{local(window.start_as_sent, UTC)} UTC. That's {local(window.start_as_sent, tz)} "
                f"in {tz}. If you meant {tz} time, send "
                f'"{iso_with_offset(window.start_as_meant, tz)}" instead.'
            )
        if window.end_as_sent != window.end_as_meant:
            where = "the end Databento fills in" if window.end_was_filled else f'"{window.end_text}"'
            pieces.append(
                f"Likewise {where} is {local(window.end_as_sent, UTC)} UTC, which is "
                f"{local(window.end_as_sent, tz)} in {tz}. For {tz} time, use "
                f'"{iso_with_offset(window.end_as_meant, tz)}".'
            )
        out.append(("WARN", " ".join(pieces)))

    if window.end_was_filled:
        out.append(
            (
                "INFO",
                f"No end was given, so Databento fills it in by rounding the start up: "
                f"{local(window.end_as_sent, UTC)} UTC.",
            )
        )

    out.append(
        (
            "INFO",
            f"The end is exclusive: the last record returned is just before {local(window.end_as_sent, UTC)} UTC.",
        )
    )

    if schema == "ohlcv-1d":
        out.append(
            (
                "INFO",
                "ohlcv-1d bars are UTC days (00:00 to 24:00 UTC), not exchange sessions and "
                "not your local days, so they won't match a broker's daily chart. To get "
                "session bars, request ohlcv-1h and group the hours yourself.",
            )
        )

    venue = dataset.split(".")[0].upper()
    if venue == "GLBX" and cme_weekend_close(window.start_as_sent, window.end_as_sent):
        out.append(
            (
                "WARN",
                "The whole window falls in CME Globex's weekend close (Friday 16:00 to Sunday "
                "17:00 Chicago time for most products), so expect no trades.",
            )
        )
    elif venue != "GLBX" and exchange_tz(dataset) and weekend_in(
        window.start_as_sent, window.end_as_sent, exchange_tz(dataset)
    ):
        out.append(("WARN", "The whole window falls on a weekend in exchange time, so expect no data."))

    if not (on_ten_minute_boundary(window.start_as_sent) and on_ten_minute_boundary(window.end_as_sent)):
        out.append(
            (
                "INFO",
                "The start or end isn't on a 10-minute boundary. Databento's docs say size "
                "estimates may then be overstated (12:10 is fine, 12:15 isn't).",
            )
        )
    return out


def table(window: Window, dataset: str) -> list[tuple[str, str]]:
    """Rows of (label, window) for the report: UTC, the customer's zone, and the exchange's."""
    out = [("UTC (as Databento reads it)", f"{local(window.start_as_sent, UTC)}  to  {local(window.end_as_sent, UTC)}")]
    zones = []
    if window.customer_tz != UTC:
        zones.append((f"{window.customer_tz} (customer)", window.customer_tz))
    ex = exchange_tz(dataset)
    if ex:
        zones.append((f"{ex} (exchange)", ex))
    for label, tz in zones:
        out.append((label, f"{local(window.start_as_sent, tz)}  to  {local(window.end_as_sent, tz)}"))
    return out
