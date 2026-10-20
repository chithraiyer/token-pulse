"""US2 — /api/teams contract."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_teams_lists_members_grouped(client: TestClient) -> None:
    teams = client.get("/api/teams").json()
    by_id = {t["id"]: t for t in teams}
    assert {"platform", "product"} <= set(by_id)

    all_members = {m["id"] for t in teams for m in t["members"]}
    assert {"alice", "bob", "carol", "dave", "erin", "frank", "__unattributed__"} <= all_members

    unattr = next(m for t in teams for m in t["members"] if m["id"] == "__unattributed__")
    assert unattr["is_unattributed"] is True
