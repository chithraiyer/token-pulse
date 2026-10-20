"""Shared fixtures: a throwaway SQLite DB, deterministic demo data, and a TestClient
with the API's settings/session dependencies overridden.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from helpers import REPO_CONFIG, seed_into
from tokenpulse.api.app import app
from tokenpulse.api.deps import get_session, get_settings
from tokenpulse.config import Settings
from tokenpulse.db.session import ensure_schema, make_engine, make_session_factory


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        mode="demo",
        database_path=tmp_path / "test.db",
        db_key_env="TOKENPULSE_DB_KEY",
        retention_days=90,
        pricing_dir=REPO_CONFIG / "pricing",
        schema_dir=REPO_CONFIG / "schemas",
        rules_catalog=REPO_CONFIG / "rules" / "catalog-v1.yaml",
        spike_multiple_override=None,
        demo_seed=20260907,
        demo_days=90,
        demo_members=6,
    )


@pytest.fixture
def db(settings: Settings) -> Iterator[Session]:
    ensure_schema(settings)
    engine = make_engine(settings)
    session = make_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def seeded_db(db: Session, settings: Settings) -> Session:
    seed_into(db, settings)
    return db


@pytest.fixture
def client(settings: Settings, seeded_db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_session] = lambda: seeded_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
