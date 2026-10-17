"""Guard that keeps real personal data out of the fixtures and the demo.

Only team-created tokens such as OWNER-A / BUYER-B are allowed as identities. The scan
also rejects anything that looks like an NID, a phone number or an email address.
"""

from __future__ import annotations

import re
from typing import Any

TOKEN_RE = re.compile(r"^(OWNER|BUYER|SELLER)-[A-Z0-9]{1,12}$")
LONG_DIGITS = re.compile(r"(?<![\d-])\d{10,17}(?![\d-])")
BD_PHONE = re.compile(r"(?:\+?88)?01[3-9]\d{8}")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
IDENTITY_KEYS = {"owner", "seller", "buyer", "recipient"}


def scan_fixture(obj: Any, path: str = "$") -> list[str]:
    """Return a list of problems; an empty list means the fixture is clean."""
    problems: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            here = f"{path}.{key}"
            if key in IDENTITY_KEYS and isinstance(value, str) and not TOKEN_RE.match(value):
                problems.append(f"{here}: identity must be a synthetic token, got {value!r}")
            problems.extend(scan_fixture(value, here))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            problems.extend(scan_fixture(value, f"{path}[{i}]"))
    elif isinstance(obj, str):
        for label, rx in (("NID-like number", LONG_DIGITS), ("phone number", BD_PHONE), ("email", EMAIL)):
            if rx.search(obj):
                problems.append(f"{path}: contains a {label}")
    return problems
