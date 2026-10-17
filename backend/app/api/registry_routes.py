"""Officer-portal endpoints: login, dashboard numbers, new registration, plot history, alerts."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..db import models as m
from ..registry import khatian, sample, service
from ..registry.auth import (
    JUDGE_NAME_BN,
    JUDGE_NAME_EN,
    JUDGE_USERNAME,
    OFFICER_NAME_BN,
    OFFICER_NAME_EN,
    bearer,
    current_officer,
)
from ..registry.checker import clean, key, parse_area
from .routes import SYNTHETIC_NOTICE, Db, rate_limited

router = APIRouter(prefix="/api")
Officer = Annotated[str, Depends(current_officer)]

NAME = Field(min_length=2, max_length=120)


class LoginBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class PlotBody(BaseModel):
    """A plot the officer adds to the registry (names may be Bangla or English)."""

    model_config = ConfigDict(extra="forbid")
    mouza: str = NAME
    dag_no: str = Field(min_length=1, max_length=32, pattern=r"^[0-9০-৯A-Za-z\-/]+$")
    owner: str = NAME
    area: str = Field(min_length=1, max_length=32)

    @field_validator("area")
    @classmethod
    def _area(cls, v: str) -> str:
        parse_area(v)
        return v


class RegistrationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mouza: str = NAME
    dag_no: str = Field(min_length=1, max_length=32, pattern=r"^[0-9০-৯A-Za-z\-/]+$")
    seller: str = NAME
    buyer: str = NAME
    area: str = Field(min_length=1, max_length=32)
    deed_date: date

    @field_validator("area")
    @classmethod
    def _area(cls, v: str) -> str:
        parse_area(v)
        return v

    @field_validator("deed_date")
    @classmethod
    def _not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("deed date cannot be in the future")
        return v

    @model_validator(mode="after")
    def _different_people(self) -> RegistrationBody:
        if key(self.seller) == key(self.buyer):
            raise ValueError("seller and buyer must be different people")
        return self


@router.post("/auth/login")
def login(body: LoginBody, request: Request):
    request.app.state.login_limiter.check(request)
    token = request.app.state.officer_auth.login(body.username, body.password)
    if token is None:
        raise HTTPException(401, "Incorrect username or password.")
    return {
        "token": token,
        "officer": {"username": body.username, "name_en": OFFICER_NAME_EN, "name_bn": OFFICER_NAME_BN},
        "synthetic_notice": SYNTHETIC_NOTICE,
    }


@router.post("/auth/logout")
def logout(request: Request, _: Officer):
    request.app.state.officer_auth.logout(bearer(request))
    return {"ok": True}


def _who(username: str) -> dict[str, str]:
    if username == JUDGE_USERNAME:
        return {"username": username, "name_en": JUDGE_NAME_EN, "name_bn": JUDGE_NAME_BN}
    return {"username": username, "name_en": OFFICER_NAME_EN, "name_bn": OFFICER_NAME_BN}


@router.post("/auth/judge")
def judge_login(request: Request):
    """One-click demo access for judges, no password. Off unless DAGSHIELD_JUDGE_LOGIN=true."""
    if not request.app.state.settings.judge_login:
        raise HTTPException(404, "Not found")
    request.app.state.login_limiter.check(request)
    return {
        "token": request.app.state.officer_auth.judge_token(),
        "officer": _who(JUDGE_USERNAME),
        "synthetic_notice": SYNTHETIC_NOTICE,
    }


@router.get("/auth/me")
def me(officer: Officer):
    return _who(officer)


@router.post("/registry/sample-data", dependencies=[Depends(rate_limited)])
def load_sample_data(request: Request, db: Db, officer: Officer):
    """Add the sample plots and past requests that make the demo look lived-in. Safe to call twice."""
    return sample.load(db, officer, request.app.state.settings.rapid_window_days)


@router.get("/registry/summary")
def summary(db: Db, _: Officer):
    return {"synthetic_notice": SYNTHETIC_NOTICE, **service.summary(db)}


@router.get("/registry/plots")
def plots(db: Db, _: Officer):
    return {"mouzas": service.mouzas(db), "plots": service.plots(db)}


@router.post("/registry/registrations", dependencies=[Depends(rate_limited)])
def register(body: RegistrationBody, request: Request, db: Db, officer: Officer):
    attempt = service.register(
        db,
        officer=officer,
        mouza=body.mouza,
        dag_no=body.dag_no,
        seller=body.seller,
        buyer=body.buyer,
        area=parse_area(body.area),
        deed_date=body.deed_date,
        rapid_window_days=request.app.state.settings.rapid_window_days,
    )
    return service.attempt_dict(attempt)


@router.get("/registry/attempts")
def attempts(
    db: Db,
    _: Officer,
    verdict: Annotated[list[Literal["success", "warning", "blocked"]] | None, Query()] = None,
):
    return {"synthetic_notice": SYNTHETIC_NOTICE, "attempts": service.list_attempts(db, verdict)}


@router.get("/registry/attempts/{attempt_id}")
def attempt(attempt_id: int, db: Db, _: Officer):
    a = db.get(m.RegAttempt, attempt_id)
    if a is None:
        raise HTTPException(404, "Attempt not found")
    return service.attempt_dict(a)


@router.get("/registry/history")
def history(
    db: Db,
    _: Officer,
    mouza: Annotated[str, Query(min_length=1, max_length=120)],
    dag_no: Annotated[str, Query(min_length=1, max_length=32)],
):
    parcel = service.find_parcel(db, clean(mouza), dag_no)
    if parcel is None:
        raise HTTPException(404, "Plot not found in supplied dataset")
    return {"synthetic_notice": SYNTHETIC_NOTICE, **service.history(db, parcel)}


@router.post("/registry/reset", dependencies=[Depends(rate_limited)])
def reset(db: Db, _: Officer):
    service.reset(db)
    return {"reset": True}


@router.post("/registry/mutations/complete")
def complete_mutation(
    db: Db,
    _: Officer,
    mouza: Annotated[str, Query(min_length=1, max_length=120)],
    dag_no: Annotated[str, Query(min_length=1, max_length=32)],
):
    """Mark the namjari done: the khatian now names the same owners as the registration record."""
    parcel = service.find_parcel(db, clean(mouza), dag_no)
    if parcel is None:
        raise HTTPException(404, "Plot not found in supplied dataset")
    khatian.complete_mutation(db, parcel.id)
    db.commit()
    return {"mutation_done": True}


@router.post("/registry/plots", status_code=201, dependencies=[Depends(rate_limited)])
def add_plot(body: PlotBody, db: Db, officer: Officer):
    try:
        parcel = service.add_plot(
            db, officer=officer, mouza=body.mouza, dag_no=body.dag_no, owner=body.owner, area=parse_area(body.area)
        )
    except service.PlotExistsError:
        raise HTTPException(409, "This plot is already in the registry.") from None
    return {"id": parcel.id, "mouza": parcel.mouza, "dag_no": parcel.dag_no, "total_area": parcel.total_area}
