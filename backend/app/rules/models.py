"""Plain, immutable data structures the rules work on.

Rules never touch the database or HTTP. They receive a `Dataset` and return findings.
Conversion of units (bigha/katha -> decimal) happens when data is loaded, never here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import cached_property
from typing import Any

ACTIVE = "active"
TRANSFER_STATUSES = frozenset({"active", "cancelled", "reversed"})


def dec(value: Any) -> Decimal | None:
    """Convert a number-like value to Decimal. None stays None (never becomes zero)."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"not a number: {value!r}") from exc


def to_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


@dataclass(frozen=True)
class Parcel:
    id: str
    label: str
    survey_type: str
    dag_no: str | None
    area: Decimal | None
    status: str = "active"


@dataclass(frozen=True)
class Lineage:
    id: str
    parent_id: str
    child_id: str
    relationship: str
    confidence: Decimal | None
    source_id: str | None = None


@dataclass(frozen=True)
class Entitlement:
    id: str
    parcel_id: str
    owner: str
    opening_area: Decimal | None
    effective_date: date | None
    source_id: str | None = None
    confidence: Decimal | None = None


@dataclass(frozen=True)
class Deed:
    id: str
    parcel_id: str
    registration_date: date | None
    status: str
    seller: str
    buyer: str
    area: Decimal | None
    source_id: str | None = None


@dataclass(frozen=True)
class Transfer:
    id: str
    deed_id: str
    parcel_id: str
    portion_key: str | None
    seller: str
    buyer: str
    area: Decimal | None
    event_date: date | None
    status: str = ACTIVE
    cancelled_on: date | None = None


@dataclass(frozen=True)
class Mutation:
    id: str
    transfer_id: str | None
    parcel_id: str
    date: date | None
    status: str
    area: Decimal | None
    recipient: str | None
    source_id: str | None = None


@dataclass(frozen=True)
class RuleParams:
    area_tolerance: Decimal = Decimal("0")
    lineage_confidence_min: Decimal = Decimal("0.8")
    rapid_window_days: int = 30
    rapid_min_events: int = 3
    enable_r5: bool = True


@dataclass
class Dataset:
    parcels: list[Parcel] = field(default_factory=list)
    lineage: list[Lineage] = field(default_factory=list)
    entitlements: list[Entitlement] = field(default_factory=list)
    deeds: list[Deed] = field(default_factory=list)
    transfers: list[Transfer] = field(default_factory=list)
    mutations: list[Mutation] = field(default_factory=list)

    # ---- indexes (built once, so audits stay fast on ~1,000 records) ----
    @cached_property
    def parcel_by_id(self) -> dict[str, Parcel]:
        return {p.id: p for p in self.parcels}

    @cached_property
    def deed_by_id(self) -> dict[str, Deed]:
        return {d.id: d for d in self.deeds}

    @cached_property
    def transfers_by_parcel(self) -> dict[str, list[Transfer]]:
        out: dict[str, list[Transfer]] = {}
        for t in self.transfers:
            out.setdefault(t.parcel_id, []).append(t)
        return out

    @cached_property
    def entitlements_by_key(self) -> dict[tuple[str, str], list[Entitlement]]:
        out: dict[tuple[str, str], list[Entitlement]] = {}
        for e in self.entitlements:
            out.setdefault((e.parcel_id, e.owner), []).append(e)
        return out

    @cached_property
    def mutations_by_transfer(self) -> dict[str, list[Mutation]]:
        out: dict[str, list[Mutation]] = {}
        for m in self.mutations:
            if m.transfer_id:
                out.setdefault(m.transfer_id, []).append(m)
        return out

    @cached_property
    def children_by_parent(self) -> dict[str, list[Lineage]]:
        out: dict[str, list[Lineage]] = {}
        for link in self.lineage:
            out.setdefault(link.parent_id, []).append(link)
        return out

    # ---- loading ----
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Dataset:
        """Build a Dataset from a fixture dictionary (strings/numbers -> typed values)."""
        transfers = []
        for t in data.get("transfers", []):
            status = t.get("status", ACTIVE)
            if status not in TRANSFER_STATUSES:
                raise ValueError(f"transfer {t.get('id')}: unknown status {status!r}")
            transfers.append(
                Transfer(
                    id=t["id"],
                    deed_id=t["deed_id"],
                    parcel_id=t["parcel_id"],
                    portion_key=t.get("portion_key"),
                    seller=t["seller"],
                    buyer=t["buyer"],
                    area=dec(t.get("area")),
                    event_date=to_date(t.get("event_date")),
                    status=status,
                    cancelled_on=to_date(t.get("cancelled_on")),
                )
            )
        return cls(
            parcels=[
                Parcel(
                    id=p["id"],
                    label=p.get("label", ""),
                    survey_type=p.get("survey_type", "RS"),
                    dag_no=p.get("dag_no"),
                    area=dec(p.get("area_decimal")),
                    status=p.get("status", "active"),
                )
                for p in data.get("parcels", [])
            ],
            lineage=[
                Lineage(
                    id=x["id"],
                    parent_id=x["parent_id"],
                    child_id=x["child_id"],
                    relationship=x.get("relationship", "split"),
                    confidence=dec(x.get("confidence")),
                    source_id=x.get("source_id"),
                )
                for x in data.get("lineage", [])
            ],
            entitlements=[
                Entitlement(
                    id=e["id"],
                    parcel_id=e["parcel_id"],
                    owner=e["owner"],
                    opening_area=dec(e.get("opening_area")),
                    effective_date=to_date(e.get("effective_date")),
                    source_id=e.get("source_id"),
                    confidence=dec(e.get("confidence")),
                )
                for e in data.get("entitlements", [])
            ],
            deeds=[
                Deed(
                    id=d["id"],
                    parcel_id=d["parcel_id"],
                    registration_date=to_date(d.get("registration_date")),
                    status=d.get("status", "registered"),
                    seller=d["seller"],
                    buyer=d["buyer"],
                    area=dec(d.get("area_decimal")),
                    source_id=d.get("source_id"),
                )
                for d in data.get("deeds", [])
            ],
            transfers=transfers,
            mutations=[
                Mutation(
                    id=m["id"],
                    transfer_id=m.get("transfer_id"),
                    parcel_id=m["parcel_id"],
                    date=to_date(m.get("date")),
                    status=m.get("status", "recorded"),
                    area=dec(m.get("area")),
                    recipient=m.get("recipient"),
                    source_id=m.get("source_id"),
                )
                for m in data.get("mutations", [])
            ],
        )
