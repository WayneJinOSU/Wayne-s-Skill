#!/usr/bin/env python3
"""Thin launcher for the audited Simon daily engine in the KhQuant workspace."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


DEFAULT_PROJECT = Path("/Users/a/PycharmProjects/khquant")


def main() -> None:
    project = Path(os.environ.get("KHQUANT_PROJECT_ROOT", DEFAULT_PROJECT)).expanduser().resolve()
    entrypoint = project / "research/simon_tail_risk/daily_check.py"
    if not entrypoint.exists():
        raise FileNotFoundError(
            f"Simon daily entrypoint not found: {entrypoint}; "
            "set KHQUANT_PROJECT_ROOT if the workspace moved"
        )
    command = [sys.executable, str(entrypoint), *sys.argv[1:]]
    raise SystemExit(subprocess.run(command, cwd=project, check=False).returncode)


if __name__ == "__main__":
    main()

