"""US2 — /api/totals contract, including the team == Σ members invariant (FR-017)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_team_equals_sum_of_members(client: TestClient) -> None:
    body = client.get("/api/totals?start=2026-08-01&end=2026-09-07").json()
    assert body["team"]["cost_micros"] == sum(m["cost_micros"] for m in body["members"])
    for field in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens"):
        assert body["team"][field] == sum(m[field] for m in body["members"])


def test_members_sorted_and_named(client: TestClient) -> None:
    body = client.get("/api/totals?start=2026-08-01&end=2026-09-07").json()
    ids = [m["scope_id"] for m in body["members"]]
    assert ids == sorted(ids)
    assert "alice" in ids


def test_prev_period_delta_present_when_prior_data_exists(client: TestClient) -> None:
    # 90 days of history ⇒ a 2-week window in September has a populated prior window.
    body = client.get("/api/totals?start=2026-08-25&end=2026-09-07").json()
    assert body["team"]["prev_period_delta_pct"] is not None
