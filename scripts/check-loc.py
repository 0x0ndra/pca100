#!/usr/bin/env python3
"""Fail if any source file exceeds 300 lines of actual code."""
import subprocess
import sys
from pathlib import Path

LIMIT = 300
EXEMPT = {"frontend/src/lib/spectral-locus.json"}
SUFFIXES = {".py", ".ts", ".tsx"}


def code_lines(path: Path) -> int:
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "//")):
            count += 1
    return count


def main() -> int:
    files = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    failures = []
    for name in files:
        path = Path(name)
        if name in EXEMPT or path.suffix not in SUFFIXES or not path.exists():
            continue
        lines = code_lines(path)
        if lines > LIMIT:
            failures.append(f"{name}: {lines} > {LIMIT} LOC")
    for failure in failures:
        print(failure, file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
