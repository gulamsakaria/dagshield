"""Database side of the hash-chained audit log (append and verify)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auditlog.chain import GENESIS, ChainResult, make_entry, verify_chain
from .models import AuditLogEntry


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def append(db: Session, event_type: str, subject_id: str, payload: dict[str, Any]) -> AuditLogEntry:
    last = db.execute(
        select(AuditLogEntry).order_by(AuditLogEntry.seq.desc()).limit(1).with_for_update()
    ).scalar_one_or_none()
    prev = last.entry_hash if last else GENESIS
    row = AuditLogEntry(**make_entry(prev, event_type, subject_id, payload, now_iso()))
    db.add(row)
    db.flush()
    return row


def entries(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(select(AuditLogEntry).order_by(AuditLogEntry.seq)).scalars().all()
    return [
        {
            "seq": r.seq,
            "event_type": r.event_type,
            "subject_id": r.subject_id,
            "payload_hash": r.payload_hash,
            "prev_hash": r.prev_hash,
            "entry_hash": r.entry_hash,
            "timestamp": r.timestamp,
        }
        for r in rows
    ]


def verify(db: Session) -> ChainResult:
    return verify_chain(entries(db))
