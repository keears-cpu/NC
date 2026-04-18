from __future__ import annotations

from fastapi.testclient import TestClient

from app.schemas import (
    AnglePoint,
    Availability,
    ChartBody,
    ChartInput,
    ChartMetadata,
    ChartSettings,
    HouseCusp,
    LaterLifeChartExtractRequest,
    LaterLifeCycleEvent,
    LaterLifePhaseWindow,
    LaterLifeTimingLayer,
    NatalChartRecord,
    ProfectionSnapshot,
    ChartStorageResult,
    TraditionalLayer,
    TraditionalPoint,
    TraditionalRuler,
)


def build_sample_chart() -> NatalChartRecord:
    return NatalChartRecord(
        metadata=ChartMetadata(
            chart_id="later-life-route",
            engine_name="swiss_ephemeris",
            status="ready",
            birth_datetime_utc="1980-04-17T00:00:00+00:00",
            jd_ut=2444340.5,
            warnings=[],
        ),
        input=ChartInput(
            person_name="Sample",
            birth_date="1980-04-17",
            birth_time_local="00:00",
            timezone="UTC",
            birth_place_name="Seoul, Korea",
            country_code="KR",
            latitude=37.5665,
            longitude=126.9780,
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


def test_extract_later_life_route_returns_timing_layer(monkeypatch):
    from app import main
    from app.api.routes import chart_extract
    from app.core.config import AppSettings

    sample_chart = build_sample_chart()
    sample_timing = LaterLifeTimingLayer(
        reference_date="2026-04-17",
        current_age=46.0,
        age_phase="40-50",
        phase_windows=[LaterLifePhaseWindow(phase_label="40-50", start_age=40.0, end_age=50.0, start_date="2020-01-01", end_date="2030-01-01")],
        cycle_events=[
            LaterLifeCycleEvent(
                event_id="jupiter_conjunction_jupiter_1",
                transit_body="Jupiter",
                aspect_type="conjunction",
                natal_target="Jupiter",
                start_age=45.0,
                peak_age=46.0,
                end_age=47.0,
                start_date="2025-01-01",
                peak_date="2026-01-01",
                end_date="2027-01-01",
                phase_bucket="40-50",
                theme_tags=["growth"],
                event_status="current",
                years_to_peak=0.5,
                days_to_peak=182,
                is_within_active_window=True,
                priority_score=98.0,
            )
        ],
        active_cycle_events=[],
        upcoming_cycle_events=[],
        recent_cycle_events=[],
        primary_transition_event=None,
        top_theme_tags=["growth"],
    )

    monkeypatch.setattr(chart_extract, "build_chart_record", lambda payload, reference_date=None: sample_chart)
    monkeypatch.setattr(chart_extract, "build_later_life_timing_layer", lambda chart, reference_date=None: sample_timing)
    monkeypatch.setattr(main, "get_settings", lambda: AppSettings(
        google_apps_script_url="https://script.google.com/macros/s/fake/exec",
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
    ))

    async def noop_ensure_database_schema(settings=None):
        return None

    monkeypatch.setattr(main, "ensure_database_schema", noop_ensure_database_schema)

    with TestClient(main.app) as client:
        response = client.post(
            "/api/chart/extract-later-life",
            json={
                "birth_date": "1980-04-17",
                "birth_time_local": "00:00",
                "timezone": "UTC",
                "birth_place_name": "Seoul, Korea",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "reference_date": "2026-04-17",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["chart"]["metadata"]["birth_datetime_utc"] == "1980-04-17T00:00:00+00:00"
    assert body["later_life"]["reference_date"] == "2026-04-17"
    assert body["later_life"]["age_phase"] == "40-50"
    assert body["later_life"]["cycle_events"][0]["event_id"] == "jupiter_conjunction_jupiter_1"
    assert "active_cycle_events" in body["later_life"]
    assert "primary_transition_event" in body["later_life"]
    assert body["later_life"]["top_theme_tags"] == ["growth"]


def test_extract_route_keeps_base_shape_without_later_life(monkeypatch):
    from app import main
    from app.api.routes import chart_extract
    from app.core.config import AppSettings

    sample_chart = build_sample_chart()
    sample_chart.traditional.reference_date = None
    sample_chart.traditional.profection = None
    monkeypatch.setattr(chart_extract, "build_chart_record", lambda payload, reference_date=None: sample_chart)
    monkeypatch.setattr(main, "get_settings", lambda: AppSettings(
        google_apps_script_url="https://script.google.com/macros/s/fake/exec",
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
    ))

    async def noop_ensure_database_schema(settings=None):
        return None

    monkeypatch.setattr(main, "ensure_database_schema", noop_ensure_database_schema)

    with TestClient(main.app) as client:
        response = client.post(
            "/api/chart/extract",
            json={
                "birth_date": "1980-04-17",
                "birth_time_local": "00:00",
                "timezone": "UTC",
                "birth_place_name": "Seoul, Korea",
                "latitude": 37.5665,
                "longitude": 126.9780,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["birth_datetime_utc"] == "1980-04-17T00:00:00+00:00"
    assert body["metadata"]["jd_ut"] == 2444340.5
    assert "later_life" not in body
    assert body["traditional"]["arabic_parts"][0]["id"] == "fortune"
    assert body["traditional"]["reference_date"] is None
    assert body["traditional"]["profection"] is None
    assert body["input"]["birth_date"] == "1980-04-17"
    assert body["angles"]["asc"]["formatted"] == "Virgo 12°48’"


def test_later_life_request_accepts_integration_report_preset():
    request = LaterLifeChartExtractRequest(
        birth_date="1980-04-17",
        birth_time_local="00:00",
        timezone="UTC",
        birth_place_name="Seoul, Korea",
        latitude=37.5665,
        longitude=126.9780,
        report_preset="later_life_integration_report",
        reference_date="2026-04-17",
    )

    assert request.report_preset == "later_life_integration_report"


def test_extract_later_life_rejects_malformed_reference_date(monkeypatch):
    from app import main
    from app.api.routes import chart_extract
    from app.core.config import AppSettings

    sample_chart = build_sample_chart()
    monkeypatch.setattr(chart_extract, "build_chart_record", lambda payload, reference_date=None: sample_chart)
    monkeypatch.setattr(main, "get_settings", lambda: AppSettings(
        google_apps_script_url="https://script.google.com/macros/s/fake/exec",
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
    ))

    async def noop_ensure_database_schema(settings=None):
        return None

    monkeypatch.setattr(main, "ensure_database_schema", noop_ensure_database_schema)

    with TestClient(main.app) as client:
        response = client.post(
            "/api/chart/extract-later-life",
            json={
                "birth_date": "1980-04-17",
                "birth_time_local": "00:00",
                "timezone": "UTC",
                "birth_place_name": "Seoul, Korea",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "reference_date": "2026-13-01",
            },
        )

    assert response.status_code == 422
    assert "reference_date" in response.text


def test_extract_later_life_rejects_under_40_request(monkeypatch):
    from app import main
    from app.api.routes import chart_extract
    from app.core.config import AppSettings

    sample_chart = build_sample_chart()
    monkeypatch.setattr(chart_extract, "build_chart_record", lambda payload, reference_date=None: sample_chart)
    monkeypatch.setattr(main, "get_settings", lambda: AppSettings(
        google_apps_script_url="https://script.google.com/macros/s/fake/exec",
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
    ))

    async def noop_ensure_database_schema(settings=None):
        return None

    monkeypatch.setattr(main, "ensure_database_schema", noop_ensure_database_schema)

    with TestClient(main.app) as client:
        response = client.post(
            "/api/chart/extract-later-life",
            json={
                "birth_date": "2010-04-17",
                "birth_time_local": "00:00",
                "timezone": "UTC",
                "birth_place_name": "Seoul, Korea",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "reference_date": "2026-04-17",
            },
        )

    assert response.status_code == 422
    assert "later-life requests require current_age >= 40" in response.text


def test_extract_later_life_rejects_unknown_timezone(monkeypatch):
    from app import main
    from app.api.routes import chart_extract
    from app.core.config import AppSettings

    sample_chart = build_sample_chart()
    monkeypatch.setattr(chart_extract, "build_chart_record", lambda payload, reference_date=None: sample_chart)
    monkeypatch.setattr(main, "get_settings", lambda: AppSettings(
        google_apps_script_url="https://script.google.com/macros/s/fake/exec",
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
    ))

    async def noop_ensure_database_schema(settings=None):
        return None

    monkeypatch.setattr(main, "ensure_database_schema", noop_ensure_database_schema)

    with TestClient(main.app) as client:
        response = client.post(
            "/api/chart/extract-later-life",
            json={
                "birth_date": "1980-04-17",
                "birth_time_local": "00:00",
                "timezone": "Mars/Phobos",
                "birth_place_name": "Seoul, Korea",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "reference_date": "2026-04-17",
            },
        )

    assert response.status_code == 422
    assert "timezone" in response.text


def test_extract_and_store_later_life_passes_timing_into_storage(monkeypatch):
    from app import main
    from app.api.routes import chart_extract
    from app.core.config import AppSettings

    sample_chart = build_sample_chart()
    sample_timing = LaterLifeTimingLayer(
        reference_date="2026-04-17",
        current_age=46.0,
        age_phase="40-50",
        phase_windows=[LaterLifePhaseWindow(phase_label="40-50", start_age=40.0, end_age=50.0, start_date="2020-01-01", end_date="2030-01-01")],
        cycle_events=[],
        active_cycle_events=[],
        upcoming_cycle_events=[],
        recent_cycle_events=[],
        primary_transition_event=None,
        top_theme_tags=[],
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(chart_extract, "build_chart_record", lambda payload, reference_date=None: sample_chart)
    monkeypatch.setattr(chart_extract, "build_later_life_timing_layer", lambda chart, reference_date=None: sample_timing)

    async def fake_store_chart_record(chart, request_payload=None, later_life_timing=None, settings=None):
        captured["later_life_timing"] = later_life_timing
        return ChartStorageResult(
            attempted=True,
            stored=True,
            destination="apps_script",
            message="stored",
        )

    monkeypatch.setattr(chart_extract, "store_chart_record", fake_store_chart_record)
    monkeypatch.setattr(main, "get_settings", lambda: AppSettings(
        google_apps_script_url="https://script.google.com/macros/s/fake/exec",
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
    ))

    async def noop_ensure_database_schema(settings=None):
        return None

    monkeypatch.setattr(main, "ensure_database_schema", noop_ensure_database_schema)

    with TestClient(main.app) as client:
        response = client.post(
            "/api/chart/extract-and-store",
            json={
                "birth_date": "1980-04-17",
                "birth_time_local": "00:00",
                "timezone": "UTC",
                "birth_place_name": "Seoul, Korea",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "report_preset": "later_life_integration_report",
                "reference_date": "2026-04-17",
            },
        )

    assert response.status_code == 200
    assert captured["later_life_timing"] is sample_timing


def test_extract_and_store_under_40_general_request_still_passes(monkeypatch):
    from app import main
    from app.api.routes import chart_extract
    from app.core.config import AppSettings

    sample_chart = build_sample_chart()
    sample_chart.traditional.reference_date = None
    sample_chart.traditional.profection = None
    captured: dict[str, object] = {}

    monkeypatch.setattr(chart_extract, "build_chart_record", lambda payload, reference_date=None: sample_chart)

    async def fake_store_chart_record(chart, request_payload=None, later_life_timing=None, settings=None):
        captured["request_payload"] = request_payload
        captured["later_life_timing"] = later_life_timing
        return ChartStorageResult(
            attempted=True,
            stored=True,
            destination="apps_script",
            message="stored",
        )

    monkeypatch.setattr(chart_extract, "store_chart_record", fake_store_chart_record)
    monkeypatch.setattr(main, "get_settings", lambda: AppSettings(
        google_apps_script_url="https://script.google.com/macros/s/fake/exec",
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
    ))

    async def noop_ensure_database_schema(settings=None):
        return None

    monkeypatch.setattr(main, "ensure_database_schema", noop_ensure_database_schema)

    with TestClient(main.app) as client:
        response = client.post(
            "/api/chart/extract-and-store",
            json={
                "birth_date": "2016-04-17",
                "birth_time_local": "00:00",
                "timezone": "UTC",
                "birth_place_name": "Seoul, Korea",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "report_preset": "teen_growth_report",
            },
        )

    assert response.status_code == 200
    assert response.json()["chart"]["traditional"]["reference_date"] is None
    assert response.json()["chart"]["traditional"]["profection"] is None
    assert captured["request_payload"].report_preset == "teen_growth_report"
    assert captured["later_life_timing"] is None
