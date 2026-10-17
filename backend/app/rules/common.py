"""Helpers shared by rules: cancellation timing, balance, lineage grouping."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from .models import ACTIVE, Dataset, Transfer

LAST_DATE = date.max
LAST_ID = "\uffff"


def counts_at(t: Transfer, at: date) -> bool:
    """Does this transfer still count at date `at`?

    Cancelled or reversed events stop counting once the cancellation takes effect.
    """
    if t.status == ACTIVE:
        return True
    return t.cancelled_on is not None and t.cancelled_on > at


def lineage_roots(ds: Dataset) -> dict[str, str]:
    """Group parcels connected by explicit lineage links (union-find). Returns parcel -> root."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for link in ds.lineage:
        ra, rb = find(link.parent_id), find(link.child_id)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    return {p: find(p) for p in list(parent)}


@dataclass
class Balance:
    opening: Decimal | None = None
    incoming: Decimal = Decimal("0")
    outgoing: Decimal = Decimal("0")
    available: Decimal | None = None
    opening_source: str = "entitlement"
    insufficient: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


def balance_before(ds: Dataset, parcel_id: str, owner: str, at: date, event_id: str) -> Balance:
    """Available = Opening + RecognizedIncoming - ActiveOutgoing, just before an event.

    Events are ordered by (date, id). A missing value never becomes zero: it adds a
    reason to `insufficient` and `available` stays None.
    """
    b = Balance()
    ents = ds.entitlements_by_key.get((parcel_id, owner), [])
    usable = []
    for e in ents:
        if e.opening_area is None or e.effective_date is None:
            b.insufficient.append(f"entitlement {e.id} has a missing area or date")
        elif e.effective_date <= at:
            usable.append(e)
    for t in ds.transfers_by_parcel.get(parcel_id, []):
        if t.id == event_id or owner not in (t.seller, t.buyer):
            continue
        if t.status != ACTIVE and t.cancelled_on is None:
            b.insufficient.append(f"transfer {t.id} is {t.status} with no cancellation date")
            continue
        if t.event_date is None:
            b.insufficient.append(f"transfer {t.id} has no event date")
            continue
        if (t.event_date, t.id) >= (at, event_id):
            continue
        if not counts_at(t, at):
            continue
        if t.area is None:
            b.insufficient.append(f"transfer {t.id} has no area")
            continue
        if t.seller == owner:
            b.outgoing += t.area
            b.evidence.append(t.id)
        elif t.buyer == owner:
            deed = ds.deed_by_id.get(t.deed_id)
            if deed is not None and deed.status == "registered":
                b.incoming += t.area
                b.evidence.append(t.id)
    if usable:
        b.opening = sum((e.opening_area for e in usable), Decimal("0"))  # type: ignore[misc]
        b.evidence.extend(e.id for e in usable)
    elif b.incoming > 0:
        # Owner holds land only through recorded transfers; no earlier entitlement exists.
        b.opening = Decimal("0")
        b.opening_source = "none_recorded"
    elif not ents:
        b.insufficient.append(f"no entitlement record for {owner} on {parcel_id}")
    if not b.insufficient and b.opening is not None:
        b.available = b.opening + b.incoming - b.outgoing
    return b


def ownership_summary(ds: Dataset, parcel_id: str) -> list[dict]:
    """Final balance per owner on a parcel, counting every transfer still active."""
    owners: list[str] = []
    for e in ds.entitlements:
        if e.parcel_id == parcel_id and e.owner not in owners:
            owners.append(e.owner)
    for t in ds.transfers_by_parcel.get(parcel_id, []):
        for who in (t.seller, t.buyer):
            if who not in owners:
                owners.append(who)
    out = []
    for owner in owners:
        b = balance_before(ds, parcel_id, owner, LAST_DATE, LAST_ID)
        out.append(
            {
                "owner": owner,
                "opening": None if b.opening is None else float(b.opening),
                "incoming": float(b.incoming),
                "outgoing": float(b.outgoing),
                "balance": None if b.available is None else float(b.available),
                "insufficient_reasons": b.insufficient,
            }
        )
    return out
