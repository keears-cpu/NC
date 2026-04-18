from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import AppSettings


def build_settings(database_url: str | None = None) -> AppSettings:
    return AppSettings(
        google_apps_script_url="https://script.google.com/macros/s/fake/exec",
        google_apps_script_timeout_seconds=2.0,
        storage_backend="apps_script",
        database_url=database_url,
        supabase_url="https://example.supabase.co",
        supabase_publishable_key="publishable",
        supabase_service_role_key="service-role",
        supabase_project_ref="project-ref",
        portone_store_id=None,
        portone_channel_key=None,
        portone_api_secret=None,
        portone_webhook_secret=None,
        payment_client_base_url=None,
        payment_redirect_path="/payment/redirect",
        payment_webhook_url=None,
    )


def test_storage_reconciliation_route_returns_blocked_payload(monkeypatch):
    from app import main

    expected_payload = {
        "ok": False,
        "status": "blocked",
        "scope": "apps_script_vs_postgres",
        "sample_limit": 25,
        "reachability_gate_passed": False,
        "blocking_reason": "DATABASE_URL not configured",
        "next_action": "DATABASE_URL을 설정한 뒤 다시 점검하세요.",
        "audit": {
            "database": {
                "configured": False,
                "reachable": False,
                "state": "unconfigured",
                "blocking_reason": "DATABASE_URL not configured",
                "next_action": "DATABASE_URL을 설정한 뒤 다시 점검하세요.",
                "reachability_gate_passed": False,
                "backend": "apps_script",
                "message": "DATABASE_URL not configured",
            }
        },
        "comparison": {
            "apps_script_total_rows": 0,
            "postgres_total_rows": 0,
            "shared_record_rows": 0,
            "apps_script_only_rows": 0,
            "postgres_only_rows": 0,
            "parity_ok_rows": 0,
            "parity_diff_rows": 0,
            "missing_record_id_rows": 0,
            "record_status_counts": {
                "apps_script_only": 0,
                "postgres_only": 0,
                "parity_ok": 0,
                "parity_diff": 0,
                "missing_record_id": 0,
            },
            "field_diff_counts": {},
            "samples": [],
        },
        "summary": "status=blocked; blocked=DATABASE_URL not configured",
    }

    async def fake_reconcile_storage(settings=None, limit=100):
        assert limit == 25
        return expected_payload

    monkeypatch.setattr(main, "reconcile_storage", fake_reconcile_storage)
    monkeypatch.setattr(main, "get_settings", lambda: build_settings())

    async def noop_ensure_database_schema(settings=None):
        return None

    monkeypatch.setattr(main, "ensure_database_schema", noop_ensure_database_schema)

    with TestClient(main.app) as client:
        response = client.get("/api/storage/reconcile?limit=25")

    assert response.status_code == 200
    assert response.json() == expected_payload


@pytest.mark.anyio
async def test_storage_reconciliation_route_returns_success_payload(monkeypatch):
    from app import main

    expected_payload = {
        "ok": True,
        "status": "ok",
        "scope": "apps_script_vs_postgres",
        "sample_limit": 25,
        "reachability_gate_passed": True,
        "blocking_reason": None,
        "next_action": "차이가 있으면 record_id 기준으로 개별 field drift를 점검하세요.",
        "audit": {"database": {"state": "reachable", "reachability_gate_passed": True}},
        "comparison": {
            "apps_script_total_rows": 2,
            "postgres_total_rows": 2,
            "shared_record_rows": 2,
            "apps_script_only_rows": 0,
            "postgres_only_rows": 0,
            "parity_ok_rows": 2,
            "parity_diff_rows": 0,
            "missing_record_id_rows": 0,
            "record_status_counts": {
                "apps_script_only": 0,
                "postgres_only": 0,
                "parity_ok": 2,
                "parity_diff": 0,
                "missing_record_id": 0,
            },
            "field_diff_counts": {},
            "samples": [],
        },
        "summary": "sample_limit=25; apps_script_total_rows=2; postgres_total_rows=2; shared_record_rows=2; apps_script_only_rows=0; postgres_only_rows=0; parity_ok_rows=2; parity_diff_rows=0; missing_record_id_rows=0",
    }

    async def fake_reconcile_storage(settings=None, limit=100):
        assert limit == 25
        return expected_payload

    monkeypatch.setattr(main, "reconcile_storage", fake_reconcile_storage)
    monkeypatch.setattr(main, "get_settings", lambda: build_settings())

    async def noop_ensure_database_schema(settings=None):
        return None

    monkeypatch.setattr(main, "ensure_database_schema", noop_ensure_database_schema)

    with TestClient(main.app) as client:
        response = client.get("/api/storage/reconcile?limit=25")

    assert response.status_code == 200
    assert response.json() == expected_payload
