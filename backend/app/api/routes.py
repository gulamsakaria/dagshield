"""REST endpoints (PRD section 12)."""

from __future__ import annotations

import time
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .. import evaluation
from ..db import audit, repo
from ..db import models as m
from ..integrity.qr import qr_png_base64, verify_url
from ..integrity.verify import verify_copy
from ..rules import REGISTRY, RuleParams, run_audit
from ..rules.common import ownership_summary
from ..rules.models import dec
from .schemas import ID_PATTERN, AlertPatch, AuditRequest, VerifyRequest
from .security import check_admin

router = APIRouter(prefix="/api")

SYNTHETIC_NOTICE = "Synthetic data only. Not real land records. Screening aid for human review."
IdPath = Annotated[str, Path(pattern=ID_PATTERN)]


def get_db(request: Request):
    with request.app.state.session_factory() as session:
        yield session


def rate_limited(request: Request) -> None:
    request.app.state.limiter.check(request)


Db = Annotated[Session, Depends(get_db)]


def _params(request: Request) -> RuleParams:
    s = request.app.state.settings
    return RuleParams(
        area_tolerance=dec(s.area_tolerance),
        lineage_confidence_min=dec(s.lineage_confidence_min),
        rapid_window_days=s.rapid_window_days,
        rapid_min_events=s.rapid_min_events,
        enable_r5=s.enable_r5,
    )


def alert_dict(a: m.Alert) -> dict[str, Any]:
    return {
        "id": a.id,
        "scenario_id": a.scenario_id,
        "parcel_id": a.parcel_id,
        "rule_id": a.rule_id,
        "rule_version": a.rule_version,
        "key": a.key,
        "severity": a.severity,
        "outcome": a.outcome,
        "status": a.status,
        "evidence_ids": a.evidence_ids,
        "calc": a.calc,
        "message_en": a.message_en,
        "message_bn": a.message_bn,
        "next_check_en": a.next_check_en,
        "next_check_bn": a.next_check_bn,
        "heuristic": a.heuristic,
        "created_at": a.created_at,
        "synthetic_notice": SYNTHETIC_NOTICE,
    }


@router.get("/health")
def health():
    return {"status": "ok", "synthetic_notice": SYNTHETIC_NOTICE}


@router.get("/rules")
def rules():
    return [{"rule_id": r.rule_id, "version": r.version, "title": r.title, "priority": r.priority} for r in REGISTRY]


@router.get("/scenarios")
def list_scenarios(db: Db):
    out = []
    for s in db.execute(select(m.Scenario).order_by(m.Scenario.position, m.Scenario.id)).scalars():
        counts = dict(
            db.execute(
                select(m.Alert.rule_id, func.count()).where(m.Alert.scenario_id == s.id).group_by(m.Alert.rule_id)
            ).all()
        )
        parcels = (
            db.execute(select(m.Parcel.id).where(m.Parcel.scenario_id == s.id).order_by(m.Parcel.id)).scalars().all()
        )
        out.append(
            {
                "id": s.id,
                "name": s.name,
                "name_bn": s.name_bn,
                "description": s.description,
                "description_bn": s.description_bn,
                "case_type": s.case_type,
                "parcel_ids": list(parcels),
                "alert_counts": counts,
                "alert_total": sum(counts.values()),
            }
        )
    return {"synthetic_notice": SYNTHETIC_NOTICE, "scenarios": out}


@router.post("/scenarios/{scenario_id}/reset", dependencies=[Depends(check_admin), Depends(rate_limited)])
def reset_scenario(scenario_id: IdPath, request: Request, db: Db):
    ok = repo.reset_scenario(db, request.app.state.fixtures, scenario_id, request.app.state.signer)
    if not ok:
        raise HTTPException(404, "Unknown scenario")
    db.commit()
    return {"scenario_id": scenario_id, "reset": True}


