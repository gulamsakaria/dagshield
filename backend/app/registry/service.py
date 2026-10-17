"""Database side of the officer-portal demo registry."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..db import audit
from ..db import models as m
from . import khatian
from .checker import ASCII_TO_BN, Holding, PastTransfer, Verdict, check, clean, key

# Hand-entered synthetic records. The names are made up.
SEED = [
    ("নমুনা মৌজা-১", "123", "রহিম উদ্দিন", Decimal("10"), date(2016, 3, 14)),
    ("নমুনা মৌজা-১", "124", "সালমা বেগম", Decimal("15"), date(2014, 8, 2)),
    ("নমুনা মৌজা-২", "201", "জামাল হোসেন", Decimal("20"), date(2018, 11, 21)),
]


def seed_if_empty(db: Session) -> bool:
    """Seed the three hand-entered plots on an empty registry, then make sure the khatian side exists
    (a fourth plot with a pending mutation, and a matching khatian for every other plot)."""
    changed = False
    if db.execute(select(m.RegParcel.id).limit(1)).first() is None:
        for mouza, dag, owner, area, since in SEED:
            parcel = m.RegParcel(mouza=mouza, mouza_key=key(mouza), dag_no=dag, total_area=float(area))
            db.add(parcel)
            db.flush()
            db.add(m.RegHolding(parcel_id=parcel.id, owner=owner, owner_key=key(owner), area=float(area)))
            db.add(m.RegEvent(parcel_id=parcel.id, kind="initial", event_date=since, to_owner=owner, area=float(area)))
        changed = True
    changed = khatian.ensure_demo_plots(db) or changed
    db.commit()
    return changed


class PlotExistsError(Exception):
    """The same mouza and dag number is already in the registry."""


def add_plot(
    db: Session, *, officer: str, mouza: str, dag_no: str, owner: str, area: Decimal, since: date | None = None
) -> m.RegParcel:
    """Officer adds a plot that is not in the registry yet. It starts with one owner and a finished mutation."""
    mouza, dag_no, owner = clean(mouza), key(dag_no), clean(owner)
    if find_parcel(db, mouza, dag_no) is not None:
        raise PlotExistsError
    parcel = m.RegParcel(mouza=mouza, mouza_key=key(mouza), dag_no=dag_no, total_area=float(area))
    db.add(parcel)
    db.flush()
    db.add(m.RegHolding(parcel_id=parcel.id, owner=owner, owner_key=key(owner), area=float(area)))
    db.add(m.RegKhatian(parcel_id=parcel.id, owner=owner, owner_key=key(owner)))
    db.add(
        m.RegEvent(
            parcel_id=parcel.id, kind="initial", event_date=since or date.today(), to_owner=owner, area=float(area)
        )
    )
    audit.append(db, "plot_added", f"{mouza}/{dag_no}", {"plot": f"{mouza}/{dag_no}", "officer": officer})
    db.commit()
    return parcel


def reset(db: Session) -> None:
    for table in (m.RegAttempt, m.RegEvent, m.RegHolding, m.RegKhatian, m.RegParcel):
        db.execute(delete(table))
    db.flush()
    seed_if_empty(db)
    audit.append(db, "registry_reset", "registry", {"parcels": len(SEED)})
    db.commit()


def _holdings(db: Session, parcel_id: int) -> list[m.RegHolding]:
    return list(
        db.execute(select(m.RegHolding).where(m.RegHolding.parcel_id == parcel_id).order_by(m.RegHolding.id))
        .scalars()
        .all()
    )


def find_parcel(db: Session, mouza: str, dag_no: str, lock: bool = False) -> m.RegParcel | None:
    stmt = select(m.RegParcel).where(m.RegParcel.mouza_key == key(mouza), m.RegParcel.dag_no == key(dag_no))
    if lock:
        stmt = stmt.with_for_update()
    return db.execute(stmt).scalar_one_or_none()


def register(
    db: Session,
    *,
    officer: str,
    mouza: str,
    dag_no: str,
    seller: str,
    buyer: str,
    area: Decimal,
    deed_date: date,
    rapid_window_days: int,
) -> m.RegAttempt:
    """Check the request, record the attempt, and move ownership unless it is blocked."""
    mouza, dag_no, seller, buyer = clean(mouza), key(dag_no), clean(seller), clean(buyer)
    parcel = find_parcel(db, mouza, dag_no, lock=True)
    holds = [Holding(h.owner, h.owner_key, Decimal(str(h.area))) for h in _holdings(db, parcel.id)] if parcel else []
    past: list[PastTransfer] = []
    if parcel:
        for e in db.execute(select(m.RegEvent).where(m.RegEvent.parcel_id == parcel.id)).scalars():
            if e.kind == "transfer":
                past.append(PastTransfer(e.from_key, e.to_owner, e.event_date))
    result: Verdict = check(
        parcel_found=parcel is not None,
        holdings=holds,
        transfers=past,
        seller=seller,
        buyer=buyer,
        area=area,
        deed_date=deed_date,
        rapid_window_days=rapid_window_days,
    )
    attempt = m.RegAttempt(
        created_at=audit.now_iso(),
        officer=officer,
        parcel_id=parcel.id if parcel else None,
        mouza=mouza,
        dag_no=dag_no,
        seller=seller,
        buyer=buyer,
        area=float(area),
        deed_date=deed_date,
        verdict=result.verdict,
        rule_id=result.rule_id,
        reason_en=result.reason_en,
        reason_bn=result.reason_bn.translate(ASCII_TO_BN),
        calc=result.calc,
    )
    db.add(attempt)
    db.flush()
    if parcel and result.verdict in ("success", "warning"):
        _move_ownership(db, parcel, seller, buyer, area, deed_date, attempt.id, flagged=result.verdict == "warning")
    audit.append(
        db,
        "registration_checked",
        f"attempt-{attempt.id}",
        {
            "attempt": attempt.id,
            "plot": f"{mouza}/{dag_no}",
            "verdict": result.verdict,
            "rule": result.rule_id,
            "officer": officer,
        },
    )
    db.commit()
    return attempt


def _move_ownership(
    db: Session, parcel: m.RegParcel, seller: str, buyer: str, area: Decimal, when: date, attempt_id: int, flagged: bool
) -> None:
    rows = _holdings(db, parcel.id)
    src = next(h for h in rows if h.owner_key == key(seller))
    remaining = Decimal(str(src.area)) - area
    if remaining <= Decimal("0.00005"):
        db.delete(src)
    else:
        src.area = float(remaining)
    dst = next((h for h in rows if h.owner_key == key(buyer)), None)
    if dst:
        dst.area = float(Decimal(str(dst.area)) + area)
    else:
        db.add(m.RegHolding(parcel_id=parcel.id, owner=buyer, owner_key=key(buyer), area=float(area)))
    db.add(
        m.RegEvent(
            parcel_id=parcel.id,
            kind="transfer",
            event_date=when,
            from_owner=src.owner,
            from_key=src.owner_key,
            to_owner=buyer,
            area=float(area),
            attempt_id=attempt_id,
            flagged=flagged,
        )
    )


def attempt_dict(a: m.RegAttempt) -> dict[str, Any]:
    return {
        "id": a.id,
        "created_at": a.created_at,
        "officer": a.officer,
        "parcel_id": a.parcel_id,
        "mouza": a.mouza,
        "dag_no": a.dag_no,
        "seller": a.seller,
        "buyer": a.buyer,
        "area": a.area,
        "deed_date": a.deed_date.isoformat(),
        "verdict": a.verdict,
        "rule_id": a.rule_id,
        "reason_en": a.reason_en,
        "reason_bn": a.reason_bn,
        "calc": a.calc,
    }


def summary(db: Session) -> dict[str, int]:
    counts = dict(db.execute(select(m.RegAttempt.verdict, func.count()).group_by(m.RegAttempt.verdict)).all())
    return {
        "total": sum(counts.values()),
        "success": counts.get("success", 0),
        "warning": counts.get("warning", 0),
        "blocked": counts.get("blocked", 0),
        "parcels": db.execute(select(func.count()).select_from(m.RegParcel)).scalar_one(),
    }


def list_attempts(db: Session, verdicts: list[str] | None = None, limit: int = 200) -> list[dict[str, Any]]:
    stmt = select(m.RegAttempt).order_by(m.RegAttempt.id.desc()).limit(limit)
    if verdicts:
        stmt = stmt.where(m.RegAttempt.verdict.in_(verdicts))
    return [attempt_dict(a) for a in db.execute(stmt).scalars()]


def mouzas(db: Session) -> list[str]:
    return list(db.execute(select(m.RegParcel.mouza).distinct().order_by(m.RegParcel.mouza)).scalars())


def plots(db: Session) -> list[dict[str, Any]]:
    out = []
    for p in db.execute(select(m.RegParcel).order_by(m.RegParcel.mouza, m.RegParcel.id)).scalars():
        owners = [h.owner for h in _holdings(db, p.id)]
        out.append({"id": p.id, "mouza": p.mouza, "dag_no": p.dag_no, "total_area": p.total_area, "owners": owners})
    return out


def history(db: Session, parcel: m.RegParcel) -> dict[str, Any]:
    events = db.execute(
        select(m.RegEvent).where(m.RegEvent.parcel_id == parcel.id).order_by(m.RegEvent.event_date, m.RegEvent.id)
    ).scalars()
    timeline: list[dict[str, Any]] = [
        {
            "kind": e.kind,
            "date": e.event_date.isoformat(),
            "from": e.from_owner,
            "to": e.to_owner,
            "area": e.area,
            "flagged": e.flagged,
            "attempt_id": e.attempt_id,
            "sort": (e.event_date.isoformat(), 0, e.id),
        }
        for e in events
    ]
    blocked = db.execute(
        select(m.RegAttempt).where(m.RegAttempt.parcel_id == parcel.id, m.RegAttempt.verdict == "blocked")
    ).scalars()
    for a in blocked:
        timeline.append(
            {
                "kind": "blocked",
                "date": a.created_at[:10],
                "from": a.seller,
                "to": a.buyer,
                "area": a.area,
                "flagged": True,
                "attempt_id": a.id,
                "rule_id": a.rule_id,
                "reason_en": a.reason_en,
                "reason_bn": a.reason_bn,
                "sort": (a.created_at, 1, a.id),
            }
        )
    timeline.sort(key=lambda e: e["sort"])
    for e in timeline:
        del e["sort"]
    return {
        "parcel": {"id": parcel.id, "mouza": parcel.mouza, "dag_no": parcel.dag_no, "total_area": parcel.total_area},
        "owners": [{"owner": h.owner, "area": h.area} for h in _holdings(db, parcel.id)],
        "timeline": timeline,
    }
