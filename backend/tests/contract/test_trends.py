"""US2 — /api/trends contract."""

from __future__ import annotations

from fastapi.testclient import TestClient

RANGE = "start=2026-07-15&end=2026-09-07"


def test_team_cost_trend_shape(client: TestClient) -> None:
    body = client.get(f"/api/trends?scope=team&metric=cost&{RANGE}").json()
    assert body["scope"] == "team"
    assert body["metric"] == "cost"
    assert body["empty_reason"] is None
    assert len(body["series"]) == 1
    pts = body["series"][0]["points"]
    assert len(pts) == 55  # inclusive day count
    p = pts[0]
    assert set(p) == {"date", "value", "is_spike", "missing"}


def test_member_by_model_series(client: TestClient) -> None:
    body = client.get(
        f"/api/trends?scope=member&scope_id=alice&metric=cost&by_model=true&{RANGE}"
    ).json()
    keys = {s["key"] for s in body["series"]}
    assert keys == {"claude-opus-4", "claude-sonnet-4", "claude-haiku-4"}


def test_out_of_range_dates_rejected(client: TestClient) -> None:
    r = client.get("/api/trends?scope=team&metric=cost&start=2026-09-07&end=2026-09-01")
    assert r.status_code == 422


def test_empty_range_reports_reason(client: TestClient) -> None:
    body = client.get("/api/trends?scope=team&metric=cost&start=2000-01-01&end=2000-01-05").json()
    assert body["empty_reason"] == "no_data_in_range"


def test_no_spikes_flagged_before_report_run(client: TestClient) -> None:
    # US2 has no ReportRun yet, so is_spike must be false everywhere.
    body = client.get(f"/api/trends?scope=team&metric=cost&{RANGE}").json()
    assert all(not pt["is_spike"] for s in body["series"] for pt in s["points"])
