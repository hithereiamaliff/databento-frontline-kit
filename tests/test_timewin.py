"""Time windows: the rules from Databento's "Standards and conventions" docs, checked offline."""

import pandas as pd
import pytest

from frontline import timewin

T = pd.Timestamp
KL = "Asia/Kuala_Lumpur"


def test_a_plain_date_is_read_as_utc_but_meant_as_local():
    w = timewin.interpret_window("2026-11-23", "2026-11-24", KL)
    assert w.start_as_sent == T("2026-11-23T00:00Z")
    assert w.start_as_meant == T("2026-11-22T16:00Z")  # midnight in Penang
    assert w.reads_differently


def test_an_explicit_offset_is_respected():
    w = timewin.interpret_window("2026-11-23T00:00+08:00", "2026-11-24T00:00+08:00", "UTC")
    assert w.start_as_sent == w.start_as_meant == T("2026-11-22T16:00Z")
    assert not w.reads_differently


@pytest.mark.parametrize(
    "start, filled_end",
    [
        ("2026", "2027-01-01T00:00Z"),
        ("2026-11", "2026-12-01T00:00Z"),
        ("2026-11-23", "2026-11-24T00:00Z"),
        ("2026-11-23T08", "2026-11-23T09:00Z"),
        ("2026-11-23T08:30", "2026-11-23T08:31Z"),
    ],
)
def test_a_missing_end_is_forward_filled_as_the_docs_describe(start, filled_end):
    w = timewin.interpret_window(start, None)
    assert w.end_as_sent == T(filled_end)
    assert w.end_was_filled


def test_no_forward_fill_below_a_minute():
    with pytest.raises(ValueError):
        timewin.interpret_window("2026-11-23T08:30:15", None)


def test_nanoseconds_since_1970_are_utc():
    ns = str(T("2026-11-23T00:00Z").value)
    w = timewin.interpret_window(ns, str(T("2026-11-24T00:00Z").value), KL)
    assert w.start_as_sent == T("2026-11-23T00:00Z")
    assert not w.reads_differently


def test_end_before_start_fails():
    w = timewin.interpret_window("2026-11-24", "2026-11-23")
    assert ("FAIL", "The end isn't after the start, so the request can't return anything.") in timewin.notes(
        w, "GLBX.MDP3", "trades"
    )


def test_daily_bars_note_and_ten_minute_note():
    w = timewin.interpret_window("2026-11-23T12:15", "2026-11-23T13:00")
    text = " ".join(message for _, message in timewin.notes(w, "GLBX.MDP3", "ohlcv-1d"))
    assert "UTC days" in text
    assert "10-minute boundary" in text
    aligned = timewin.interpret_window("2026-11-23T12:10", "2026-11-23T13:00")
    assert "10-minute" not in " ".join(m for _, m in timewin.notes(aligned, "GLBX.MDP3", "trades"))


@pytest.mark.parametrize(
    "start, end, closed",
    [
        ("2026-11-21T00:00Z", "2026-11-21T12:00Z", True),  # Saturday
        ("2026-11-20T21:00Z", "2026-11-20T21:59Z", False),  # Friday 15:00 Chicago, still open
        ("2026-11-22T22:00Z", "2026-11-22T22:59Z", True),  # Sunday 16:00 Chicago, not open yet
        ("2026-11-22T23:00Z", "2026-11-23T00:00Z", False),  # Sunday 17:00 Chicago, open
    ],
)
def test_cme_weekend_close(start, end, closed):
    assert timewin.cme_weekend_close(T(start), T(end)) is closed


@pytest.mark.parametrize(
    "ts, trading_date",
    [
        ("2026-11-22T23:00Z", "2026-11-23"),  # Sunday 17:00 CST opens Monday's session
        ("2026-11-23T21:59Z", "2026-11-23"),  # Monday 15:59 CST
        ("2026-11-23T23:00Z", "2026-11-24"),  # Monday 17:00 CST opens Tuesday's session
        ("2026-07-12T22:00Z", "2026-07-13"),  # Sunday 17:00 CDT, in US summer time
    ],
)
def test_cme_trading_date(ts, trading_date):
    assert timewin.cme_trading_date(T(ts)) == T(trading_date)


def test_table_shows_utc_customer_and_exchange_time():
    w = timewin.interpret_window("2026-11-23", "2026-11-24", KL)
    rows = dict(timewin.table(w, "GLBX.MDP3"))
    assert rows["UTC (as Databento reads it)"].startswith("Mon 2026-11-23 00:00")
    assert rows[f"{KL} (customer)"].startswith("Mon 2026-11-23 08:00")
    assert rows["America/Chicago (exchange)"].startswith("Sun 2026-11-22 18:00")
