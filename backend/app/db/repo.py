"""Loading fixtures into the database, reading datasets back, signing deeds."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..integrity.canonical import make_record, record_hash
from ..integrity.signing import Signer
from ..privacy import scan_fixture
from ..rules.models import Dataset, dec
from . import audit
from . import models as m

SCENARIO_TABLES = (
    m.Alert,
    m.MutationRecord,
    m.TransferEvent,
    m.Deed,
    m.OwnershipEntitlement,
    m.ParcelLineage,
    m.Parcel,
    m.SourceRecord,
)


def load_fixture_files(directory: Path) -> list[dict[str, Any]]:
    files = sorted(directory.glob("*.json"))
    if not files:
        raise RuntimeError(f"no scenario fixtures found in {directory}")
    fixtures = []
    for position, f in enumerate(files):
        data = json.loads(f.read_text(encoding="utf-8"))
        problems = scan_fixture(data)
        if problems:
            raise ValueError(f"{f.name} failed the synthetic-data guard: {problems[:3]}")
        Dataset.from_dict(data)  # validates types, dates and statuses
        data["position"] = position
        fixtures.append(data)
    return fixtures


def deed_record_dict(d: m.Deed) -> dict[str, str | None]:
    return make_record(d.id, d.registration_date, d.status, d.seller, d.buyer, d.parcel_id, d.area_decimal, d.source_id)


def insert_scenario(db: Session, fx: dict[str, Any], signer: Signer) -> None:
    sid = fx["scenario_id"]
    db.merge(
        m.Scenario(
            id=sid,
            name=fx["name"],
            name_bn=fx.get("name_bn", ""),
            description=fx.get("description", ""),
            description_bn=fx.get("description_bn", ""),
            case_type=fx.get("case_type", ""),
        )
    )
    for s in fx.get("source_records", []):
        db.add(m.SourceRecord(scenario_id=sid, **s))
    for p in fx.get("parcels", []):
        db.add(m.Parcel(scenario_id=sid, **p))
    for x in fx.get("lineage", []):
        db.add(m.ParcelLineage(scenario_id=sid, **x))
    for e in fx.get("entitlements", []):
        e = dict(e)
        e["effective_date"] = ds_date(e.get("effective_date"))
        db.add(m.OwnershipEntitlement(scenario_id=sid, **e))
    db.flush()
    for d in fx.get("deeds", []):
        d = dict(d)
        d["registration_date"] = ds_date(d.get("registration_date"))
        row = m.Deed(scenario_id=sid, **d)
        rec = deed_record_dict(row)
        row.record_hash = record_hash(rec)
        row.signature = signer.sign(row.record_hash)
        db.add(row)
        audit.append(db, "deed_signed", row.id, {"deed_ref": row.id, "record_hash": row.record_hash})
    for t in fx.get("transfers", []):
        t = dict(t)
        t["event_date"] = ds_date(t.get("event_date"))
        t["cancelled_on"] = ds_date(t.get("cancelled_on"))
        db.add(m.TransferEvent(scenario_id=sid, **t))
    for x in fx.get("mutations", []):
        x = dict(x)
        x["date"] = ds_date(x.get("date"))
        db.add(m.MutationRecord(scenario_id=sid, **x))
    db.flush()


def ds_date(value: Any):
    from ..rules.models import to_date

    return to_date(value)


def clear_scenario(db: Session, scenario_id: str) -> None:
    for table in SCENARIO_TABLES:
        db.execute(delete(table).where(table.scenario_id == scenario_id))
    db.flush()


def reset_scenario(db: Session, fixtures: list[dict[str, Any]], scenario_id: str, signer: Signer) -> bool:
    fx = next((f for f in fixtures if f["scenario_id"] == scenario_id), None)
    if fx is None:
        return False
    clear_scenario(db, scenario_id)
    insert_scenario(db, fx, signer)
    audit.append(db, "scenario_reset", scenario_id, {"scenario_id": scenario_id})
    return True


def ensure_seeded(db: Session, fixtures: list[dict[str, Any]], signer: Signer) -> str:
    """Seed an empty database; re-seed if stored signatures do not verify under the current key."""
    has_data = db.execute(select(m.Scenario.id).limit(1)).first() is not None
    if has_data:
        deeds = db.execute(select(m.Deed)).scalars().all()
        if all(d.record_hash and signer.verify(d.record_hash, d.signature) for d in deeds):
            known = {s for (s,) in db.execute(select(m.Scenario.id)).all()}
            missing = [f for f in fixtures if f["scenario_id"] not in known]
            for fx in missing:
                insert_scenario(db, fx, signer)
            db.commit()
            return "kept"
        for fx in fixtures:
            clear_scenario(db, fx["scenario_id"])
            insert_scenario(db, fx, signer)
        audit.append(db, "reseed_after_key_change", "all", {"scenarios": len(fixtures)})
        db.commit()
        return "reseeded"
    for fx in fixtures:
        insert_scenario(db, fx, signer)
    audit.append(db, "seed_all", "all", {"scenarios": len(fixtures)})
    db.commit()
    return "seeded"


def load_dataset(db: Session, scenario_id: str | None = None) -> Dataset:
    def q(model):
        stmt = select(model)
        if scenario_id is not None:
            stmt = stmt.where(model.scenario_id == scenario_id)
        return db.execute(stmt).scalars().all()

    from ..rules import models as r

    return Dataset(
        parcels=[r.Parcel(p.id, p.label, p.survey_type, p.dag_no, dec(p.area_decimal), p.status) for p in q(m.Parcel)],
        lineage=[
            r.Lineage(x.id, x.parent_id, x.child_id, x.relationship, dec(x.confidence), x.source_id)
            for x in q(m.ParcelLineage)
        ],
        entitlements=[
            r.Entitlement(
                e.id, e.parcel_id, e.owner, dec(e.opening_area), e.effective_date, e.source_id, dec(e.confidence)
            )
            for e in q(m.OwnershipEntitlement)
        ],
        deeds=[
            r.Deed(
                d.id, d.parcel_id, d.registration_date, d.status, d.seller, d.buyer, dec(d.area_decimal), d.source_id
            )
            for d in q(m.Deed)
        ],
        transfers=[
            r.Transfer(
                t.id,
                t.deed_id,
                t.parcel_id,
                t.portion_key,
                t.seller,
                t.buyer,
                dec(t.area),
                t.event_date,
                t.status,
                t.cancelled_on,
            )
            for t in q(m.TransferEvent)
        ],
        mutations=[
            r.Mutation(x.id, x.transfer_id, x.parcel_id, x.date, x.status, dec(x.area), x.recipient, x.source_id)
            for x in q(m.MutationRecord)
        ],
    )
