"""Khatian (land record) side of the demo registry, used by the public "Check Land" page.

Two different records name an owner for a plot:
  * the REGISTRATION record (RegHolding): updated the moment an officer registers a deed;
  * the KHATIAN (RegKhatian): updated only when the mutation (namjari) is completed.
While they differ, the mutation is pending ("নামজারি বাকি").
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..db import models as m
from .checker import key


def _holdings(db: Session, parcel_id: int) -> list[m.RegHolding]:
    return list(db.execute(select(m.RegHolding).where(m.RegHolding.parcel_id == parcel_id)).scalars())


def khatian_keys(db: Session, parcel_id: int) -> set[str]:
    return set(db.execute(select(m.RegKhatian.owner_key).where(m.RegKhatian.parcel_id == parcel_id)).scalars())


def mutation_done(db: Session, parcel_id: int) -> bool:
    """True when the khatian names exactly the same owners as the registration record."""
    return khatian_keys(db, parcel_id) == {h.owner_key for h in _holdings(db, parcel_id)}


def complete_mutation(db: Session, parcel_id: int) -> None:
    """Officer finishes the namjari: the khatian now copies the registered owners."""
    db.execute(delete(m.RegKhatian).where(m.RegKhatian.parcel_id == parcel_id))
    for h in _holdings(db, parcel_id):
        db.add(m.RegKhatian(parcel_id=parcel_id, owner=h.owner, owner_key=h.owner_key))
    db.flush()


def ensure_demo_plots(db: Session) -> bool:
    """Idempotent. Adds one plot whose mutation is still pending, and gives every other plot a khatian
    that matches its current owners (mutation done). Returns True if it changed anything."""
    changed = False
    mouza, dag = "নমুনা মৌজা-২", "202"
    exists = db.execute(
        select(m.RegParcel.id).where(m.RegParcel.mouza_key == key(mouza), m.RegParcel.dag_no == dag)
    ).first()
    if exists is None:
        # Abdus Salam sold to Nazma Khatun recently; the deed is registered but the khatian still names him.
        parcel = m.RegParcel(mouza=mouza, mouza_key=key(mouza), dag_no=dag, total_area=12.0)
        db.add(parcel)
        db.flush()
        seller, buyer = "আব্দুস সালাম", "নাজমা খাতুন"
        sale_day = date.today() - timedelta(days=20)
        db.add(m.RegHolding(parcel_id=parcel.id, owner=buyer, owner_key=key(buyer), area=12.0))
        db.add(m.RegKhatian(parcel_id=parcel.id, owner=seller, owner_key=key(seller)))
        db.add(m.RegEvent(parcel_id=parcel.id, kind="initial", event_date=date(2012, 5, 9), to_owner=seller, area=12.0))
        db.add(
            m.RegEvent(
                parcel_id=parcel.id,
                kind="transfer",
                event_date=sale_day,
                from_owner=seller,
                from_key=key(seller),
                to_owner=buyer,
                area=12.0,
            )
        )
        changed = True
    db.flush()
    for (pid,) in db.execute(select(m.RegParcel.id)).all():
        if not khatian_keys(db, pid):
            for h in _holdings(db, pid):
                db.add(m.RegKhatian(parcel_id=pid, owner=h.owner, owner_key=h.owner_key))
            changed = True
    return changed
