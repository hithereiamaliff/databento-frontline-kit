"""
Case 4: "I get an authentication error."

Shows what a customer actually sees for the usual causes, using made-up keys,
so no real key ever appears in the output. The last step checks that the real
key from .env works, and prints only the result.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common  # noqa: E402

import databento as db  # noqa: E402

from frontline import keys  # noqa: E402

FAKE = "db-Fake0Key0For0Tests0Only000000"  # right shape, but not a real key


def attempt(label: str, make_client) -> None:
    print(f"\n{label}")
    try:
        client = make_client()
        client.metadata.list_datasets()
        print("  Result: accepted")
    except db.BentoClientError as exc:
        print(f"  Result: BentoClientError {exc.http_status}")
        print("  " + _common.safe(exc.message or "").replace("\n", "\n  "))
    except Exception as exc:
        print(f"  Result: {type(exc).__name__}: {_common.safe(exc)}")


def main() -> None:
    real = _common.key()  # read now, so the next steps can hide it from the environment
    saved = {name: os.environ.pop(name, None) for name in [keys.ENV_NAME, "DATABENTO_KEY"]}
    try:
        _common.heading("1. What the customer sees")
        attempt("a) No key anywhere: db.Historical()", lambda: db.Historical())
        attempt("b) A well-formed key that isn't valid", lambda: db.Historical(FAKE))
        attempt("c) The same key with a line break on the end", lambda: db.Historical(FAKE + "\n"))
        attempt("d) The same key pasted with its quotes", lambda: db.Historical(f'"{FAKE}"'))
        os.environ["DATABENTO_KEY"] = FAKE
        attempt("e) Key saved as DATABENTO_KEY instead of DATABENTO_API_KEY", lambda: db.Historical())

        _common.heading("2. What preflight's key check says for each")
        for label, raw, saved_under_wrong_name in [
            ("a)", None, False),
            ("b)", FAKE, False),
            ("c)", FAKE + "\n", False),
            ("d)", f'"{FAKE}"', False),
            ("e)", None, True),
        ]:
            if saved_under_wrong_name:
                os.environ["DATABENTO_KEY"] = FAKE
            else:
                os.environ.pop("DATABENTO_KEY", None)
            problems = keys.shape_problems(raw)
            if not problems:
                problems = ["Right shape, so only Databento can say whether it's valid: the server answers 401."]
            for problem in problems:
                print(f"{label} {problem}")
    finally:
        os.environ.pop("DATABENTO_KEY", None)
        for name, value in saved.items():
            if value is not None:
                os.environ[name] = value

    _common.heading("3. The real key from .env (never printed)")
    datasets = db.Historical(real).metadata.list_datasets()
    print(f"Accepted. This account can see {len(datasets)} datasets.")


if __name__ == "__main__":
    main()
