"""
The preflight checks: everything a frontline engineer would look at before
answering "why didn't my request work?" or "what will this cost?".

Every call here is a metadata or symbology call. None of them downloads
market data. The checks stop early when something basic fails (a rejected
key, an unknown dataset), because later answers would only mislead.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from datetime import timedelta

import databento as db
import pandas as pd

from . import timewin
from .keys import scrub

OK, INFO, WARN, FAIL = "OK", "INFO", "WARN", "FAIL"


@dataclass
class Finding:
    level: str  # OK, INFO, WARN or FAIL
    title: str
    detail: str = ""


@dataclass
class Request:
    """What the customer says they ran."""

    dataset: str
    schema: str
    symbols: list[str]
    stype_in: str = "raw_symbol"
    start: str = ""
    end: str | None = None
    customer_tz: str = "UTC"


@dataclass
class Result:
    findings: list[Finding] = field(default_factory=list)
    window: timewin.Window | None = None
    mappings: dict = field(default_factory=dict)
    cost_usd: float | None = None
    records: int | None = None
    billable_bytes: int | None = None

    @property
    def failed(self) -> bool:
        return any(f.level == FAIL for f in self.findings)


def symbol_hint(symbol: str, stype_in: str) -> str:
    """Suggest the likely fix for a symbol that didn't resolve."""
    root = symbol.split(".")[0]
    if stype_in == "raw_symbol" and symbol.isalpha() and len(symbol) <= 3:
        return (
            f'"{symbol}" looks like a product root, but a raw symbol names one contract, such as '
            f'{root}Z6. For every {root} contract, use "{root}.FUT" with stype_in="parent". For the '
            f'front month, use "{root}.c.0" with stype_in="continuous".'
        )
    if stype_in == "raw_symbol" and symbol.count(".") >= 1:
        return (
            f'"{symbol}" looks like a parent or continuous symbol, but stype_in is raw_symbol. '
            f'Use stype_in="parent" for {root}.FUT or stype_in="continuous" for {root}.c.0.'
        )
    if stype_in == "parent" and not symbol.upper().endswith((".FUT", ".OPT", ".SPOT")):
        return f'Parent symbols end in .FUT or .OPT, for example "{root}.FUT".'
    return "Check the spelling, and whether the contract had listed or expired by those dates."


