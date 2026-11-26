"""
Find the Databento API key and check its shape, without ever showing it.

Support note: most "authentication failed" tickets come down to one of four
things: a stray space or line break around the key, quotes around it, a key
copied only in part, or a key saved under the wrong variable name. The checks
here catch all four before a request is sent.
"""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path

ENV_NAME = "DATABENTO_API_KEY"  # the only name the official client reads
KEY_PREFIX = "db-"
KEY_LENGTH = 32  # every Databento key is 32 characters and starts with "db-"

# Names people often use by mistake.
LOOKALIKE_NAMES = ("DATABENTO_KEY", "DATABENTO_API", "DATABENTO_TOKEN", "DB_API_KEY", "API_KEY")


def read_env_file(path: Path) -> dict[str, str]:
    """Read simple NAME=VALUE lines from a .env file.

    Values come back exactly as written (not trimmed), so the checks below
    can spot stray spaces and quotes.
    """
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    # "utf-8-sig" also copes with the invisible marker some editors add at the start.
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        values[name.strip()] = value
    return values


def find_key(env_file: Path) -> tuple[str | None, str]:
    """Return (the key as found, where it came from).

    The environment variable wins over the .env file, as with most tools.
    """
    if os.environ.get(ENV_NAME, "").strip():
        return os.environ[ENV_NAME], f"the {ENV_NAME} environment variable"
    from_file = read_env_file(env_file).get(ENV_NAME)
    if from_file is not None and from_file.strip():
        return from_file, env_file.name
    return None, "nowhere"


def shape_problems(raw: str | None, env_file: Path | None = None) -> list[str]:
    """Describe what's wrong with the key's shape, in plain English.

    The messages never include the key itself.
    """
    if raw is None or not raw.strip():
        found_under = {name for name in LOOKALIKE_NAMES if os.environ.get(name)}
        if env_file is not None:
            found_under |= {name for name in read_env_file(env_file) if name in LOOKALIKE_NAMES}
        hint = ""
        if found_under:
            hint = (
                f" Something is saved under {', '.join(sorted(found_under))},"
                f" but the client only reads {ENV_NAME}."
            )
        return [f"No API key found. Set {ENV_NAME} in the environment or in .env.{hint}"]

    problems = []
    if raw != raw.strip():
        problems.append("The key has a space or line break before or after it.")
    key = raw.strip()
    if key[:1] in {'"', "'"} or key[-1:] in {'"', "'"}:
        problems.append("The key is wrapped in quotes. Paste it without them.")
        key = key.strip("\"'")
    if not key.startswith(KEY_PREFIX):
        problems.append(f"The key doesn't start with {KEY_PREFIX}. Copy it again from the API keys page.")
    if len(key) != KEY_LENGTH:
        problems.append(f"The key is {len(key)} characters long, but Databento keys are {KEY_LENGTH}.")
    return problems


def clean(raw: str) -> str:
    """The key with stray spaces, line breaks and quotes removed."""
    return raw.strip().strip("\"'")


def scrub(text: str, *secrets: str | None) -> str:
    """Remove keys from text before it's printed or saved anywhere.

    The client sends the key with HTTP Basic auth, which is base64("<key>:"),
    so that form is removed too. As a last line of defence, anything shaped
    like a Databento key is masked even if it wasn't passed in.
    """
    for secret in secrets:
        if not secret:
            continue
        for variant in {secret, secret.strip(), clean(secret)}:
            if not variant:
                continue
            text = text.replace(variant, "[key]")
            text = text.replace(base64.b64encode(f"{variant}:".encode()).decode(), "[key]")
    text = re.sub(r"Basic\s+[A-Za-z0-9+/=]{8,}", "Basic [redacted]", text)
    text = re.sub(r"db-[A-Za-z0-9]{8,}", "db-[redacted]", text)
    return text
