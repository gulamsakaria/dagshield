"""Hash-chained, append-only audit log (pure functions).

Each entry stores the hash of the entry before it. Editing an entry, or removing one
from the middle or the start, breaks chain verification. Removing entries from the very
end cannot be detected from the log alone, so /api/audit-log/verify also reports the
head hash and length; record those somewhere outside the database to catch truncation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

GENESIS = "0" * 64


def payload_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def entry_hash(prev_hash: str, event_type: str, subject_id: str, p_hash: str, timestamp: str) -> str:
    material = "\x1f".join([prev_hash, event_type, subject_id, p_hash, timestamp])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def make_entry(
    prev_hash: str, event_type: str, subject_id: str, payload: dict[str, Any], timestamp: str
) -> dict[str, str]:
    p_hash = payload_hash(payload)
    return {
        "event_type": event_type,
        "subject_id": subject_id,
        "payload_hash": p_hash,
        "prev_hash": prev_hash,
        "entry_hash": entry_hash(prev_hash, event_type, subject_id, p_hash, timestamp),
        "timestamp": timestamp,
    }


@dataclass(frozen=True)
class ChainResult:
    ok: bool
    checked: int
    head_hash: str
    broken_at: int | None = None
    reason: str | None = None


def verify_chain(entries: list[dict[str, Any]]) -> ChainResult:
    """`entries` must be in append order."""
    prev = GENESIS
    for index, e in enumerate(entries):
        if e["prev_hash"] != prev:
            return ChainResult(False, index, prev, index, "previous-hash link is broken")
        expected = entry_hash(e["prev_hash"], e["event_type"], e["subject_id"], e["payload_hash"], e["timestamp"])
        if expected != e["entry_hash"]:
            return ChainResult(False, index, prev, index, "entry content does not match its hash")
        prev = e["entry_hash"]
    return ChainResult(True, len(entries), prev)
