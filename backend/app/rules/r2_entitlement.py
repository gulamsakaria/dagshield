"""R2 - Transfer exceeds entitlement.

A transfer amount is larger than the entitlement available just before the event.
Available = Opening + RecognizedIncoming - ActiveOutgoing, in chronological order.
"""

from __future__ import annotations

from datetime import date

from .common import balance_before
from .findings import Finding, fmt, insufficient, num
from .messages import render
from .models import ACTIVE, Dataset, RuleParams

RULE_ID = "R2"
VERSION = "1.0.0"
TITLE = "Transfer exceeds entitlement"


def run(ds: Dataset, params: RuleParams) -> list[Finding]:
    out: list[Finding] = []
    active = [t for t in ds.transfers if t.status == ACTIVE]
    for t in sorted(active, key=lambda t: (t.event_date or date.max, t.id)):
        reasons: list[str] = []
        if t.event_date is None:
            reasons.append(f"transfer {t.id} has no event date")
        if t.area is None:
            reasons.append(f"transfer {t.id} has no area")
        if reasons:
            out.append(insufficient(RULE_ID, VERSION, t.parcel_id, t.id, reasons, [t.id, t.deed_id]))
            continue
        assert t.event_date is not None and t.area is not None
        b = balance_before(ds, t.parcel_id, t.seller, t.event_date, t.id)
        if b.insufficient or b.available is None or b.opening is None:
            out.append(
                insufficient(
                    RULE_ID,
                    VERSION,
                    t.parcel_id,
                    t.id,
                    b.insufficient or ["opening entitlement unknown"],
                    [t.id, t.deed_id, *b.evidence],
                )
            )
            continue
        if t.area > b.available:
            excess = t.area - b.available
            en, bn, nen, nbn = render(
                "R2",
                t=t.id,
                seller=t.seller,
                attempted=fmt(t.area),
                available=fmt(b.available),
                opening=fmt(b.opening),
                incoming=fmt(b.incoming),
                outgoing=fmt(b.outgoing),
                excess=fmt(excess),
            )
            out.append(
                Finding(
                    rule_id=RULE_ID,
                    rule_version=VERSION,
                    parcel_id=t.parcel_id,
                    key=t.id,
                    severity="high",
                    outcome="alert",
                    evidence_ids=tuple(sorted({t.id, t.deed_id, *b.evidence})),
                    calc={
                        "owner": t.seller,
                        "unit": "decimal",
                        "opening": num(b.opening),
                        "opening_source": b.opening_source,
                        "recognized_incoming": num(b.incoming),
                        "prior_active_outgoing": num(b.outgoing),
                        "available": num(b.available),
                        "attempted": num(t.area),
                        "excess": num(excess),
                        "formula": "available = opening + recognized_incoming - active_outgoing",
                    },
                    message_en=en,
                    message_bn=bn,
                    next_check_en=nen,
                    next_check_bn=nbn,
                )
            )
    return out
