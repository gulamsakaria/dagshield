"""The result type every rule returns."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from .messages import render


def num(value: Decimal | None) -> float | None:
    """Decimal -> float for JSON output. None stays None."""
    return None if value is None else float(value)


def fmt(value: Decimal) -> str:
    """Decimal -> short readable string (12.0 -> '12')."""
    return format(value.normalize(), "f") if value != 0 else "0"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    rule_version: str
    parcel_id: str
    key: str
    severity: str  # high | medium | low | review
    outcome: str  # alert | insufficient_data
    evidence_ids: tuple[str, ...]
    calc: dict[str, Any]
    message_en: str
    message_bn: str
    next_check_en: str
    next_check_bn: str
    heuristic: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def alert_id(self) -> str:
        digest = hashlib.sha256(f"{self.rule_id}|{self.rule_version}|{self.key}".encode()).hexdigest()
        return "AL-" + digest[:10].upper()

    def match_key(self) -> tuple[str, str, str]:
        return (self.rule_id, self.key, self.outcome)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.alert_id,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "parcel_id": self.parcel_id,
            "key": self.key,
            "severity": self.severity,
            "outcome": self.outcome,
            "evidence_ids": list(self.evidence_ids),
            "calc": self.calc,
            "message_en": self.message_en,
            "message_bn": self.message_bn,
            "next_check_en": self.next_check_en,
            "next_check_bn": self.next_check_bn,
            "heuristic": self.heuristic,
        }


def insufficient(
    rule_id: str,
    version: str,
    parcel_id: str,
    key: str,
    reasons: list[str],
    evidence: list[str],
) -> Finding:
    reason = "; ".join(reasons)
    en, bn, nen, nbn = render("insufficient", reason=reason)
    return Finding(
        rule_id=rule_id,
        rule_version=version,
        parcel_id=parcel_id,
        key=key,
        severity="review",
        outcome="insufficient_data",
        evidence_ids=tuple(sorted(set(evidence))),
        calc={"reasons": reasons},
        message_en=en,
        message_bn=bn,
        next_check_en=nen,
        next_check_bn=nbn,
    )
