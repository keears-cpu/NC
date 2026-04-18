from __future__ import annotations

import pytest

from app.core import database
from app.core.config import AppSettings


def build_settings() -> AppSettings:
    return AppSettings(
        google_apps_script_url="https://script.google.com/macros/s/fake/exec",
        google_apps_script_timeout_seconds=2.0,
        storage_backend="apps_script",
        database_url="postgresql://example",
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


class FakeConnection:
    def __init__(self):
        self.executed: list[str] = []

    async def execute(self, statement):
        self.executed.append(" ".join(str(statement).split()))


class FakeBeginContext:
    def __init__(self, connection: FakeConnection):
        self._connection = connection

    async def __aenter__(self) -> FakeConnection:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class FakeEngine:
    def __init__(self):
        self.connection = FakeConnection()

    def begin(self) -> FakeBeginContext:
        return FakeBeginContext(self.connection)


@pytest.mark.anyio
async def test_ensure_database_schema_includes_phase1_b2b_tables(monkeypatch):
    fake_engine = FakeEngine()
    monkeypatch.setattr(database, "_schema_initialized", False)
    monkeypatch.setattr(database, "get_engine", lambda settings=None: fake_engine)

    created = await database.ensure_database_schema(settings=build_settings())

    assert created is True
    executed_sql = "\n".join(fake_engine.connection.executed)
    assert "create table if not exists charts" in executed_sql
    assert "create table if not exists reports" in executed_sql
    assert "create table if not exists counselors" in executed_sql
    assert "create table if not exists storage_audit_runs" in executed_sql
    assert "create table if not exists organizations" in executed_sql
    assert "create table if not exists organization_memberships" in executed_sql
    assert "create table if not exists report_runs" in executed_sql
    assert "create table if not exists report_versions" in executed_sql
    assert "create table if not exists access_events" in executed_sql
