"""Check a deed copy against the signed record. Pure function, no database."""

from __future__ import annotations

import hmac
from typing import Any

from .canonical import FIELDS, normalize_fields, record_hash
from .signing import Signer


def _eq(a: str | None, b: str | None) -> bool:
    return hmac.compare_digest((a or "").encode(), (b or "").encode())


def verify_copy(
    signer: Signer,
    stored: dict[str, Any] | None,
    copy_fields: dict[str, Any],
    qr_hash: str | None = None,
    qr_signature: str | None = None,
) -> dict[str, Any]:
    """`stored` = {"record", "hash", "signature"} for the registered deed, or None."""
    norm = normalize_fields(copy_fields)
    recomputed = record_hash(norm)
    if stored is None:
        return {
            "result": "not_found",
            "recomputed_hash": recomputed,
            "signed_hash": None,
            "qr_hash": qr_hash,
            "signature_valid": False,
            "qr_signature_valid": None,
            "mismatched_fields": [],
            "message_en": "Deed reference not found in the supplied dataset.",
            "message_bn": "দলিলের রেফারেন্স সরবরাহকৃত ডেটাসেটে পাওয়া যায়নি।",
        }
    signed_hash = stored["hash"]
    signature_valid = signer.verify(signed_hash, stored["signature"])
    hash_equal = _eq(recomputed, signed_hash)
    qr_consistent = True
    qr_signature_valid: bool | None = None
    if qr_hash is not None:
        qr_consistent = _eq(qr_hash, signed_hash)
        if qr_signature is not None:
            qr_signature_valid = signer.verify(qr_hash, qr_signature)
            qr_consistent = qr_consistent and qr_signature_valid
    mismatched = [k for k in FIELDS if norm.get(k) != stored["record"].get(k)]
    match = signature_valid and hash_equal and qr_consistent
    return {
        "result": "match" if match else "mismatch",
        "recomputed_hash": recomputed,
        "signed_hash": signed_hash,
        "qr_hash": qr_hash,
        "signature_valid": signature_valid,
        "qr_signature_valid": qr_signature_valid,
        "mismatched_fields": mismatched,
        "message_en": (
            "This copy matches the signed record."
            if match
            else "This copy does not match the signed record. Human review needed."
        ),
        "message_bn": (
            "এই কপি স্বাক্ষরিত রেকর্ডের সাথে মিলেছে।"
            if match
            else "এই কপি স্বাক্ষরিত রেকর্ডের সাথে মেলেনি। মানুষের পর্যালোচনা প্রয়োজন।"
        ),
    }
