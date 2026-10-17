"""Canonical deed record: fixed field order, one date format, one area unit.

The same synthetic deed always produces the same bytes, so the same hash.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

FIELDS = (
    "deed_ref",
    "registration_date",
    "registration_status",
    "seller",
    "buyer",
    "parcel_id",
    "area_decimal",
    "source_id",
)


def _area(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return format(Decimal(str(value)).quantize(Decimal("0.0001")), "f")
    except (InvalidOperation, ValueError):
        return str(value)  # unparseable text stays as typed, so it will not match


def _date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        return str(value)


def make_record(
    deed_ref: str,
    registration_date: Any,
    registration_status: str | None,
    seller: str | None,
    buyer: str | None,
    parcel_id: str | None,
    area_decimal: Any,
    source_id: str | None,
) -> dict[str, str | None]:
    """Build the canonical record. Strings are kept exactly as given (no trimming)."""
    return {
        "deed_ref": deed_ref,
        "registration_date": _date(registration_date),
        "registration_status": registration_status,
        "seller": seller,
        "buyer": buyer,
        "parcel_id": parcel_id,
        "area_decimal": _area(area_decimal),
        "source_id": source_id,
    }


def normalize_fields(fields: dict[str, Any]) -> dict[str, str | None]:
    """Normalise the fields printed on a deed copy into canonical form."""
    return make_record(**{k: fields.get(k) for k in FIELDS})


def canonical_bytes(record: dict[str, str | None]) -> bytes:
    ordered = {k: record.get(k) for k in FIELDS}
    return json.dumps(ordered, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def record_hash(record: dict[str, str | None]) -> str:
    return hashlib.sha256(canonical_bytes(record)).hexdigest()
