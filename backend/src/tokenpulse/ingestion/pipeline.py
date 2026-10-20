"""Normalise raw usage into ``UsageRecord`` rows and upsert them idempotently (FR-007).

Cost is computed here at the boundary via the pure ``PricingCatalog`` so that everything
downstream in ``tokenpulse.core`` stays a pure function of stored records.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from tokenpulse.core.pricing import PricingCatalog, TokenCounts
from tokenpulse.db.models import UsageRecord, make_idem_key


@dataclass(frozen=True)
class RawUsageBucket:
    member_id: str
    source: str  # demo | live
    source_identity: str | None
    date: date
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    request_type: str | None = None


@dataclass(frozen=True)
class UpsertResult:
    inserted: int
    updated: int

    @property
    def total(self) -> int:
        return self.inserted + self.updated


def upsert_usage_records(
    session: Session,
    buckets: Iterable[RawUsageBucket],
    *,
    pricing: PricingCatalog,
) -> UpsertResult:
    buckets = list(buckets)
    keys = {
        make_idem_key(b.source, b.source_identity, b.member_id, b.model, b.date)
        for b in buckets
    }
    existing: set[str] = set()
    if keys:
        existing = set(
            session.scalars(
                select(UsageRecord.idem_key).where(UsageRecord.idem_key.in_(keys))
            ).all()
        )

    inserted = updated = 0
    for b in buckets:
        table = pricing.table_for_date(b.date)
        cost_micros, is_estimate = pricing.cost_micros(
            TokenCounts(b.input_tokens, b.output_tokens, b.cache_read_tokens, b.cache_write_tokens),
            b.model,
            on=b.date,
        )
        idem_key = make_idem_key(
            b.source, b.source_identity, b.member_id, b.model, b.date
        )
        values = {
            "member_id": b.member_id,
            "source": b.source,
            "source_identity": b.source_identity,
            "date": b.date,
            "model": b.model,
            "input_tokens": b.input_tokens,
            "output_tokens": b.output_tokens,
            "cache_read_tokens": b.cache_read_tokens,
            "cache_write_tokens": b.cache_write_tokens,
            "request_type": b.request_type,
            "cost_micros": cost_micros,
            "cost_is_estimate": is_estimate,
            "pricing_table_version": table.version,
            "idem_key": idem_key,
        }
        stmt = sqlite_insert(UsageRecord).values(**values)
        update_cols = {c: stmt.excluded[c] for c in values if c != "idem_key"}
        stmt = stmt.on_conflict_do_update(index_elements=["idem_key"], set_=update_cols)
        session.execute(stmt)
        if idem_key in existing:
            updated += 1
        else:
            inserted += 1
    session.flush()
    return UpsertResult(inserted=inserted, updated=updated)
