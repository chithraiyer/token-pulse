"""SQLAlchemy models — the schema source of truth.

Stored fields are limited to the constitution's Section 2 list plus ``source_identity``
(see docs/adr/0001-source-identity-field.md). No prompt/completion/code content is stored.
Money is integer micro-USD; ratios that must stay exact are stored as decimal strings.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

UNATTRIBUTED_MEMBER_ID = "__unattributed__"


def make_idem_key(
    source: str, source_identity: str | None, member_id: str, model: str, day: date
) -> str:
    """Idempotency key for a usage row (FR-007). Pure function of stored fields."""
    who = source_identity if source_identity is not None else member_id
    return f"{source}|{who}|{model}|{day.isoformat()}"


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "team"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    members: Mapped[list[Member]] = relationship(back_populates="team")


class Member(Base):
    __tablename__ = "member"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    team_id: Mapped[str] = mapped_column(ForeignKey("team.id"), nullable=False, index=True)
    is_unattributed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    team: Mapped[Team] = relationship(back_populates="members")


class AttributionMapEntry(Base):
    """Operator-maintained source_identity -> member mapping (live mode only, FR-008a)."""

    __tablename__ = "attribution_map_entry"

    source_identity: Mapped[str] = mapped_column(String, primary_key=True)
    identity_kind: Mapped[str] = mapped_column(String, nullable=False)  # api_key | workspace
    member_id: Mapped[str] = mapped_column(ForeignKey("member.id"), nullable=False)


class UsageRecord(Base):
    __tablename__ = "usage_record"
    __table_args__ = (
        # Idempotent ingestion (FR-007). idem_key is a pure function of the fields below;
        # it exists only so demo rows (source_identity NULL) also dedupe under SQLite.
        UniqueConstraint("idem_key", name="uq_usage_record_idem_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("member.id"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False)  # demo | live
    source_identity: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    model: Mapped[str] = mapped_column(String, nullable=False)

    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_type: Mapped[str | None] = mapped_column(String, nullable=True)

    cost_micros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_is_estimate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pricing_table_version: Mapped[str] = mapped_column(String, nullable=False)

    idem_key: Mapped[str] = mapped_column(String, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    requested_start: Mapped[date] = mapped_column(Date, nullable=False)
    requested_end: Mapped[date] = mapped_column(Date, nullable=False)
    covered_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    covered_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    gap_days: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String, nullable=False)  # complete | partial | failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tool_version: Mapped[str] = mapped_column(String, nullable=False)


class ReportRun(Base):
    __tablename__ = "report_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_window_start: Mapped[date] = mapped_column(Date, nullable=False)
    source_window_end: Mapped[date] = mapped_column(Date, nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    pricing_table_versions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    rule_catalog_version: Mapped[str] = mapped_column(String, nullable=False)
    tool_version: Mapped[str] = mapped_column(String, nullable=False)
    reconciliation: Mapped[list | None] = mapped_column(JSON, nullable=True)


class SpikeFlag(Base):
    __tablename__ = "spike_flag"
    __table_args__ = (
        UniqueConstraint("report_run_id", "member_id", "date", name="uq_spike_flag_run_member_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("member.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    baseline_avg_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    deviation_ratio: Mapped[str] = mapped_column(String, nullable=False)  # exact decimal string
    excess_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    spike_multiple: Mapped[str] = mapped_column(String, nullable=False)
    high_floor_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    critical_floor_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    rule_catalog_version: Mapped[str] = mapped_column(String, nullable=False)
    report_run_id: Mapped[int] = mapped_column(ForeignKey("report_run.id"), nullable=False, index=True)


class Recommendation(Base):
    __tablename__ = "recommendation"
    __table_args__ = (
        UniqueConstraint(
            "report_run_id", "rule_id", "subject_kind", "subject_id",
            name="uq_recommendation_run_rule_subject",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_kind: Mapped[str] = mapped_column(String, nullable=False)  # member | team
    subject_id: Mapped[str] = mapped_column(String, nullable=False)
    rule_id: Mapped[str] = mapped_column(String, nullable=False)
    rule_catalog_version: Mapped[str] = mapped_column(String, nullable=False)
    window_start: Mapped[date] = mapped_column(Date, nullable=False)
    window_end: Mapped[date] = mapped_column(Date, nullable=False)
    trigger_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    threshold_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    message: Mapped[str] = mapped_column(String, nullable=False)
    estimated_savings_micros: Mapped[int | None] = mapped_column(Integer, nullable=True)
    savings_basis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    report_run_id: Mapped[int] = mapped_column(ForeignKey("report_run.id"), nullable=False, index=True)
