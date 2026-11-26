"""Turn preflight findings into plain text that can be pasted into a reply or a ticket."""

from __future__ import annotations

import textwrap

from . import timewin
from .checks import Request, Result

WIDTH = 92


def render(req: Request, result: Result, key_notes: list[str] | None = None) -> str:
    lines = [
        "Databento preflight report",
        "==========================",
        f"Dataset {req.dataset}  |  schema {req.schema}  |  stype_in {req.stype_in}",
        f"Symbols {', '.join(req.symbols)}",
        f'Start "{req.start}"  |  end ' + (f'"{req.end}"' if req.end is not None else "(not given)")
        + f"  |  customer time zone {req.customer_tz}",
        "",
    ]
    for note in key_notes or []:
        lines += _wrap("[WARN]", note)
    for f in result.findings:
        lines += _wrap(f"[{f.level}]", f.title, f.detail)

    if result.window is not None:
        lines += ["", "The window in three time zones (start inclusive, end exclusive):"]
        rows = timewin.table(result.window, req.dataset)
        width = max(len(label) for label, _ in rows)
        lines += [f"  {label.ljust(width)}  {text}" for label, text in rows]

    verdict = "Problems found: see FAIL lines." if result.failed else "No blocking problems found."
    lines += ["", verdict]
    return "\n".join(lines)


def _wrap(tag: str, title: str, detail: str = "") -> list[str]:
    head = textwrap.wrap(f"{tag} {title}", WIDTH, subsequent_indent=" " * (len(tag) + 1))
    body = textwrap.wrap(detail, WIDTH, initial_indent=" " * (len(tag) + 1), subsequent_indent=" " * (len(tag) + 1)) if detail else []
    return head + body
