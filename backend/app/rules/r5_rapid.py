"""R5 (P1) - Rapid-transfer heuristic.

Three or more active transfers touch the same parcel within a configurable window
(default 30 days). This is a heuristic: it is labelled as such and needs human review.
"""

from __future__ import annotations

from .findings import Finding
from .messages import render
from .models import ACTIVE, Dataset, RuleParams

RULE_ID = "R5"
VERSION = "1.0.0"
TITLE = "Rapid-transfer pattern (heuristic)"


def run(ds: Dataset, params: RuleParams) -> list[Finding]:
    out: list[Finding] = []
    for parcel_id in sorted(ds.transfers_by_parcel):
        dated = sorted(
            (t for t in ds.transfers_by_parcel[parcel_id] if t.status == ACTIVE and t.event_date is not None),
            key=lambda t: (t.event_date, t.id),
        )
        i = 0
        while i < len(dated):
            j = i
            while (
                j + 1 < len(dated)
                and (
                    dated[j + 1].event_date - dated[i].event_date  # type: ignore[operator]
                ).days
                <= params.rapid_window_days
            ):
                j += 1
            cluster = dated[i : j + 1]
            if len(cluster) >= params.rapid_min_events:
                first, last = cluster[0], cluster[-1]
                en, bn, nen, nbn = render(
                    "R5",
                    n=len(cluster),
                    p=parcel_id,
                    first=first.event_date.isoformat(),  # type: ignore[union-attr]
                    last=last.event_date.isoformat(),
                    min=params.rapid_min_events,  # type: ignore[union-attr]
                    days=params.rapid_window_days,
                )
                out.append(
                    Finding(
                        rule_id=RULE_ID,
                        rule_version=VERSION,
                        parcel_id=parcel_id,
                        key=f"{parcel_id}:{first.id}",
                        severity="low",
                        outcome="alert",
                        evidence_ids=tuple(sorted({x.id for x in cluster} | {x.deed_id for x in cluster})),
                        calc={
                            "threshold": params.rapid_min_events,
                            "window_days": params.rapid_window_days,
                            "count": len(cluster),
                            "transfers": [x.id for x in cluster],
                            "heuristic": True,
                        },
                        message_en=en,
                        message_bn=bn,
                        next_check_en=nen,
                        next_check_bn=nbn,
                        heuristic=True,
                    )
                )
                i = j + 1
            else:
                i += 1
    return out
