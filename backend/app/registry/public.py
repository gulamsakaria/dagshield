"""Public "Check Land" lookup: is this person the registered owner of this plot?

Reads the same registry tables the officer portal writes, so a deed registered by an officer shows up here at once.
It returns ONLY: registered owner name(s), a status, the mutation status and a short list of previous owners with
sale dates. No alerts, risk scores, officer names, audit entries or blocked attempts ever leave this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import audit
from ..db import models as m
from . import khatian
from .checker import clean, key


@dataclass(frozen=True)
class PastSale:
    from_owner: str
    from_key: str
    when: date


@dataclass(frozen=True)
class PublicResult:
    result: str  # not_found | ok | mutation_pending | not_owner
    level: str  # green | amber | red
    message_bn: str
    message_en: str
    owners: list[str] = field(default_factory=list)
    mutation_done: bool | None = None
    sold_on: date | None = None  # only for not_owner, when the typed name sold this plot earlier
    previous_owners: list[dict[str, str]] = field(default_factory=list)


def decide(
    *,
    found: bool,
    owners: list[tuple[str, str]],  # (name, key) of the current registered owners
    mutation_complete: bool,
    sales: list[PastSale],
    name: str,
) -> PublicResult:
    """Pure decision, no database. The four outcomes of the Check Land page."""
    if not found:
        return PublicResult("not_found", "amber", "এই দাগ রেকর্ডে পাওয়া যায়নি", "This plot was not found in the record")

    names = [n for n, _ in owners]
    # Short history: who sold before, and when (latest sale per person, people still holding some land left out).
    current_keys = {k for _, k in owners}
    latest: dict[str, PastSale] = {}
    for s in sorted(sales, key=lambda s: s.when):
        if s.from_key not in current_keys:
            latest[s.from_key] = s
    previous = [{"name": s.from_owner, "date": s.when.isoformat()} for s in latest.values()]

    typed = key(name)
    if typed in current_keys:
        if mutation_complete:
            return PublicResult(
                "ok",
                "green",
                "এই নামেই আছে, বিক্রির যোগ্য",
                "Registered under this name, eligible for sale",
                names,
                True,
                None,
                previous,
            )
        return PublicResult(
            "mutation_pending",
            "amber",
            "রেজিস্ট্রেশন ও খতিয়ানের মালিক মিলছে না, নামজারি বাকি। আবার বিক্রি সন্দেহজনক।",
            "Registration and khatian owners differ: mutation is pending. A fresh sale is suspicious.",
            names,
            False,
            None,
            previous,
        )

    sold = latest.get(typed)
    return PublicResult(
        "not_owner",
        "red",
        f"এই নামে নেই। বর্তমান মালিক: {' ও '.join(names)}",
        f"Not registered under this name. Current owner: {', '.join(names)}",
        names,
        mutation_complete,
        sold.when if sold else None,
        previous,
    )


def check(db: Session, mouza: str, dag_no: str, name: str) -> dict[str, Any]:
    """Look the plot up, decide, and write a minimal audit entry (mouza + dag only, no personal data)."""
    mouza, dag = clean(mouza), key(dag_no)
    parcel = db.execute(
        select(m.RegParcel).where(m.RegParcel.mouza_key == key(mouza), m.RegParcel.dag_no == dag)
    ).scalar_one_or_none()
    owners: list[tuple[str, str]] = []
    sales: list[PastSale] = []
    done = False
    if parcel:
        holds = db.execute(select(m.RegHolding).where(m.RegHolding.parcel_id == parcel.id)).scalars()
        owners = [(h.owner, h.owner_key) for h in holds]
        events = db.execute(
            select(m.RegEvent).where(m.RegEvent.parcel_id == parcel.id, m.RegEvent.kind == "transfer")
        ).scalars()
        sales = [PastSale(e.from_owner or "", e.from_key or "", e.event_date) for e in events if e.from_key]
        done = khatian.mutation_done(db, parcel.id)
    r = decide(found=parcel is not None, owners=owners, mutation_complete=done, sales=sales, name=name)
    audit.append(db, "public_check", f"{mouza}/{dag}", {"mouza": mouza, "dag": dag, "result": r.result})
    db.commit()
    return {
        "result": r.result,
        "level": r.level,
        "message_bn": r.message_bn,
        "message_en": r.message_en,
        "registered_owners": r.owners,
        "mutation_done": r.mutation_done,
        "sold_on": r.sold_on.isoformat() if r.sold_on else None,
        "previous_owners": r.previous_owners,
    }


def mouzas(db: Session) -> list[str]:
    return list(db.execute(select(m.RegParcel.mouza).distinct().order_by(m.RegParcel.mouza)).scalars())
