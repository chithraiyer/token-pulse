"""US1 — /api/meta contract (contracts/rest-api.openapi.yaml)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_meta_shape_and_demo_flag(client: TestClient) -> None:
    body = client.get("/api/meta").json()
    assert body["mode"] == "demo"
    assert body["is_demo_data"] is True
    assert body["rule_catalog_version"] == "v1"
    assert body["spike_multiple"] == "2.5"
    assert body["retention_days"] == 90
    assert "anthropic-2026-09-01" in body["pricing_table_versions"]
    assert body["tool_version"]