@router.get("/parcels")
def search_parcels(db: Db, query: Annotated[str, Query(min_length=1, max_length=64, pattern=r"^[\w.\-/ ]+$")]):
    q = query.strip()
    rows = (
        db.execute(
            select(m.Parcel)
            .where((func.lower(m.Parcel.id) == q.lower()) | (m.Parcel.dag_no == q))
            .order_by(m.Parcel.id)
        )
        .scalars()
        .all()
    )
    return {
        "query": q,
        "count": len(rows),
        "results": [
            {
                "id": p.id,
                "label": p.label,
                "dag_no": p.dag_no,
                "survey_type": p.survey_type,
                "area_decimal": p.area_decimal,
                "scenario_id": p.scenario_id,
            }
            for p in rows
        ],
    }


@router.get("/parcels/{parcel_id}/history")
def parcel_history(parcel_id: IdPath, request: Request, db: Db):
    parcel = db.get(m.Parcel, parcel_id)
    if parcel is None:
        raise HTTPException(404, "Parcel not found in supplied dataset")
    ds = repo.load_dataset(db, parcel.scenario_id)
    links = [x for x in ds.lineage if parcel_id in (x.parent_id, x.child_id)]

    def brief(pid: str):
        p = ds.parcel_by_id.get(pid)
        return {
            "id": pid,
            "dag_no": p.dag_no if p else None,
            "area": float(p.area) if p and p.area is not None else None,
        }

    lineage = [
        {
            "id": x.id,
            "relationship": x.relationship,
            "direction": "child" if x.parent_id == parcel_id else "parent",
            "parent": brief(x.parent_id),
            "child": brief(x.child_id),
            "confidence": None if x.confidence is None else float(x.confidence),
            "uncertain": x.confidence is None or x.confidence < dec(request.app.state.settings.lineage_confidence_min),
            "source_id": x.source_id,
        }
        for x in links
    ]

    def f(v):
        return None if v is None else float(v)

    timeline = []
    for d in ds.deeds:
        if d.parcel_id == parcel_id:
            timeline.append(
                {
                    "kind": "deed",
                    "order": 0,
                    "id": d.id,
                    "date": d.registration_date,
                    "status": d.status,
                    "summary": f"{d.seller} to {d.buyer}",
                    "details": {"seller": d.seller, "buyer": d.buyer, "area": f(d.area), "source_id": d.source_id},
                }
            )
    for t in ds.transfers_by_parcel.get(parcel_id, []):
        timeline.append(
            {
                "kind": "transfer",
                "order": 1,
                "id": t.id,
                "date": t.event_date,
                "status": t.status,
                "summary": f"{t.seller} to {t.buyer}, area {f(t.area)}",
                "details": {
                    "deed_id": t.deed_id,
                    "portion_key": t.portion_key,
                    "seller": t.seller,
                    "buyer": t.buyer,
                    "area": f(t.area),
                    "cancelled_on": t.cancelled_on.isoformat() if t.cancelled_on else None,
                },
            }
        )
    for x in ds.mutations:
        if x.parcel_id == parcel_id:
            timeline.append(
                {
                    "kind": "mutation",
                    "order": 2,
                    "id": x.id,
                    "date": x.date,
                    "status": x.status,
                    "summary": f"mutation to {x.recipient}, area {f(x.area)}",
                    "details": {
                        "transfer_id": x.transfer_id,
                        "recipient": x.recipient,
                        "area": f(x.area),
                        "source_id": x.source_id,
                    },
                }
            )
    timeline.sort(key=lambda e: (e["date"] is None, e["date"] or date.max, e["order"], e["id"]))
    for e in timeline:
        e["date"] = e["date"].isoformat() if e["date"] else None
        del e["order"]
    alerts = (
        db.execute(select(m.Alert).where(m.Alert.parcel_id == parcel_id).order_by(m.Alert.rule_id, m.Alert.key))
        .scalars()
        .all()
    )
    return {
        "synthetic_notice": SYNTHETIC_NOTICE,
        "parcel": {
            "id": parcel.id,
            "label": parcel.label,
            "survey_type": parcel.survey_type,
            "dag_no": parcel.dag_no,
            "area_decimal": parcel.area_decimal,
            "status": parcel.status,
            "scenario_id": parcel.scenario_id,
        },
        "lineage": lineage,
        "ownership_summary": ownership_summary(ds, parcel_id),
        "timeline": timeline,
        "alerts": [alert_dict(a) for a in alerts],
    }


