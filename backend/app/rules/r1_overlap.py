"""R1 - Overlapping transfer claim.

Two active transfers use the same synthetic portion_key in the same parcel lineage and
name different recipients. A cancelled or reversed transfer is excluded. The same dag
number alone is not enough: the portion_key and the lineage must match.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from .common import lineage_roots
from .findings import Finding, insufficient
from .messages import render
from .models import ACTIVE, Dataset, RuleParams, Transfer

RULE_ID = "R1"
VERSION = "1.0.0"
TITLE = "Overlapping transfer claim"


def run(ds: Dataset, params: RuleParams) -> list[Finding]:
    roots = lineage_roots(ds)
    groups: dict[tuple[str, str], list[Transfer]] = defaultdict(list)
    out: list[Finding] = []
    for t in ds.transfers:
        if t.status != ACTIVE:
            continue
        if not t.portion_key:
            out.append(
                insufficient(
                    RULE_ID,
                    VERSION,
                    t.parcel_id,
                    f"missing-portion:{t.id}",
                    [f"transfer {t.id} has no portion key"],
                    [t.id, t.deed_id],
                )
            )
            continue
        groups[(roots.get(t.parcel_id, t.parcel_id), t.portion_key)].append(t)

    for (_, portion_key), items in groups.items():
        items.sort(key=lambda t: t.id)
        for a, b in combinations(items, 2):
            if a.buyer == b.buyer:
                continue
            en, bn, nen, nbn = render(
                "R1", portion_key=portion_key, buyer_a=a.buyer, buyer_b=b.buyer, t_a=a.id, t_b=b.id
            )
            out.append(
                Finding(
                    rule_id=RULE_ID,
                    rule_version=VERSION,
                    parcel_id=a.parcel_id,
                    key=f"{a.id}|{b.id}",
                    severity="high",
                    outcome="alert",
                    evidence_ids=tuple(sorted({a.id, b.id, a.deed_id, b.deed_id})),
                    calc={
                        "portion_key": portion_key,
                        "claims": [
                            {
                                "transfer": x.id,
                                "deed": x.deed_id,
                                "recipient": x.buyer,
                                "date": x.event_date.isoformat() if x.event_date else None,
                            }
                            for x in (a, b)
                        ],
                    },
                    message_en=en,
                    message_bn=bn,
                    next_check_en=nen,
                    next_check_bn=nbn,
                )
            )
    return out
