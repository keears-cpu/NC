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
    NatalChartRecord,
    ChartExtractRequest,
)
from app.services.chart_storage_service import build_apps_script_payload, build_report_request_payload, store_chart_record


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
    result = await store_chart_record(chart, settings=AppSettings(google_apps_script_url=None, google_apps_script_timeout_seconds=2.0))

    assert result.attempted is False
    assert result.stored is False
    assert result.message == "GOOGLE_APPS_SCRIPT_URL not configured"


@pytest.mark.anyio
async def test_store_chart_record_follows_redirects_and_accepts_json_success(monkeypatch):
    chart = build_sample_chart()
    captured: dict[str, object] = {}

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

    result = await store_chart_record(
        chart,
        settings=AppSettings(
            google_apps_script_url="https://script.google.com/macros/s/fake/exec",
            google_apps_script_timeout_seconds=2.0,
        ),
    )

    assert captured["follow_redirects"] is True
    assert result.attempted is True
    assert result.stored is True
    assert result.status_code == 200
    assert result.message == "stored"
    assert result.record_id == "sample-chart"
    assert result.row_number == 2
    assert result.row_updated is False
    assert result.row_appended is True


@pytest.mark.anyio
async def test_store_chart_record_rejects_non_json_success_response(monkeypatch):
    chart = build_sample_chart()

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

    result = await store_chart_record(
        chart,
        settings=AppSettings(
            google_apps_script_url="https://script.google.com/macros/s/fake/exec",
            google_apps_script_timeout_seconds=2.0,
        ),
    )

    assert result.attempted is True
    assert result.stored is False
    assert result.status_code == 200
    assert result.message == "apps_script_non_json_response"


def test_build_report_request_payload_defaults_to_adult_preset():
    chart = build_sample_chart()
    request = build_report_request_payload(chart)

    assert request["preset"] == "adult_deep_blueprint"
    assert request["addons"] == []
    assert request["access"]["viewer_code"] is None