@router.post("/audits", dependencies=[Depends(rate_limited)])
def run_audits(body: AuditRequest, request: Request, db: Db):
    started = time.perf_counter()
    scenario_id = body.scenario_id
    if body.parcel_id:
        parcel = db.get(m.Parcel, body.parcel_id)
        if parcel is None:
            raise HTTPException(404, "Parcel not found in supplied dataset")
        scenario_id = parcel.scenario_id
    scenarios = (
        [scenario_id]
        if scenario_id
        else [s for (s,) in db.execute(select(m.Scenario.id).order_by(m.Scenario.id)).all()]
    )
    if scenario_id and db.get(m.Scenario, scenario_id) is None:
        raise HTTPException(404, "Unknown scenario")
    params = _params(request)
    total = 0
    for sid in scenarios:
        findings = run_audit(repo.load_dataset(db, sid), params)
        if body.parcel_id:
            findings = [x for x in findings if x.parcel_id == body.parcel_id]
        stmt = select(m.Alert).where(m.Alert.scenario_id == sid)
        if body.parcel_id:
            stmt = stmt.where(m.Alert.parcel_id == body.parcel_id)
        old = {a.id: a.status for a in db.execute(stmt).scalars()}
        del_stmt = delete(m.Alert).where(m.Alert.scenario_id == sid)
        if body.parcel_id:
            del_stmt = del_stmt.where(m.Alert.parcel_id == body.parcel_id)
        db.execute(del_stmt)
        stamp = audit.now_iso()
        for fnd in findings:
            d = fnd.to_dict()
            db.add(
                m.Alert(
                    scenario_id=sid, status=old.get(d["id"], "New"), created_at=stamp, **{k: v for k, v in d.items()}
                )
            )
        total += len(findings)
    db.flush()
    audit.append(
        db,
        "audit_run",
        scenario_id or "all",
        {"scenarios": scenarios, "alerts": total, "rules": {r.rule_id: r.version for r in REGISTRY}},
    )
    db.commit()
    alerts = (
        db.execute(
            select(m.Alert)
            .where(m.Alert.scenario_id.in_(scenarios))
            .order_by(m.Alert.scenario_id, m.Alert.rule_id, m.Alert.key)
        )
        .scalars()
        .all()
    )
    return {
        "synthetic_notice": SYNTHETIC_NOTICE,
        "scenarios": scenarios,
        "alert_count": len(alerts),
        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
        "alerts": [alert_dict(a) for a in alerts],
    }


@router.get("/alerts")
def list_alerts(
    db: Db,
    parcel_id: Annotated[str | None, Query(pattern=ID_PATTERN)] = None,
    scenario_id: Annotated[str | None, Query(pattern=ID_PATTERN)] = None,
    rule_id: Annotated[str | None, Query(pattern=r"^R[1-5]$")] = None,
    status: Annotated[str | None, Query(pattern=r"^(New|Under Review|Closed)$")] = None,
):
    return {
        "synthetic_notice": SYNTHETIC_NOTICE,
        "alerts": [alert_dict(a) for a in _query_alerts(db, parcel_id, scenario_id, rule_id, status)],
    }


def _query_alerts(db: Session, parcel_id, scenario_id, rule_id, status):
    stmt = select(m.Alert).order_by(m.Alert.scenario_id, m.Alert.rule_id, m.Alert.key)
    for col, val in (
        (m.Alert.parcel_id, parcel_id),
        (m.Alert.scenario_id, scenario_id),
        (m.Alert.rule_id, rule_id),
        (m.Alert.status, status),
    ):
        if val:
            stmt = stmt.where(col == val)
    return db.execute(stmt).scalars().all()


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: IdPath, db: Db):
    a = db.get(m.Alert, alert_id)
    if a is None:
        raise HTTPException(404, "Alert not found")
    return alert_dict(a)


