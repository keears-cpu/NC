from __future__ import annotations

import pytest

from app.core.config import AppSettings
from app.schemas import Availability, ChartBody, ChartInput, ChartMetadata, ChartSettings, HouseCusp, NatalChartRecord, StoredChartListItem, StoredChartListResponse, AnglePoint


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


def build_item(
    *,
    record_id: str,
    chart_id: str | None = None,
    report_id: str | None = None,
    viewer_code: str | None = None,
    product_code: str | None = None,
    payment_status: str | None = None,
    report_request: dict[str, object] | None = None,
    report_payload: dict[str, object] | None = None,
    report_html: str | None = None,
    report_html_url: str | None = None,
    chart_svg: str | None = None,
) -> StoredChartListItem:
    return StoredChartListItem(
        record_id=record_id,
        chart_id=chart_id,
        birth_date="1980-04-17",
        birth_time_local="00:00",
        birth_place_name="Seoul, Korea",
        report_id=report_id,
        report_viewer_code=viewer_code,
        report_product_code=product_code,
        report_payment_status=payment_status,
        report_request=report_request,
        report_payload=report_payload,
        report_html=report_html,
        report_html_url=report_html_url,
        chart_svg=chart_svg,
    )


@pytest.mark.anyio
async def test_reconcile_storage_returns_blocked_when_database_gate_fails(monkeypatch):
    from app.services import storage_reconciliation_service

    async def fake_get_storage_audit(settings=None):
        return {
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
        }

    def fail_fetch_stored_charts(*args, **kwargs):
        raise AssertionError("fetch_stored_charts should not be called when gate is blocked")

    monkeypatch.setattr(storage_reconciliation_service, "get_storage_audit", fake_get_storage_audit)
    monkeypatch.setattr(storage_reconciliation_service, "fetch_stored_charts", fail_fetch_stored_charts)

    result = await storage_reconciliation_service.reconcile_storage(settings=build_settings(), limit=25)

    assert result["ok"] is False
    assert result["status"] == "blocked"
    assert result["blocking_reason"] == "DATABASE_URL not configured"
    assert result["next_action"] == "DATABASE_URL을 설정한 뒤 다시 점검하세요."
    assert result["comparison"]["parity_ok_rows"] == 0


@pytest.mark.anyio
async def test_reconcile_storage_counts_parity_and_diffs(monkeypatch):
    from app.services import storage_reconciliation_service

    sample_apps_script = StoredChartListResponse(
        ok=True,
        items=[
            build_item(
                record_id="r-1",
                chart_id="r-1",
                report_id="report-1",
                viewer_code="1234",
                product_code="adult_deep_blueprint",
                payment_status="paid",
                report_request={"preset": "adult_deep_blueprint"},
                report_payload={"sections": []},
                report_html="<html>A</html>",
                report_html_url="https://example.com/a",
                chart_svg="<svg>a</svg>",
            ),
            build_item(
                record_id="r-2",
                chart_id="r-2",
                report_id="report-2",
                viewer_code="5678",
                product_code="adult_deep_blueprint",
                payment_status="pending",
                report_request={"preset": "adult_deep_blueprint", "addons": ["career"]},
                report_payload={"sections": ["one"]},
                report_html="<html>B</html>",
                report_html_url="https://example.com/b",
                chart_svg="<svg>b</svg>",
            ),
            build_item(
                record_id="r-only-apps",
                chart_id="r-only-apps",
                report_id="report-only-apps",
                viewer_code="9999",
                product_code="adult_deep_blueprint",
                payment_status="paid",
            ),
        ],
    )

    postgres_rows = [
        {
            "record_id": "r-1",
            "chart_id": "r-1",
            "report_id": "report-1",
            "viewer_code": "1234",
            "product_code": "adult_deep_blueprint",
            "payment_status": "paid",
            "report_request_json": {"preset": "adult_deep_blueprint"},
            "report_payload_json": {"sections": []},
            "report_html": "<html>A</html>",
            "report_html_url": "https://example.com/a",
            "chart_svg": "<svg>a</svg>",
        },
        {
            "record_id": "r-2",
            "chart_id": "r-2",
            "report_id": "report-2",
            "viewer_code": "8888",
            "product_code": "adult_deep_blueprint",
            "payment_status": "paid",
            "report_request_json": {"preset": "adult_deep_blueprint", "addons": ["career"]},
            "report_payload_json": {"sections": ["one"]},
            "report_html": "<html>B</html>",
            "report_html_url": "https://example.com/b",
            "chart_svg": "<svg>b</svg>",
        },
        {
            "record_id": "r-only-postgres",
            "chart_id": "r-only-postgres",
            "report_id": "report-only-postgres",
            "viewer_code": "0000",
            "product_code": "adult_deep_blueprint",
            "payment_status": "paid",
            "report_request_json": {"preset": "adult_deep_blueprint"},
            "report_payload_json": {"sections": []},
            "report_html": "<html>C</html>",
            "report_html_url": "https://example.com/c",
            "chart_svg": "<svg>c</svg>",
        },
    ]

    async def fake_get_storage_audit(settings=None):
        return {
            "database": {
                "configured": True,
                "reachable": True,
                "state": "reachable",
                "blocking_reason": None,
                "next_action": "Apps Script ↔ Postgres parity audit를 실행하세요.",
                "reachability_gate_passed": True,
                "backend": "apps_script",
                "message": "database reachable",
            }
        }

    async def fake_fetch_postgres_rows(*, settings, limit):
        assert limit == 25
        return postgres_rows, None

    async def fake_fetch_stored_charts(*args, **kwargs):
        return sample_apps_script

    monkeypatch.setattr(storage_reconciliation_service, "get_storage_audit", fake_get_storage_audit)
    monkeypatch.setattr(storage_reconciliation_service, "fetch_stored_charts", fake_fetch_stored_charts)
    monkeypatch.setattr(storage_reconciliation_service, "_fetch_postgres_rows", fake_fetch_postgres_rows)

    result = await storage_reconciliation_service.reconcile_storage(settings=build_settings(), limit=25)

    assert result["ok"] is True
    assert result["status"] == "ok"
    assert result["comparison"]["apps_script_total_rows"] == 3
    assert result["comparison"]["postgres_total_rows"] == 3
    assert result["comparison"]["shared_record_rows"] == 2
    assert result["comparison"]["apps_script_only_rows"] == 1
    assert result["comparison"]["postgres_only_rows"] == 1
    assert result["comparison"]["parity_ok_rows"] == 1
    assert result["comparison"]["parity_diff_rows"] == 1
    assert result["comparison"]["record_status_counts"]["parity_diff"] == 1
    assert result["comparison"]["field_diff_counts"]["viewer_code"] == 1
    assert any(sample["status"] == "parity_diff" for sample in result["comparison"]["samples"])
    assert result["summary"].startswith("sample_limit=25;")
