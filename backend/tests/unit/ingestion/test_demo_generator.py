"""US1 — the demo generator is deterministic and plants the expected patterns."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from tokenpulse.ingestion.demo_generator import generate

END = date(2026, 9, 7)


def test_same_seed_same_params_is_identical() -> None:
    a = generate(seed=20260907, days=90, members=6, end_date=END)
    b = generate(seed=20260907, days=90, members=6, end_date=END)
    assert a == b


def test_different_seed_changes_the_data() -> None:
    a = generate(seed=1, days=90, members=6, end_date=END)
    b = generate(seed=2, days=90, members=6, end_date=END)
    assert a != b


def test_shape_matches_request() -> None:
    buckets = generate(seed=20260907, days=90, members=6, end_date=END)
    members = {b.member_id for b in buckets}
    days = {b.date for b in buckets}
    assert len(members) == 6
    assert len(days) == 90
    assert max(days) == END
    assert all(b.source == "demo" and b.source_identity is None for b in buckets)


def test_contains_a_week_long_opus_spike_for_member_0() -> None:
    buckets = generate(seed=20260907, days=90, members=6, end_date=END)
    opus_by_day: dict[date, int] = defaultdict(int)
    for b in buckets:
        if b.member_id == "alice" and b.model == "claude-opus-4":
            opus_by_day[b.date] += b.input_tokens
    ordered = [opus_by_day[d] for d in sorted(opus_by_day)]
    baseline = sorted(ordered)[len(ordered) // 2]
    spike_days = [v for v in ordered if v > baseline * 5]
    assert len(spike_days) >= 5  # a sustained ~week-long spike


def test_contains_a_low_cache_high_input_member() -> None:
    buckets = generate(seed=20260907, days=90, members=6, end_date=END)
    carol = [b for b in buckets if b.member_id == "carol"]
    total_input = sum(b.input_tokens for b in carol)
    total_cache_read = sum(b.cache_read_tokens for b in carol)
    assert total_input > 0
    assert total_cache_read / total_input < 0.10


def test_product_team_model_mix_shifts_toward_opus() -> None:
    buckets = generate(seed=20260907, days=90, members=6, end_date=END)
    early_opus = early_total = late_opus = late_total = 0
    for b in buckets:
        if b.member_id not in {"dave", "erin", "frank"}:
            continue
        offset = (END - b.date).days
        if offset > 40:
            early_total += b.input_tokens
            early_opus += b.input_tokens if b.model == "claude-opus-4" else 0
        elif offset < 15:
            late_total += b.input_tokens
            late_opus += b.input_tokens if b.model == "claude-opus-4" else 0
    assert (late_opus / late_total) > (early_opus / early_total) + 0.10


def test_rejects_out_of_range_member_count() -> None:
    import pytest

    with pytest.raises(ValueError):
        generate(seed=1, days=10, members=99, end_date=END)
