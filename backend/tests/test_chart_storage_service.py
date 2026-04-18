from __future__ import annotations

import pytest
from httpx import Response

from app.core.config import AppSettings
from app.schemas import (
    AnglePoint,
    Availability,
    ChartBody,
    ChartInput,
    ChartMetadata,
    ChartSettings,
    HouseCusp,
    LaterLifeCycleEvent,
    LaterLifePhaseWindow,
    LaterLifeTimingLayer,
    NatalChartRecord,
    ProfectionSnapshot,
    ChartStorageResult,
    ChartExtractRequest,
    TraditionalLayer,
    TraditionalPoint,
    TraditionalRuler,
)
from app.services.chart_storage_service import build_apps_script_payload, build_report_request_payload, store_chart_record


def build_settings(*, google_apps_script_url: str | None = "https://script.google.com/macros/s/fake/exec") -> AppSettings:
    return AppSettings(
        google_apps_script_url=google_apps_script_url,
        google_apps_script_timeout_seconds=2.0,
        storage_backend="apps_script",
        database_url=None,
        supabase_url=None,
        supabase_publishable_key=None,
        supabase_service_role_key=None,
        supabase_project_ref=None,
        portone_store_id=None,
        portone_channel_key=None,
        portone_api_secret=None,
        portone_webhook_secret=None,
        payment_client_base_url=None,
        payment_redirect_path="/payment/redirect",
        payment_webhook_url=None,
    )


def build_sample_chart() -> NatalChartRecord:
    return NatalChartRecord(
        metadata=ChartMetadata(chart_id="sample-chart", engine_name="swiss_ephemeris", status="ready", warnings=[]),
        input=ChartInput(
            person_name="Sample",
            birth_date="2016-04-19",
            birth_time_local="15:20",
            timezone="Asia/Seoul",
            birth_place_name="Yongin-si, South Korea",
            country_code="KR",
            latitude=37.2333,
            longitude=127.1833,
        ),
        settings=ChartSettings(),
        angles={
            "asc": AnglePoint(id="asc", label="Ascendant", sign="Virgo", degree=12.8, formatted="Virgo 12°48’", lon=162.8),
            "mc": AnglePoint(id="mc", label="Midheaven", sign="Gemini", degree=10.5667, formatted="Gemini 10°34’", lon=70.5667),
            "dsc": AnglePoint(id="dsc", label="Descendant", sign="Pisces", degree=12.8, formatted="Pisces 12°48’", lon=342.8),
            "ic": AnglePoint(id="ic", label="Imum Coeli", sign="Sagittarius", degree=10.5667, formatted="Sagittarius 10°34’", lon=250.5667),
        },
        houses=[HouseCusp(house=1, sign="Virgo", degree=12.8, formatted="Virgo 12°48’", lon=162.8)],
        bodies=[ChartBody(id="sun", label="Sun", classification="planet", sign="Aries", degree=28.65, formatted="Aries 28°39’", lon=28.65, house=8)],
        points=[],
        aspects=[],
        availability=Availability(core_complete=True, soft_missing=[]),
        traditional=TraditionalLayer(
            reference_date="2026-04-17",
            arabic_parts=[
                TraditionalPoint(
                    id="fortune",
                    label="Part of Fortune",
                    formula_key="fortune",
                    sign="Capricorn",
                    degree=10.0,
                    formatted="Capricorn 10°00’",
                    lon=280.0,
                    house=5,
                )
            ],
            profection=ProfectionSnapshot(
                reference_date="2026-04-17",
                current_age=46.0,
                completed_years=46,
                profection_house=11,
                activated_sign="Cancer",
                annual_lord=TraditionalRuler(id="moon", label="Moon"),
                rotation_degrees=1380.0,
                cycle_start_date="2026-04-17",
                cycle_end_date="2027-04-17",
            ),
        ),
    )


def test_build_apps_script_payload_embeds_chart_json():
    chart = build_sample_chart()
    request_payload = ChartExtractRequest(
        person_name="Sample",
        phone="010-1111-2222",
        email="sample@example.com",
        birth_date="2016-04-19",
        birth_time_local="15:20",
        birth_place_name="Yongin-si, South Korea",
        country_code="KR",
        latitude=37.2333,
        longitude=127.1833,
        report_preset="teen_growth_report",
        report_addons=["parenting", "wellbeing"],
        report_id="report-sample-chart",
        report_viewer_code="1234",
        report_product_code="teen_growth_report",
        report_payment_status="paid",
    )
    payload = build_apps_script_payload(chart, request_payload=request_payload)

    assert payload["record_id"] == "sample-chart"
    assert payload["chart_id"] == "sample-chart"
    assert payload["person_name"] == "Sample"
    assert payload["source_type"] == "computed_by_fastapi"
    assert payload["extraction_mode"] == "computed_by_swiss_ephemeris"
    assert payload["birth_date"] == "2016-04-19"
    assert payload["zodiac_type"] == "tropical"
    assert payload["house_system"] == "placidus"
    assert payload["core_complete"] is True
    assert payload["soft_missing_json"] == "[]"
    assert payload["warnings_json"] == "[]"
    assert "\"chart_id\": \"sample-chart\"" in payload["chart_json"]
    assert payload["report_preset"] == "teen_growth_report"
    assert payload["viewer_code"] == "1234"
    assert payload["product_code"] == "teen_growth_report"
    assert payload["payment_status"] == "paid"
    assert payload["report_request"]["preset"] == "teen_growth_report"
    assert payload["report_request"]["addons"] == ["parenting", "wellbeing"]
    assert payload["report_request"]["access"]["viewer_code"] == "1234"
    assert "\"preset\": \"teen_growth_report\"" in payload["report_request_json"]
    assert payload["chart"]["metadata"]["engine_name"] == "swiss_ephemeris"
    assert payload["chart"]["angles"]["asc"]["formatted"] == "Virgo 12°48’"


