"""``tokenpulse`` command-line interface (Typer).

In scope for US1/US2: ``seed`` (synthetic data) and ``serve`` (the API). ``ingest`` /
``report`` / ``prune`` land in later user stories.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer

from tokenpulse.config import Settings
from tokenpulse.logging import configure_logging, get_logger

app = typer.Typer(add_completion=False, help="TokenPulse — Claude Code cost & usage monitor.")
log = get_logger("tokenpulse.cli")

_ConfigOpt = Annotated[Path | None, typer.Option("--config", help="Path to a tokenpulse.toml")]
_LogOpt = Annotated[str, typer.Option("--log-level", help="debug|info|warning|error")]


@app.callback()
def _main(
    ctx: typer.Context,
    config: _ConfigOpt = None,
    log_level: _LogOpt = "info",
) -> None:
    configure_logging(log_level)
    ctx.obj = {"config": config}


def _settings(ctx: typer.Context) -> Settings:
    return Settings.load(ctx.obj["config"])


@app.command()
def seed(
    ctx: typer.Context,
    seed: Annotated[int | None, typer.Option(help="RNG seed (default: from config)")] = None,
    days: Annotated[int | None, typer.Option(help="Days of history (default: from config)")] = None,
    members: Annotated[int | None, typer.Option(help="Team members 1-8 (default: config)")] = None,
    end: Annotated[
        datetime | None,
        typer.Option(formats=["%Y-%m-%d"], help="Last day (default: today, UTC)"),
    ] = None,
    reset: Annotated[bool, typer.Option(help="Delete existing demo data first")] = False,
) -> None:
    """Generate the synthetic demo dataset and store it (demo mode)."""
    from sqlalchemy import delete
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    from tokenpulse.db.models import Member, UsageRecord
    from tokenpulse.db.session import ensure_schema, session_scope
    from tokenpulse.ingestion.demo_generator import generate, roster
    from tokenpulse.ingestion.pipeline import upsert_usage_records
    from tokenpulse.services import load_pricing

    s = _settings(ctx)
    if s.mode != "demo":
        raise typer.BadParameter("seed only runs in demo mode; set mode = \"demo\" in the config")

    rng_seed = seed if seed is not None else s.demo_seed
    n_days = days if days is not None else s.demo_days
    n_members = members if members is not None else s.demo_members
    end_date = (end.date() if end else datetime.now(UTC).date())

    ensure_schema(s)
    pricing = load_pricing(s)

    with session_scope(s) as session:
        if reset:
            session.execute(delete(UsageRecord).where(UsageRecord.source == "demo"))
            keep = {"__unattributed__"}
            session.execute(delete(Member).where(Member.id.not_in(keep)))

        for member_id, display_name, team_id in roster(n_members):
            stmt = sqlite_insert(Member).values(
                id=member_id, display_name=display_name, team_id=team_id, is_unattributed=False
            )
            session.execute(stmt.on_conflict_do_nothing(index_elements=["id"]))

        buckets = generate(seed=rng_seed, days=n_days, members=n_members, end_date=end_date)
        result = upsert_usage_records(session, buckets, pricing=pricing)

    typer.echo(
        f"seeded demo data: seed={rng_seed} days={n_days} members={n_members} end={end_date} "
        f"| inserted={result.inserted} updated={result.updated}"
    )
    log.info("demo_seeded", seed=rng_seed, days=n_days, members=n_members, end=str(end_date),
             inserted=result.inserted, updated=result.updated)


@app.command()
def serve(
    ctx: typer.Context,
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
) -> None:
    """Run the FastAPI app with uvicorn."""
    import uvicorn

    from tokenpulse.api.deps import CONFIG_ENV
    from tokenpulse.db.session import ensure_schema

    s = _settings(ctx)
    ensure_schema(s)
    cfg = ctx.obj["config"]
    if cfg is not None:
        os.environ[CONFIG_ENV] = str(Path(cfg).resolve())
    uvicorn.run("tokenpulse.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":  # pragma: no cover
    app()
