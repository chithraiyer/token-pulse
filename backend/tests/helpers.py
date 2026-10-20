"""Test helpers importable as ``from helpers import ...`` (tests/ is on pythonpath)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from tokenpulse.config import Settings
from tokenpulse.db.models import Member
from tokenpulse.ingestion.demo_generator import generate, roster
from tokenpulse.ingestion.pipeline import upsert_usage_records
from tokenpulse.services import load_pricing

REPO_CONFIG = Path(__file__).resolve().parents[1] / "config"
DEMO_END = date(2026, 9, 7)


def seed_into(session: Session, settings: Settings, *, days: int = 90, members: int = 6) -> None:
    for member_id, display_name, team_id in roster(members):
        stmt = sqlite_insert(Member).values(
            id=member_id, display_name=display_name, team_id=team_id, is_unattributed=False
        )
        session.execute(stmt.on_conflict_do_nothing(index_elements=["id"]))
    buckets = generate(seed=settings.demo_seed, days=days, members=members, end_date=DEMO_END)
    upsert_usage_records(session, buckets, pricing=load_pricing(settings))
    session.commit()
