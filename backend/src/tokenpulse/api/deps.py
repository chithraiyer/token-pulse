"""Shared FastAPI dependencies: settings and a request-scoped DB session."""

from __future__ import annotations

import os
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy.orm import Session, sessionmaker

from tokenpulse.config import Settings
from tokenpulse.db.session import make_engine, make_session_factory

CONFIG_ENV = "TOKENPULSE_CONFIG"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.load(os.environ.get(CONFIG_ENV))


@lru_cache(maxsize=1)
def _session_factory() -> sessionmaker[Session]:
    return make_session_factory(make_engine(get_settings()))


def get_session() -> Iterator[Session]:
    session = _session_factory()()
    try:
        yield session
    finally:
        session.close()
