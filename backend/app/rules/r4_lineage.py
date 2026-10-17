"""R4 - Lineage or area anomaly.

(a) A parent-child link is uncertain (confidence below the minimum), or
(b) child areas sum to more than the parent area beyond a set tolerance.
Alerts show exact IDs, the confidence and the arithmetic, and always require review.
"""

from __future__ import annotations

from decimal import Decimal

from .findings import Finding, fmt, insufficient, num
from .messages import render
from .models import Dataset, RuleParams

RULE_ID = "R4"
VERSION = "1.0.0"
TITLE = "Lineage or area anomaly"


def run(ds: Dataset, params: RuleParams) -> list[Finding]:
    out: list[Finding] = []
    for link in sorted(ds.lineage, key=lambda x: x.id):
        if link.confidence is None:
            out.append(
                insufficient(
                    RULE_ID,
                    VERSION,
                    link.parent_id,
                    f"lineage:{link.id}",
                    [f"lineage link {link.id} has no confidence value"],
                    [link.id],
                )
            )
        elif link.confidence < params.lineage_confidence_min:
            en, bn, nen, nbn = render(
                "R4_uncertain",
                p=link.parent_id,
                c=link.child_id,
                conf=fmt(link.confidence),
                min=fmt(params.lineage_confidence_min),
            )
            out.append(
                Finding(
                    rule_id=RULE_ID,
                    rule_version=VERSION,
                    parcel_id=link.parent_id,
                    key=f"lineage:{link.id}",
                    severity="medium",
                    outcome="alert",
                    evidence_ids=tuple(sorted({link.id, link.parent_id, link.child_id})),
                    calc={
                        "link": link.id,
                        "parent": link.parent_id,
                        "child": link.child_id,
                        "confidence": num(link.confidence),
                        "minimum": num(params.lineage_confidence_min),
                    },
                    message_en=en,
                    message_bn=bn,
                    next_check_en=nen,
                    next_check_bn=nbn,
                )
            )

    for parent_id in sorted(ds.children_by_parent):
        links = ds.children_by_parent[parent_id]
        parent = ds.parcel_by_id.get(parent_id)
        children = [ds.parcel_by_id.get(x.child_id) for x in links]
        reasons = []
        if parent is None or parent.area is None:
            reasons.append(f"parent parcel {parent_id} has no area")
        for link, child in zip(links, children, strict=True):
            if child is None or child.area is None:
                reasons.append(f"child parcel {link.child_id} has no area")
        evidence = [parent_id, *[x.id for x in links], *[x.child_id for x in links]]
        if reasons:
            out.append(insufficient(RULE_ID, VERSION, parent_id, f"area:{parent_id}", reasons, evidence))
            continue
        assert parent is not None and parent.area is not None
        total = sum((c.area for c in children if c and c.area is not None), Decimal("0"))
        diff = total - parent.area
        if diff > params.area_tolerance:
            en, bn, nen, nbn = render(
                "R4_area",
                p=parent_id,
                sum=fmt(total),
                parent=fmt(parent.area),
                diff=fmt(diff),
                tol=fmt(params.area_tolerance),
            )
            out.append(
                Finding(
                    rule_id=RULE_ID,
                    rule_version=VERSION,
                    parcel_id=parent_id,
                    key=f"area:{parent_id}",
                    severity="medium",
                    outcome="alert",
                    evidence_ids=tuple(sorted(set(evidence))),
                    calc={
                        "parent": parent_id,
                        "parent_area": num(parent.area),
                        "children": {c.id: num(c.area) for c in children if c},
                        "children_total": num(total),
                        "difference": num(diff),
                        "tolerance": num(params.area_tolerance),
                        "unit": "decimal",
                    },
                    message_en=en,
                    message_bn=bn,
                    next_check_en=nen,
                    next_check_bn=nbn,
                )
            )
    return out
