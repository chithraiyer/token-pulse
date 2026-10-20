"""US1 — seeding stores the dataset and is idempotent (FR-007)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from helpers import seed_into
from tokenpulse.config import Settings
from tokenpulse.db.models import Member, UsageRecord


def test_seed_creates_members_and_records(db: Session, settings: Settings) -> None:
    seed_into(db, settings)
    members = db.scalars(select(Member.id).where(Member.id != "__unattributed__")).all()
    assert set(members) == {"alice", "bob", "carol", "dave", "erin", "frank"}

    rows = db.scalar(select(func.count()).select_from(UsageRecord))
    distinct_days = db.scalar(select(func.count(func.distinct(UsageRecord.date))))
    assert distinct_days == 90
    assert rows and rows > 90 * 6  # multiple models per member-day


def test_reseeding_is_idempotent(db: Session, settings: Settings) -> None:
    seed_into(db, settings)
    first = db.scalar(select(func.count()).select_from(UsageRecord))
    seed_into(db, settings)
    second = db.scalar(select(func.count()).select_from(UsageRecord))
    assert first == second


def test_unattributed_member_exists(seeded_db: Session) -> None:
    row = seeded_db.get(Member, "__unattributed__")
    assert row is not None and row.is_unattributed is True
