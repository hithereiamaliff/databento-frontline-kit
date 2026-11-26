"""
Issue #147 in the pinned client (databento 0.90.0), checked offline.

These tests describe the bug as it is today. If an upgrade makes the first
one fail, the bug has been fixed: update the case and the reply.
"""

import datetime as dt
import importlib.util
from pathlib import Path

CASE = Path(__file__).resolve().parents[1] / "cases" / "05-nan-symbols-issue-147" / "offline_repro.py"
spec = importlib.util.spec_from_file_location("offline_repro", CASE)
repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repro)

AFTER_VOLUME_ROLL = dt.date(2026, 9, 17)


def test_symbol_is_lost_when_ES_c_0_is_listed_first():
    assert repro.label_on(["ES.c.0", "ES.v.0"], AFTER_VOLUME_ROLL) is None


def test_the_answer_depends_on_the_order_of_the_symbols():
    assert repro.label_on(["ES.v.0", "ES.c.0"], AFTER_VOLUME_ROLL) == "ES.c.0"


def test_workaround_one_symbol_per_request_maps_correctly():
    assert repro.label_on(["ES.c.0"], AFTER_VOLUME_ROLL) == "ES.c.0"
