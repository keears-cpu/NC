from __future__ import annotations

from collections.abc import Iterable

import pytest
from fastapi.testclient import TestClient

from app.core.config import AppSettings


def build_settings(database_url: str | None = "postgresql://example") -> AppSettings:
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


def test_storage_audit_route_returns_service_payload(monkeypatch):
    from app import main

    expected_payload = {
        "operational_hub": "google_apps_script",
        "durable_store": "postgres",
        "storage_backend": "apps_script",
        "google_apps_script_url_configured": True,
        "database": {
            "configured": False,
            "reachable": False,
            "state": "unconfigured",
            "blocking_reason": "DATABASE_URL not configured",
            "next_action": "DATABASE_URL을 설정한 뒤 다시 점검하세요.",
            "reachability_gate_passed": False,
            "backend": "apps_script",
            "message": "DATABASE_URL not configured",
        },
        "core_tables": {
            "charts": {"exists": False, "row_count": None},
            "reports": {"exists": False, "row_count": None},
            "counselors": {"exists": False, "row_count": None},
        },
        "phase1_schema": {
            "ready": False,
            "tables": {
                "storage_audit_runs": False,
                "organizations": False,
                "organization_memberships": False,
                "report_runs": False,
                "report_versions": False,
                "access_events": False,
            },
        },
        "summary": "database=unconfigured; reachability_gate_passed=false; core_tables=0/3; core_rows=0; phase1_tables=0/6",
    }

    async def fake_get_storage_audit(settings):
        assert settings.database_url is None
        return expected_payload

    monkeypatch.setattr(main, "get_settings", lambda: build_settings(database_url=None))
    monkeypatch.setattr(main, "get_storage_audit", fake_get_storage_audit)

    with TestClient(main.app) as client:
        response = client.get("/api/storage/audit")

    assert response.status_code == 200
    assert response.json() == expected_payload


class FakeScalarResult:
    def __init__(self, value: int):
        self._value = value

    def scalar_one(self) -> int:
        return self._value


class FakeScalars:
    def __init__(self, values: Iterable[str]):
        self._values = list(values)

    def all(self) -> list[str]:
        return list(self._values)


class FakeTableResult:
    def __init__(self, values: Iterable[str]):
        self._values = list(values)

    def scalars(self) -> FakeScalars:
        return FakeScalars(self._values)


class FakeConnection:
    def __init__(self, existing_tables: set[str], row_counts: dict[str, int]):
        self._existing_tables = existing_tables
        self._row_counts = row_counts

    async def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        if "select 1" in sql.lower():
            return FakeScalarResult(1)
        if "information_schema.tables" in sql:
            return FakeTableResult(self._existing_tables)
        if "select count(*)" in sql.lower():
            table_name = sql.lower().split("from", 1)[1].strip().strip('"')
            return FakeScalarResult(self._row_counts[table_name])
        raise AssertionError(f"Unexpected SQL: {sql}")


class FakeConnectContext:
    def __init__(self, connection: FakeConnection):
        self._connection = connection

    async def __aenter__(self) -> FakeConnection:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class FakeEngine:
    def __init__(self, existing_tables: set[str], row_counts: dict[str, int]):
        self._connection = FakeConnection(existing_tables, row_counts)

    def connect(self) -> FakeConnectContext:
        return FakeConnectContext(self._connection)


@pytest.mark.anyio
async def test_get_storage_audit_reports_unconfigured_database():
    from app.services.storage_audit_service import get_storage_audit

    audit = await get_storage_audit(settings=build_settings(database_url=None))

    assert audit["database"]["configured"] is False
    assert audit["database"]["reachable"] is False
    assert audit["database"]["state"] == "unconfigured"
    assert audit["database"]["blocking_reason"] == "DATABASE_URL not configured"
    assert audit["database"]["reachability_gate_passed"] is False
    assert audit["core_tables"]["charts"]["row_count"] is None
    assert audit["phase1_schema"]["ready"] is False
    assert audit["summary"] == "database=unconfigured; reachability_gate_passed=false; core_tables=0/3; core_rows=0; phase1_tables=0/6"


@pytest.mark.anyio
async def test_get_storage_audit_reports_incomplete_schema(monkeypatch):
    from app.services import storage_audit_service

    fake_engine = FakeEngine(
        existing_tables={"charts", "reports", "organizations"},
        row_counts={"charts": 4, "reports": 2},
    )
    monkeypatch.setattr(storage_audit_service, "get_engine", lambda settings=None: fake_engine)

    audit = await storage_audit_service.get_storage_audit(settings=build_settings())

    assert audit["database"]["configured"] is True
    assert audit["database"]["reachable"] is True
    assert audit["database"]["state"] == "reachable"
    assert audit["database"]["reachability_gate_passed"] is True
    assert audit["core_tables"]["charts"] == {"exists": True, "row_count": 4}
    assert audit["core_tables"]["counselors"] == {"exists": False, "row_count": None}
    assert audit["phase1_schema"]["tables"]["organizations"] is True
    assert audit["phase1_schema"]["tables"]["report_runs"] is False
    assert audit["phase1_schema"]["ready"] is False
    assert audit["summary"] == "database=reachable; reachability_gate_passed=true; core_tables=2/3; core_rows=6; phase1_tables=1/6"


@pytest.mark.anyio
async def test_get_storage_audit_reports_zero_row_schema_ready(monkeypatch):
    from app.services import storage_audit_service

    all_tables = {
        "charts",
        "reports",
        "counselors",
        "storage_audit_runs",
        "organizations",
        "organization_memberships",
        "report_runs",
        "report_versions",
        "access_events",
    }
    fake_engine = FakeEngine(
        existing_tables=all_tables,
        row_counts={"charts": 0, "reports": 0, "counselors": 0},
    )
    monkeypatch.setattr(storage_audit_service, "get_engine", lambda settings=None: fake_engine)

    audit = await storage_audit_service.get_storage_audit(settings=build_settings())

    assert audit["phase1_schema"]["ready"] is True
    assert audit["core_tables"]["charts"]["row_count"] == 0
    assert audit["database"]["next_action"] == "Apps Script ↔ Postgres parity audit를 실행하세요."
    assert audit["summary"] == "database=reachable; reachability_gate_passed=true; core_tables=3/3; core_rows=0; phase1_tables=6/6"


@pytest.mark.anyio
async def test_get_storage_audit_reports_core_row_counts(monkeypatch):
    from app.services import storage_audit_service

    all_tables = {
        "charts",
        "reports",
        "counselors",
        "storage_audit_runs",
        "organizations",
        "organization_memberships",
        "report_runs",
        "report_versions",
        "access_events",
    }
    fake_engine = FakeEngine(
        existing_tables=all_tables,
        row_counts={"charts": 11, "reports": 7, "counselors": 2},
    )
    monkeypatch.setattr(storage_audit_service, "get_engine", lambda settings=None: fake_engine)

    audit = await storage_audit_service.get_storage_audit(settings=build_settings())

    assert audit["core_tables"]["charts"] == {"exists": True, "row_count": 11}
    assert audit["core_tables"]["reports"] == {"exists": True, "row_count": 7}
    assert audit["core_tables"]["counselors"] == {"exists": True, "row_count": 2}
    assert audit["summary"] == "database=reachable; reachability_gate_passed=true; core_tables=3/3; core_rows=20; phase1_tables=6/6"
