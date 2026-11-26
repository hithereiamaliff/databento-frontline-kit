"""Preflight checks against a fake client, so they run offline and cost nothing.

The fake answers in the same shapes as Databento's API docs describe.
"""

import databento as db
import pandas as pd

from frontline import checks, report

FAKE = "db-Fake0Key0For0Tests0Only000000"
ALL_SCHEMAS = ["mbo", "mbp-1", "trades", "ohlcv-1h", "ohlcv-1d"]


class FakeMetadata:
    def __init__(self, reject_key=False, range_end="2026-11-26T00:00:00.000000000Z", conditions=None, echo_key=False):
        self.reject_key, self.range_end, self.conditions, self.echo_key = reject_key, range_end, conditions, echo_key
        self.calls = []

    def list_datasets(self):
        self.calls.append("list_datasets")
        if self.reject_key:
            message = f"Authentication failed for {FAKE}." if self.echo_key else "Authentication failed."
            raise db.BentoClientError(http_status=401, message=message)
        return ["GLBX.MDP3", "XNAS.ITCH"]

    def list_schemas(self, dataset):
        self.calls.append("list_schemas")
        return ALL_SCHEMAS

    def get_dataset_range(self, dataset):
        span = {"start": "2010-06-06T00:00:00.000000000Z", "end": self.range_end}
        return {**span, "schema": {s: dict(span) for s in ALL_SCHEMAS}}

    def get_dataset_condition(self, dataset, start_date=None, end_date=None):
        if self.conditions is not None:
            return self.conditions
        days = pd.date_range(start_date, end_date, freq="D")
        return [{"date": d.date().isoformat(), "condition": "available", "last_modified_date": None} for d in days]

    def get_cost(self, **query):
        self.calls.append("get_cost")
        return 0.0123

    def get_record_count(self, **query):
        return 24

    def get_billable_size(self, **query):
        return 1344


class FakeSymbology:
    def __init__(self, result=None, not_found=(), partial=()):
        self.result, self.not_found, self.partial = result or {}, list(not_found), list(partial)

    def resolve(self, **query):
        return {"result": self.result, "not_found": self.not_found, "partial": self.partial, "message": "OK", "status": 0}


class FakeClient:
    def __init__(self, metadata=None, symbology=None):
        self.metadata = metadata or FakeMetadata()
        self.symbology = symbology or FakeSymbology(result={"ESZ6": [{"d0": "2026-11-23", "d1": "2026-11-24", "s": "42140878"}]})


def request(**changes):
    base = dict(dataset="GLBX.MDP3", schema="ohlcv-1h", symbols=["ESZ6"], start="2026-11-23", end="2026-11-24")
    return checks.Request(**{**base, **changes})


def levels(result):
    return [(f.level, f.title) for f in result.findings]


def test_happy_path_estimates_the_cost():
    result = checks.run(FakeClient(), request())
    assert not result.failed
    assert result.cost_usd == 0.0123
    assert any("Estimated cost" in title for _, title in levels(result))


def test_rejected_key_stops_everything_and_never_shows_the_key():
    metadata = FakeMetadata(reject_key=True, echo_key=True)
    result = checks.run(FakeClient(metadata), request(), key=FAKE)
    assert result.failed
    assert metadata.calls == ["list_datasets"]
    text = report.render(request(), result)
    assert "401" in text
    assert FAKE not in text


def test_unknown_dataset_suggests_the_right_one():
    result = checks.run(FakeClient(), request(dataset="GLBX"))
    [fail] = [f for f in result.findings if f.level == checks.FAIL]
    assert "GLBX.MDP3" in fail.detail


def test_a_bare_root_symbol_gets_a_useful_hint():
    client = FakeClient(symbology=FakeSymbology(not_found=["ES"]))
    result = checks.run(client, request(symbols=["ES"]))
    [fail] = [f for f in result.findings if f.level == checks.FAIL]
    assert "ES.FUT" in fail.detail and "ES.c.0" in fail.detail
    assert "get_cost" not in client.metadata.calls  # nothing to price


def test_a_continuous_roll_is_pointed_out():
    rolled = {"ES.c.0": [{"d0": "2026-09-14", "d1": "2026-09-19", "s": "1"}, {"d0": "2026-09-19", "d1": "2026-09-24", "s": "2"}]}
    client = FakeClient(symbology=FakeSymbology(result=rolled))
    result = checks.run(client, request(symbols=["ES.c.0"], stype_in="continuous", start="2026-09-14", end="2026-09-24"))
    assert any("rolled" in title for _, title in levels(result))


def test_a_parent_symbol_is_summarised_in_one_line():
    # The live API keys a parent's answer by each child contract, not by "ES.FUT".
    children = {
        "ESZ6": [{"d0": "2026-11-23", "d1": "2026-11-24", "s": "10252"}],
        "ESH7": [{"d0": "2026-11-23", "d1": "2026-11-24", "s": "20000"}],
        "ESZ6-ESH7": [{"d0": "2026-11-23", "d1": "2026-11-24", "s": "30000"}],
    }
    client = FakeClient(symbology=FakeSymbology(result=children))
    result = checks.run(client, request(symbols=["ES.FUT"], stype_in="parent"))
    summary = [title for _, title in levels(result) if "covers" in title]
    assert summary == ["ES.FUT covers 3 instruments (1 of them spreads)."]
    assert not any(title.startswith("ESZ6 resolves") for _, title in levels(result))


def test_a_window_past_the_available_end_is_flagged():
    client = FakeClient(FakeMetadata(range_end="2026-11-23T12:00:00.000000000Z"))
    result = checks.run(client, request())
    assert any(level == "WARN" and "isn't available yet" in title for level, title in levels(result))


def test_degraded_days_are_listed():
    conditions = [{"date": "2026-11-23", "condition": "degraded", "last_modified_date": "2026-11-24"}]
    result = checks.run(FakeClient(FakeMetadata(conditions=conditions)), request())
    [warn] = [f for f in result.findings if f.title.startswith("Some days")]
    assert "2026-11-23 degraded" in warn.detail


def test_report_shows_three_time_zones():
    req = request(customer_tz="Asia/Kuala_Lumpur")
    text = report.render(req, checks.run(FakeClient(), req))
    assert "Asia/Kuala_Lumpur (customer)" in text
    assert "America/Chicago (exchange)" in text
