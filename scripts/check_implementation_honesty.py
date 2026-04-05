#!/usr/bin/env python3
"""Fail CI when runtime code contains fake-success placeholder patterns."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SCAN_DIRS = [
    ROOT / "src",
    ROOT / "webapp" / "backend",
    ROOT / "webapp" / "frontend" / "src",
]

IGNORE_PATH_PARTS = {
    ".venv",
    "venv",
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".cursor",
    "docs",
    "tests",
}

ALLOW_FILE_NAMES = {
    "example_tools.py",
}

PATTERNS = [
    re.compile(r"\bsimulat(e|ed|ion)\b", re.IGNORECASE),
    re.compile(r"\bplaceholder (implementation|method|string)\b", re.IGNORECASE),
    re.compile(r"\breturn (a |the )?placeholder\b", re.IGNORECASE),
    re.compile(r"\bmock response\b", re.IGNORECASE),
    re.compile(r"\bstatic list for demonstration\b", re.IGNORECASE),
    re.compile(r"\bfor now, we('| wi)ll\b", re.IGNORECASE),
]

ALLOW_TEXT_PATTERNS = [
    re.compile(r"under construction", re.IGNORECASE),
    re.compile(r"not_implemented", re.IGNORECASE),
]


def should_skip(path: Path) -> bool:
    if path.name in ALLOW_FILE_NAMES:
        return True
    return any(part in IGNORE_PATH_PARTS for part in path.parts)


def main() -> int:
    violations: list[tuple[Path, int, str, str]] = []

    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".py", ".tsx", ".ts", ".jsx", ".js"}:
                continue
            if should_skip(path):
                continue

            text = path.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()

            for idx, line in enumerate(lines, start=1):
                if any(allow.search(line) for allow in ALLOW_TEXT_PATTERNS):
                    continue
                for pattern in PATTERNS:
                    if pattern.search(line):
                        violations.append((path, idx, pattern.pattern, line.strip()))
                        break

    if not violations:
        print("Implementation honesty check passed.")
        return 0

    print("Implementation honesty check failed. Banned placeholder patterns found:")
    for path, line_no, pattern, line in violations:
        rel = path.relative_to(ROOT)
        print(f"- {rel}:{line_no} pattern={pattern} line={line}")

    print(
        "\nFix required: implement behavior or replace with explicit "
        "'not_implemented' / 'under construction' contract."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
