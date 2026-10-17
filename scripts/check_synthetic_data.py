#!/usr/bin/env python3
"""Fail if any fixture contains non-synthetic identities, NID-like numbers, phones or emails."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.privacy import scan_fixture  # noqa: E402


def main() -> int:
    files = sorted((ROOT / "fixtures").rglob("*.json"))
    bad = 0
    for f in files:
        problems = scan_fixture(json.loads(f.read_text(encoding="utf-8")))
        for p in problems:
            print(f"{f.relative_to(ROOT)}: {p}")
        bad += len(problems)
    print(f"check_synthetic_data: {len(files)} fixture file(s) scanned, {bad} problem(s).")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
