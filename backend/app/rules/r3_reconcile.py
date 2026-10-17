"""R3 - Deed and mutation gap.

A registered transfer has no linked mutation entry in the supplied data, or the linked
fields disagree. The wording is always "not found in supplied dataset" or "records do not
align" - never a fraud label.
"""

from __future__ import annotations

from .findings import Finding, insufficient
from .messages import render
from .models import ACTIVE, Dataset, Mutation, RuleParams, Transfer

RULE_ID = "R3"
VERSION = "1.0.0"
TITLE = "Deed and mutation gap"


def _diffs(t: Transfer, m: Mutation) -> list[str]:
    diffs: list[str] = []
    if m.status != "recorded":
        diffs.append(f"mutation status is {m.status}")
    if m.recipient != t.buyer:
        diffs.append(f"recipient {t.buyer} vs {m.recipient}")
    if m.area != t.area:
        diffs.append(f"area {t.area} vs {m.area}")
    return diffs


def run(ds: Dataset, params: RuleParams) -> list[Finding]:
    out: list[Finding] = []
    for t in sorted(ds.transfers, key=lambda t: t.id):
        if t.status != ACTIVE:
            continue
        deed = ds.deed_by_id.get(t.deed_id)
        if deed is None or deed.status != "registered":
            continue
        links = ds.mutations_by_transfer.get(t.id, [])
        if not links:
            en, bn, nen, nbn = render("R3_gap", t=t.id, deed=deed.id)
            out.append(
                Finding(
                    rule_id=RULE_ID,
                    rule_version=VERSION,
                    parcel_id=t.parcel_id,
                    key=t.id,
                    severity="medium",
                    outcome="alert",
                    evidence_ids=(deed.id, t.id),
                    calc={"reason": "no linked mutation entry in supplied dataset", "transfer": t.id, "deed": deed.id},
                    message_en=en,
                    message_bn=bn,
                    next_check_en=nen,
                    next_check_bn=nbn,
                )
            )
            continue
        missing = []
        if t.area is None:
            missing.append(f"transfer {t.id} has no area")
        missing += [f"mutation {m.id} has no area" for m in links if m.area is None]
        if missing:
            out.append(
                insufficient(RULE_ID, VERSION, t.parcel_id, t.id, missing, [t.id, deed.id, *[m.id for m in links]])
            )
            continue
        if any(not _diffs(t, m) for m in links):
            continue
        first = sorted(links, key=lambda m: m.id)[0]
        diffs = _diffs(t, first)
        en, bn, nen, nbn = render("R3_mismatch", t=t.id, m=first.id, diffs="; ".join(diffs))
        out.append(
            Finding(
                rule_id=RULE_ID,
                rule_version=VERSION,
                parcel_id=t.parcel_id,
                key=t.id,
                severity="medium",
                outcome="alert",
                evidence_ids=tuple(sorted({deed.id, t.id, *[m.id for m in links]})),
                calc={"reason": "records do not align", "differences": diffs, "transfer": t.id, "mutation": first.id},
                message_en=en,
                message_bn=bn,
                next_check_en=nen,
                next_check_bn=nbn,
            )
        )
    return out