def run(client, req: Request, *, key: str | None = None, estimate_cost: bool = True) -> Result:
    """Run every check and return what was found. `client` is a db.Historical."""
    result = Result()
    add = result.findings.append

    def explain(exc: Exception) -> str:
        return scrub(str(exc), key)

    # 1. The key: the cheapest authenticated call there is.
    try:
        datasets = client.metadata.list_datasets()
    except db.BentoClientError as exc:
        if exc.http_status in (401, 403):
            add(Finding(FAIL, "API key rejected", f"Databento answered {explain(exc)}"))
        else:
            add(Finding(FAIL, "Databento refused the request", explain(exc)))
        return result
    except Exception as exc:  # no network, proxy or certificate trouble, and so on
        add(Finding(FAIL, "Couldn't reach Databento", f"{type(exc).__name__}: {explain(exc)}"))
        return result
    add(Finding(OK, "API key accepted"))

    # 2. The dataset.
    if req.dataset not in datasets:
        close = difflib.get_close_matches(req.dataset.upper(), datasets, n=3, cutoff=0.4)
        hint = f"Did you mean {', '.join(close)}?" if close else "See metadata.list_datasets()."
        add(Finding(FAIL, f"Unknown dataset {req.dataset}", hint))
        return result
    add(Finding(OK, f"Dataset {req.dataset} exists"))

    # 3. The schema.
    schemas = client.metadata.list_schemas(req.dataset)
    if req.schema not in schemas:
        add(Finding(FAIL, f"{req.dataset} has no {req.schema} schema", "Available: " + ", ".join(schemas)))
        return result
    add(Finding(OK, f"Schema {req.schema} is available for {req.dataset}"))

    # 4. The time window, as sent and as meant.
    try:
        window = timewin.interpret_window(req.start, req.end, req.customer_tz)
    except ValueError as exc:
        add(Finding(FAIL, "Couldn't read the time window", str(exc)))
        return result
    result.window = window
    for level, text in timewin.notes(window, req.dataset, req.schema):
        title, _, detail = text.partition(". ")
        add(Finding(level, title.rstrip(".") + ".", detail))
    if result.failed:
        return result

    # 5. Is the window inside what's available for this schema?
    span = client.metadata.get_dataset_range(req.dataset)
    schema_span = span.get("schema", {}).get(req.schema, span)
    first, last = pd.Timestamp(schema_span["start"]), pd.Timestamp(schema_span["end"])
    if window.start_as_sent >= last:
        add(
            Finding(
                FAIL,
                "None of the window is available yet.",
                f"{req.schema} on {req.dataset} is available up to {timewin.local(last, 'UTC')} UTC (exclusive).",
            )
        )
        return result
    if window.end_as_sent > last:
        add(
            Finding(
                WARN,
                "The newest part of the window isn't available yet.",
                f"{req.schema} on {req.dataset} is available up to {timewin.local(last, 'UTC')} UTC (exclusive), "
                "so anything after that won't come back.",
            )
        )
    elif window.start_as_sent < first:
        add(Finding(WARN, "The window starts before the first available data.", f"Data starts {timewin.local(first, 'UTC')} UTC."))
    else:
        add(Finding(OK, "The whole window is inside the available range"))

    # 6. Data-quality flags, day by day (dates are UTC and inclusive here).
    first_day = window.start_as_sent.date()
    last_day = (min(window.end_as_sent, last) - pd.Timedelta(1, "ns")).date()
    try:
        days = client.metadata.get_dataset_condition(req.dataset, start_date=first_day.isoformat(), end_date=last_day.isoformat())
        flagged = [d for d in days if d.get("condition") != "available"]
        if flagged:
            listed = ", ".join(f"{d['date']} {d['condition']}" for d in flagged)
            add(Finding(WARN, "Some days carry a data-quality flag.", listed + ". \"degraded\" means data may be missing or wrong; \"pending\" means not ready yet."))
        else:
            add(Finding(OK, f"Every day in the window is marked available ({len(days)} day{'s' if len(days) != 1 else ''})"))
    except db.BentoClientError as exc:
        add(Finding(INFO, "Couldn't check data-quality flags.", explain(exc)))

    # 7. The symbols. Resolution is free, and it's the usual cause of "I got no data".
    stype_out = "raw_symbol" if req.stype_in == "instrument_id" else "instrument_id"
    resolve_end = last_day + timedelta(days=1)  # resolve's end_date is exclusive
    try:
        resolved = client.symbology.resolve(
            dataset=req.dataset,
            symbols=req.symbols,
            stype_in=req.stype_in,
            stype_out=stype_out,
            start_date=first_day.isoformat(),
            end_date=resolve_end.isoformat(),
        )
    except db.BentoClientError as exc:
        add(Finding(FAIL, "Symbology lookup failed.", explain(exc)))
        return result
    result.mappings = resolved.get("result", {})
    not_found = resolved.get("not_found", [])
    partial = resolved.get("partial", [])
    for symbol in not_found:
        add(Finding(FAIL, f'"{symbol}" didn\'t resolve to anything between {first_day} and {last_day}.', symbol_hint(symbol, req.stype_in)))
    if partial:
        add(Finding(WARN, "Some symbols resolved for only part of the window.", ", ".join(partial) + ". They may have listed, expired or rolled inside it."))
    if req.stype_in == "parent":
        # For a parent, the answer is keyed by each child contract, not by the parent symbol.
        children = sorted(result.mappings)
        ids = {str(i.get("s")) for intervals in result.mappings.values() for i in intervals}
        spreads = [c for c in children if "-" in c]
        if ids:
            add(
                Finding(
                    INFO,
                    f"{', '.join(req.symbols)} covers {len(ids)} instruments ({len(spreads)} of them spreads).",
                    "A parent symbol means every expiry and every spread. How much that adds depends on "
                    "the product and the schema, so check the cost estimate below.",
                )
            )
    else:
        for symbol, intervals in result.mappings.items():
            ids = sorted({str(i.get("s")) for i in intervals})
            if req.stype_in == "continuous" and len(ids) > 1:
                changes = "; ".join(f"{i['d0']} to {i['d1']}: {i['s']}" for i in intervals)
                add(Finding(INFO, f"{symbol} rolled to a new contract inside the window.", changes))
            elif ids:
                add(Finding(OK, f"{symbol} resolves to {stype_out} {', '.join(ids)}"))
    if not_found and len(not_found) == len(req.symbols):
        return result

    # 8. The price, before anyone downloads anything. These calls return no market data.
    if estimate_cost:
        query = dict(
            dataset=req.dataset,
            start=req.start,
            end=req.end,
            symbols=req.symbols,
            schema=req.schema,
            stype_in=req.stype_in,
        )
        try:
            result.cost_usd = client.metadata.get_cost(**query)
            result.records = client.metadata.get_record_count(**query)
            result.billable_bytes = client.metadata.get_billable_size(**query)
            add(
                Finding(
                    INFO,
                    f"Estimated cost US${result.cost_usd:,.6f} for {result.records:,} records "
                    f"({result.billable_bytes:,} billable bytes).",
                    "Nothing has been downloaded. Billing is on the uncompressed binary size, "
                    "whatever encoding you ask for.",
                )
            )
        except db.BentoClientError as exc:
            add(Finding(WARN, "Couldn't get a cost estimate.", explain(exc)))
    return result
