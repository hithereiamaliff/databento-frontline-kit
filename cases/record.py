"""
Run every case and save what it printed as transcript.md in its folder.

  python cases/record.py            run them all
  python cases/record.py 03 06      run only the cases whose folder starts with 03 or 06

Each transcript records the date and versions, and everything the case
printed, warnings included. The key is scrubbed before anything is saved,
and the local folder path is shortened to ".".
"""

from __future__ import annotations

import datetime as dt
import importlib.metadata as md
import os
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from frontline import keys  # noqa: E402

ORDER = ["offline_repro.py", "run.py"]  # offline steps first, where a case has them


def scripts_in(case: Path) -> list[Path]:
    return [case / name for name in ORDER if (case / name).exists()]


def record(case: Path, key: str | None) -> None:
    started = dt.datetime.now(dt.timezone.utc)
    parts = []
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for script in scripts_in(case):
        proc = subprocess.run(
            [sys.executable, "-u", str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            env=env,
            cwd=ROOT,
        )
        output = keys.scrub(proc.stdout, key).replace(str(ROOT), ".")
        command = f"python {script.relative_to(ROOT).as_posix()}"
        parts.append(f"`{command}` (exit code {proc.returncode})\n\n```text\n{output.rstrip()}\n```")
        print(f"{command}: exit code {proc.returncode}")

    title = case.name.split("-", 1)[1].replace("-", " ")
    header = (
        f"# Transcript: {title}\n\n"
        f"Recorded {started:%Y-%m-%d %H:%M} UTC with databento {md.version('databento')}, "
        f"pandas {md.version('pandas')} and Python {platform.python_version()} on {platform.system()} "
        f"{platform.release()}. Produced by `python cases/record.py`; nothing here was edited by hand.\n"
    )
    (case / "transcript.md").write_text(header + "\n" + "\n\n".join(parts) + "\n", encoding="utf-8", newline="\n")


def main(prefixes: list[str]) -> int:
    raw, _ = keys.find_key(ROOT / ".env")
    key = keys.clean(raw) if raw else None
    cases = sorted(p for p in HERE.iterdir() if p.is_dir() and scripts_in(p))
    if prefixes:
        cases = [c for c in cases if c.name.startswith(tuple(prefixes))]
    for case in cases:
        record(case, key)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