@router.patch("/alerts/{alert_id}", dependencies=[Depends(check_admin), Depends(rate_limited)])
def patch_alert(alert_id: IdPath, body: AlertPatch, db: Db):
    a = db.get(m.Alert, alert_id)
    if a is None:
        raise HTTPException(404, "Alert not found")
    a.status = body.status
    audit.append(db, "alert_status_changed", a.id, {"alert": a.id, "status": body.status})
    db.commit()
    return alert_dict(a)


@router.get("/evaluation")
def get_evaluation(request: Request):
    return evaluation.evaluate(request.app.state.fixtures, _params(request), request.app.state.signer)


def _deed_or_404(db: Session, deed_id: str) -> m.Deed:
    d = db.get(m.Deed, deed_id)
    if d is None:
        raise HTTPException(404, "Deed not found in supplied dataset")
    return d


@router.get("/deeds")
def list_deeds(db: Db, parcel_id: Annotated[str | None, Query(pattern=ID_PATTERN)] = None):
    stmt = select(m.Deed).order_by(m.Deed.id)
    if parcel_id:
        stmt = stmt.where(m.Deed.parcel_id == parcel_id)
    return {
        "deeds": [{"deed_ref": d.id, "parcel_id": d.parcel_id, "status": d.status} for d in db.execute(stmt).scalars()]
    }


@router.get("/deeds/{deed_id}")
def get_deed(deed_id: IdPath, db: Db):
    d = _deed_or_404(db, deed_id)
    rec = repo.deed_record_dict(d)
    return {"synthetic_notice": SYNTHETIC_NOTICE, "fields": rec, "record_hash": d.record_hash}


@router.get("/deeds/{deed_id}/qr")
def deed_qr(deed_id: IdPath, request: Request, db: Db):
    d = _deed_or_404(db, deed_id)
    url = verify_url(request.app.state.settings.public_base_url, d.id, d.record_hash or "", d.signature or "")
    return {
        "deed_ref": d.id,
        "hash": d.record_hash,
        "signature": d.signature,
        "verify_url": url,
        "public_key": request.app.state.signer.public_key_b64url,
        "png_base64": qr_png_base64(url),
        "synthetic_notice": SYNTHETIC_NOTICE,
    }


@router.post("/verify", dependencies=[Depends(rate_limited)])
def verify(body: VerifyRequest, request: Request, db: Db):
    d = db.get(m.Deed, body.deed_ref)
    stored = None
    if d is not None and d.record_hash and d.signature:
        stored = {"record": repo.deed_record_dict(d), "hash": d.record_hash, "signature": d.signature}
    result = verify_copy(request.app.state.signer, stored, body.fields.model_dump(), body.hash, body.signature)
    audit.append(
        db,
        "deed_verified",
        body.deed_ref,
        {"deed_ref": body.deed_ref, "result": result["result"], "recomputed_hash": result["recomputed_hash"]},
    )
    db.commit()
    result["deed_ref"] = body.deed_ref
    result["synthetic_notice"] = SYNTHETIC_NOTICE
    return result


@router.get("/audit-log/verify")
def audit_log_verify(db: Db):
    r = audit.verify(db)
    return {
        "ok": r.ok,
        "entries_checked": r.checked,
        "head_hash": r.head_hash,
        "broken_at": r.broken_at,
        "reason": r.reason,
        "note": "Record head_hash outside the database to also detect truncation.",
    }


@router.get("/audit-log")
def audit_log(db: Db, limit: Annotated[int, Query(ge=1, le=200)] = 50):
    rows = audit.entries(db)
    return {"total": len(rows), "entries": rows[-limit:][::-1]}
