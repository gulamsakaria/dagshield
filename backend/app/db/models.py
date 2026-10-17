"""SQLAlchemy tables (PRD section 8). All identities are synthetic tokens."""

from __future__ import annotations

from datetime import date

from sqlalchemy import JSON, Boolean, Date, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    name_bn: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    description_bn: Mapped[str] = mapped_column(Text, default="")
    case_type: Mapped[str] = mapped_column(String(32), default="")
    position: Mapped[int] = mapped_column(Integer, default=0)


class SourceRecord(Base):
    __tablename__ = "source_records"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(200))
    data_version: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str] = mapped_column(Text, default="")


class Parcel(Base):
    __tablename__ = "parcels"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(200))
    survey_type: Mapped[str] = mapped_column(String(8))
    dag_no: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    area_decimal: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")


class ParcelLineage(Base):
    __tablename__ = "parcel_lineage"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    parent_id: Mapped[str] = mapped_column(String(64))
    child_id: Mapped[str] = mapped_column(String(64))
    relationship: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class OwnershipEntitlement(Base):
    __tablename__ = "ownership_entitlements"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    parcel_id: Mapped[str] = mapped_column(String(64))
    owner: Mapped[str] = mapped_column(String(32))
    opening_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)


class Deed(Base):
    __tablename__ = "deeds"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # deed reference
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    parcel_id: Mapped[str] = mapped_column(String(64), index=True)
    registration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    seller: Mapped[str] = mapped_column(String(32))
    buyer: Mapped[str] = mapped_column(String(32))
    area_decimal: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    record_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signature: Mapped[str | None] = mapped_column(String(128), nullable=True)


class TransferEvent(Base):
    __tablename__ = "transfer_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    deed_id: Mapped[str] = mapped_column(String(64))
    parcel_id: Mapped[str] = mapped_column(String(64), index=True)
    portion_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    seller: Mapped[str] = mapped_column(String(32))
    buyer: Mapped[str] = mapped_column(String(32))
    area: Mapped[float | None] = mapped_column(Float, nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    cancelled_on: Mapped[date | None] = mapped_column(Date, nullable=True)


class MutationRecord(Base):
    __tablename__ = "mutation_records"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    transfer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parcel_id: Mapped[str] = mapped_column(String(64), index=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(16))
    area: Mapped[float | None] = mapped_column(Float, nullable=True)
    recipient: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    parcel_id: Mapped[str] = mapped_column(String(64), index=True)
    rule_id: Mapped[str] = mapped_column(String(8))
    rule_version: Mapped[str] = mapped_column(String(16))
    key: Mapped[str] = mapped_column(String(200))
    severity: Mapped[str] = mapped_column(String(16))
    outcome: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(16), default="New")
    evidence_ids: Mapped[list] = mapped_column(JSON)
    calc: Mapped[dict] = mapped_column(JSON)
    message_en: Mapped[str] = mapped_column(Text)
    message_bn: Mapped[str] = mapped_column(Text)
    next_check_en: Mapped[str] = mapped_column(Text)
    next_check_bn: Mapped[str] = mapped_column(Text)
    heuristic: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String(40))


class AuditLogEntry(Base):
    __tablename__ = "audit_log"
    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(48))
    subject_id: Mapped[str] = mapped_column(String(200))
    payload_hash: Mapped[str] = mapped_column(String(64))
    prev_hash: Mapped[str] = mapped_column(String(64))
    entry_hash: Mapped[str] = mapped_column(String(64))
    timestamp: Mapped[str] = mapped_column(String(40))


class RegParcel(Base):
    """A plot (mouza + dag number) in the officer-portal demo registry. Synthetic names only."""

    __tablename__ = "reg_parcels"
    __table_args__ = (UniqueConstraint("mouza_key", "dag_no"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mouza: Mapped[str] = mapped_column(String(120))
    mouza_key: Mapped[str] = mapped_column(String(120))
    dag_no: Mapped[str] = mapped_column(String(32))
    total_area: Mapped[float] = mapped_column(Float)  # shatak (decimal)


class RegHolding(Base):
    """Who currently holds how much of a plot."""

    __tablename__ = "reg_holdings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("reg_parcels.id"), index=True)
    owner: Mapped[str] = mapped_column(String(120))
    owner_key: Mapped[str] = mapped_column(String(120))
    area: Mapped[float] = mapped_column(Float)


class RegEvent(Base):
    """Ownership timeline entry: the opening record or an accepted transfer."""

    __tablename__ = "reg_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("reg_parcels.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # "initial" | "transfer"
    event_date: Mapped[date] = mapped_column(Date)
    from_owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    from_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    to_owner: Mapped[str] = mapped_column(String(120))
    area: Mapped[float] = mapped_column(Float)
    attempt_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)


class RegKhatian(Base):
    """Who the khatian (land record) names for a plot. It only changes when the mutation (namjari) is done,
    so after a deed is registered it differs from RegHolding until the mutation catches up."""

    __tablename__ = "reg_khatian"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("reg_parcels.id"), index=True)
    owner: Mapped[str] = mapped_column(String(120))
    owner_key: Mapped[str] = mapped_column(String(120))


class RegAttempt(Base):
    """Every registration request and what the checker decided, including the blocked ones."""

    __tablename__ = "reg_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[str] = mapped_column(String(40))
    officer: Mapped[str] = mapped_column(String(64))
    parcel_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    mouza: Mapped[str] = mapped_column(String(120))
    dag_no: Mapped[str] = mapped_column(String(32))
    seller: Mapped[str] = mapped_column(String(120))
    buyer: Mapped[str] = mapped_column(String(120))
    area: Mapped[float] = mapped_column(Float)
    deed_date: Mapped[date] = mapped_column(Date)
    verdict: Mapped[str] = mapped_column(String(16), index=True)  # success | warning | blocked
    rule_id: Mapped[str] = mapped_column(String(8))
    reason_en: Mapped[str] = mapped_column(Text)
    reason_bn: Mapped[str] = mapped_column(Text)
    calc: Mapped[dict] = mapped_column(JSON)


Index("ix_alerts_scenario_parcel", Alert.scenario_id, Alert.parcel_id)