@pytest.mark.anyio
async def test_store_chart_record_returns_not_configured_without_url():
    chart = build_sample_chart()
    
    async def fake_upsert(*args, **kwargs):
        return ChartStorageResult(
            attempted=False,
            stored=False,
            destination="postgres",
            message="GOOGLE_APPS_SCRIPT_URL not configured",
        )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("app.services.chart_storage_service.upsert_chart_record_postgres", fake_upsert)
    try:
        result = await store_chart_record(chart, settings=build_settings(google_apps_script_url=None))
    finally:
        monkeypatch.undo()

    assert result.attempted is False
    assert result.stored is False
    assert result.message == "GOOGLE_APPS_SCRIPT_URL not configured"


@pytest.mark.anyio
async def test_store_chart_record_follows_redirects_and_accepts_json_success(monkeypatch):
    chart = build_sample_chart()
    captured: dict[str, object] = {}

    async def fake_upsert(*args, **kwargs):
        return ChartStorageResult(
            attempted=True,
            stored=True,
            destination="postgres",
            message="stored",
        )

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            captured["follow_redirects"] = kwargs.get("follow_redirects")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            captured["url"] = url
            captured["payload"] = json
            return Response(
                200,
                headers={"content-type": "application/json"},
                json={"ok": True, "sheet": "charts", "row_number": 2, "record_id": "sample-chart", "row_updated": False, "row_appended": True},
            )

    monkeypatch.setattr("app.services.chart_storage_service.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr("app.services.chart_storage_service.upsert_chart_record_postgres", fake_upsert)

    result = await store_chart_record(
        chart,
        settings=build_settings(),
    )

    assert captured["follow_redirects"] is True
    assert result.attempted is True
    assert result.stored is True
    assert result.status_code == 200
    assert result.message == "stored_both"
    assert result.record_id == "sample-chart"
    assert result.row_number == 2
    assert result.row_updated is False
    assert result.row_appended is True


@pytest.mark.anyio
async def test_store_chart_record_rejects_non_json_success_response(monkeypatch):
    chart = build_sample_chart()

    async def fake_upsert(*args, **kwargs):
        return ChartStorageResult(
            attempted=True,
            stored=True,
            destination="postgres",
            message="stored",
        )

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            return Response(
                200,
                headers={"content-type": "text/html"},
                text="<html><body>Moved Temporarily</body></html>",
            )

    monkeypatch.setattr("app.services.chart_storage_service.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr("app.services.chart_storage_service.upsert_chart_record_postgres", fake_upsert)

    result = await store_chart_record(
        chart,
        settings=build_settings(),
    )

    assert result.attempted is True
    assert result.stored is True
    assert result.status_code == 200
    assert result.message.startswith("stored_postgres_only; apps_script=apps_script_non_json_response")


def test_build_report_request_payload_defaults_to_adult_preset():
    chart = build_sample_chart()
    request = build_report_request_payload(chart)

    assert request["preset"] == "adult_deep_blueprint"
    assert request["addons"] == []
    assert request["access"]["viewer_code"] is None


def test_build_report_request_payload_includes_later_life_block_when_provided():
    chart = build_sample_chart()
    later_life = LaterLifeTimingLayer(
        reference_date="2026-04-17",
        current_age=45.25,
        age_phase="40-50",
        phase_windows=[LaterLifePhaseWindow(phase_label="40-50", start_age=40.0, end_age=50.0, start_date="2020-01-01", end_date="2030-01-01")],
        cycle_events=[
            LaterLifeCycleEvent(
                event_id="saturn_opposition_saturn_1",
                transit_body="Saturn",
                aspect_type="opposition",
                natal_target="Saturn",
                start_age=44.0,
                peak_age=45.0,
                end_age=46.0,
                start_date="2020-01-01",
                peak_date="2021-01-01",
                end_date="2022-01-01",
                phase_bucket="40-50",
                theme_tags=["reality-check"],
                event_status="current",
                years_to_peak=0.5,
                days_to_peak=182,
                is_within_active_window=True,
                priority_score=77.0,
            )
        ],
        active_cycle_events=[],
        upcoming_cycle_events=[],
        recent_cycle_events=[],
        primary_transition_event=None,
        top_theme_tags=["reality-check"],
    )

    request = build_report_request_payload(chart, later_life_timing=later_life)

    assert request["later_life"]["reference_date"] == "2026-04-17"
    assert request["later_life"]["age_phase"] == "40-50"
    assert request["later_life"]["cycle_events"][0]["event_id"] == "saturn_opposition_saturn_1"
    assert request["later_life"]["active_cycle_events"] == []
    assert request["later_life"]["upcoming_cycle_events"] == []
    assert request["later_life"]["primary_transition_event"] is None
    assert request["later_life"]["top_theme_tags"] == ["reality-check"]


def test_build_report_request_payload_includes_traditional_block_when_chart_has_it():
    chart = build_sample_chart()

    request = build_report_request_payload(chart)

    assert request["traditional"]["reference_date"] == "2026-04-17"
    assert request["traditional"]["arabic_parts"][0]["id"] == "fortune"
    assert request["traditional"]["profection"]["annual_lord"]["id"] == "moon"


def test_build_report_request_payload_keeps_plain_traditional_without_profection():
    chart = build_sample_chart()
    chart.traditional.reference_date = None
    chart.traditional.profection = None

    request = build_report_request_payload(chart)

    assert request["traditional"]["reference_date"] is None
    assert request["traditional"]["arabic_parts"][0]["id"] == "fortune"
    assert request["traditional"]["profection"] is None
