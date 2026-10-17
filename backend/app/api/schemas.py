"""Request models. Strict patterns and length limits on every input."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ID_PATTERN = r"^[A-Za-z0-9._:\-]{1,64}$"
HASH_PATTERN = r"^[0-9a-f]{64}$"
SIG_PATTERN = r"^[A-Za-z0-9_\-]{20,128}$"


class AuditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: str | None = Field(default=None, pattern=ID_PATTERN)
    parcel_id: str | None = Field(default=None, pattern=ID_PATTERN)


class AlertPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["New", "Under Review", "Closed"]


class DeedFields(BaseModel):
    """The fields printed on a deed copy. All eight must be present."""

    model_config = ConfigDict(extra="forbid")
    deed_ref: str | None = Field(max_length=64)
    registration_date: str | None = Field(max_length=32)
    registration_status: str | None = Field(max_length=32)
    seller: str | None = Field(max_length=64)
    buyer: str | None = Field(max_length=64)
    parcel_id: str | None = Field(max_length=64)
    area_decimal: str | None = Field(max_length=32)
    source_id: str | None = Field(max_length=64)


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deed_ref: str = Field(pattern=ID_PATTERN)
    fields: DeedFields
    hash: str | None = Field(default=None, pattern=HASH_PATTERN)
    signature: str | None = Field(default=None, pattern=SIG_PATTERN)
