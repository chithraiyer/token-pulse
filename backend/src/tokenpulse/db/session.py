"""Engine / session factory and schema bootstrap.

Demo mode uses a plain SQLite file. Live mode's SQLCipher-encrypted engine lands in US5
(T092); ``Settings.database_url`` guards it until then.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from tokenpulse.config import Settings

_ALEMBIC_DIR = Path(__file__).resolve().parent / "migrations"


def make_engine(settings: Settings) -> Engine:
    return create_engine(settings.database_url(), future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def ensure_schema(settings: Settings) -> None:
    """Upgrade the database to the latest Alembic revision (idempotent)."""
    import logging

    logging.getLogger("alembic").setLevel(logging.WARNING)
    cfg = AlembicConfig()
    cfg.set_main_option("script_location", str(_ALEMBIC_DIR))
    cfg.set_main_option("sqlalchemy.url", settings.database_url())
    command.upgrade(cfg, "head")


@contextmanager
def session_scope(settings: Settings) -> Iterator[Session]:
    engine = make_engine(settings)
    factory = make_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()
