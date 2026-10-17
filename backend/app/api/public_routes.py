"""Public endpoints (no login) for the "Check Land" page. Read-only apart from one audit-log line per check."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from ..registry import public
from .routes import SYNTHETIC_NOTICE, Db

router = APIRouter(prefix="/api/public")


class PublicCheckBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mouza: str = Field(min_length=1, max_length=120)
    dag_no: str = Field(min_length=1, max_length=32, pattern=r"^[0-9০-৯A-Za-z\-/]+$")
    owner_name: str = Field(min_length=2, max_length=120)


@router.get("/config")
def config(request: Request):
    """What the web UI may offer: today only whether the one-click judge demo is switched on."""
    return {"judge_login": request.app.state.settings.judge_login}


@router.get("/mouzas")
def mouzas(db: Db):
    return {"mouzas": public.mouzas(db)}


@router.post("/check")
def check_land(body: PublicCheckBody, request: Request, db: Db):
    request.app.state.public_limiter.check(request)  # bulk-lookup guard, per client address
    return {"synthetic_notice": SYNTHETIC_NOTICE, **public.check(db, body.mouza, body.dag_no, body.owner_name)}
