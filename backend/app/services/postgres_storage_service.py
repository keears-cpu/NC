from __future__ import annotations

import json

from sqlalchemy import text

from ..core.config import AppSettings, get_settings
from ..core.database import ensure_database_schema, get_engine
from ..schemas import ChartExtractRequest, ChartStorageResult, NatalChartRecord
from .storage_payloads import build_apps_script_payload


async def upsert_chart_record_postgres(
    chart: NatalChartRecord,
    request_payload: ChartExtractRequest | None = None,
    settings: AppSettings | None = None,
) -> ChartStorageResult:
    settings = settings or get_settings()
    engine = get_engine(settings=settings)
    if engine is None:
        return ChartStorageResult(
            attempted=False,
            stored=False,
            destination="postgres",
            message="DATABASE_URL not configured",
        )

    await ensure_database_schema(settings=settings)

    payload = build_apps_script_payload(chart, request_payload=request_payload)
    chart_params = {
        "record_id": payload.get("record_id"),
        "chart_id": payload.get("chart_id"),
        "engine_name": payload.get("engine_name"),
        "status": payload.get("status"),
        "source_type": payload.get("source_type"),
        "extraction_mode": payload.get("extraction_mode"),
        "classification": payload.get("classification"),
        "notes": payload.get("notes"),
        "person_name": payload.get("person_name"),
        "phone": payload.get("phone"),
        "email": payload.get("email"),
        "counselor_code": payload.get("counselor_code"),
        "tester_local_id": payload.get("tester_local_id"),
        "birth_date": payload.get("birth_date"),
        "birth_time_local": payload.get("birth_time_local"),
        "timezone": payload.get("timezone"),
        "birth_place_name": payload.get("birth_place_name"),
        "country_code": payload.get("country_code"),
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "zodiac_type": payload.get("zodiac_type"),
        "house_system": payload.get("house_system"),
        "node_mode": payload.get("node_mode"),
        "lilith_mode": payload.get("lilith_mode"),
        "fortune_formula": chart.settings.fortune_formula,
        "core_complete": payload.get("core_complete"),
        "soft_missing_json": payload.get("soft_missing_json") or json.dumps([]),
        "warnings_json": payload.get("warnings_json") or json.dumps([]),
        "chart_json": payload.get("chart_json") or json.dumps(chart.model_dump(mode="json"), ensure_ascii=False),
        "chart_svg": payload.get("chart_svg"),
        "chart_svg_updated_at": payload.get("chart_svg_updated_at"),
        "report_preset": payload.get("report_preset"),
        "report_addons_json": payload.get("report_addons_json") or json.dumps([]),
        "report_id": payload.get("report_id"),
        "viewer_code": payload.get("viewer_code"),
        "product_code": payload.get("product_code"),
        "payment_status": payload.get("payment_status"),
        "report_request_json": payload.get("report_request_json") or json.dumps({}),
        "report_payload_json": payload.get("report_payload_json"),
        "report_html": payload.get("report_html"),
        "report_html_url": payload.get("report_html_url"),
    }

    report_params = {
        "record_id": chart_params["record_id"],
        "report_preset": chart_params["report_preset"],
        "report_addons_json": chart_params["report_addons_json"],
        "report_id": chart_params["report_id"],
        "viewer_code": chart_params["viewer_code"],
        "product_code": chart_params["product_code"],
        "payment_status": chart_params["payment_status"],
        "report_request_json": chart_params["report_request_json"],
        "report_payload_json": chart_params["report_payload_json"],
        "report_html": chart_params["report_html"],
        "report_html_url": chart_params["report_html_url"],
    }

    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    insert into charts (
                        record_id, chart_id, engine_name, status, source_type, extraction_mode, classification, notes,
                        person_name, phone, email, counselor_code, tester_local_id,
                        birth_date, birth_time_local, timezone, birth_place_name, country_code, latitude, longitude,
                        zodiac_type, house_system, node_mode, lilith_mode, fortune_formula,
                        core_complete, soft_missing_json, warnings_json, chart_json, chart_svg, chart_svg_updated_at,
                        report_preset, report_addons_json, report_id, viewer_code, product_code, payment_status,
                        report_request_json, report_payload_json, report_html, report_html_url
                    ) values (
                        :record_id, :chart_id, :engine_name, :status, :source_type, :extraction_mode, :classification, :notes,
                        :person_name, :phone, :email, :counselor_code, :tester_local_id,
                        :birth_date, :birth_time_local, :timezone, :birth_place_name, :country_code, :latitude, :longitude,
                        :zodiac_type, :house_system, :node_mode, :lilith_mode, :fortune_formula,
                        :core_complete, cast(:soft_missing_json as jsonb), cast(:warnings_json as jsonb), cast(:chart_json as jsonb), :chart_svg, cast(:chart_svg_updated_at as timestamptz),
                        :report_preset, cast(:report_addons_json as jsonb), :report_id, :viewer_code, :product_code, :payment_status,
                        cast(:report_request_json as jsonb), cast(:report_payload_json as jsonb), :report_html, :report_html_url
                    )
                    on conflict (record_id) do update set
                        updated_at = now(),
                        chart_id = excluded.chart_id,
                        engine_name = excluded.engine_name,
                        status = excluded.status,
                        source_type = excluded.source_type,
                        extraction_mode = excluded.extraction_mode,
                        classification = excluded.classification,
                        notes = excluded.notes,
                        person_name = excluded.person_name,
                        phone = excluded.phone,
                        email = excluded.email,
                        counselor_code = excluded.counselor_code,
                        tester_local_id = excluded.tester_local_id,
                        birth_date = excluded.birth_date,
                        birth_time_local = excluded.birth_time_local,
                        timezone = excluded.timezone,
                        birth_place_name = excluded.birth_place_name,
                        country_code = excluded.country_code,
                        latitude = excluded.latitude,
                        longitude = excluded.longitude,
                        zodiac_type = excluded.zodiac_type,
                        house_system = excluded.house_system,
                        node_mode = excluded.node_mode,
                        lilith_mode = excluded.lilith_mode,
                        fortune_formula = excluded.fortune_formula,
                        core_complete = excluded.core_complete,
                        soft_missing_json = excluded.soft_missing_json,
                        warnings_json = excluded.warnings_json,
                        chart_json = excluded.chart_json,
                        chart_svg = coalesce(excluded.chart_svg, charts.chart_svg),
                        chart_svg_updated_at = coalesce(excluded.chart_svg_updated_at, charts.chart_svg_updated_at),
                        report_preset = excluded.report_preset,
                        report_addons_json = excluded.report_addons_json,
                        report_id = excluded.report_id,
                        viewer_code = excluded.viewer_code,
                        product_code = excluded.product_code,
                        payment_status = excluded.payment_status,
                        report_request_json = excluded.report_request_json,
                        report_payload_json = coalesce(excluded.report_payload_json, charts.report_payload_json),
                        report_html = coalesce(excluded.report_html, charts.report_html),
                        report_html_url = coalesce(excluded.report_html_url, charts.report_html_url)
                    """
                ),
                chart_params,
            )
            await connection.execute(
                text(
                    """
                    insert into reports (
                        record_id, report_preset, report_addons_json, report_id, viewer_code, product_code,
                        payment_status, report_request_json, report_payload_json, report_html, report_html_url
                    ) values (
                        :record_id, :report_preset, cast(:report_addons_json as jsonb), :report_id, :viewer_code, :product_code,
                        :payment_status, cast(:report_request_json as jsonb), cast(:report_payload_json as jsonb), :report_html, :report_html_url
                    )
                    on conflict (record_id) do update set
                        updated_at = now(),
                        report_preset = excluded.report_preset,
                        report_addons_json = excluded.report_addons_json,
                        report_id = excluded.report_id,
                        viewer_code = excluded.viewer_code,
                        product_code = excluded.product_code,
                        payment_status = excluded.payment_status,
                        report_request_json = excluded.report_request_json,
                        report_payload_json = coalesce(excluded.report_payload_json, reports.report_payload_json),
                        report_html = coalesce(excluded.report_html, reports.report_html),
                        report_html_url = coalesce(excluded.report_html_url, reports.report_html_url)
                    """
                ),
                report_params,
            )

        return ChartStorageResult(
            attempted=True,
            stored=True,
            destination="postgres",
            message="stored",
            record_id=str(chart_params["record_id"]),
        )
    except Exception as exc:
        return ChartStorageResult(
            attempted=True,
            stored=False,
            destination="postgres",
            message=str(exc),
            record_id=str(chart_params["record_id"]),
        )


async def update_chart_artwork_postgres(
    record_id: str,
    chart_svg: str,
    chart_svg_updated_at: str | None = None,
    settings: AppSettings | None = None,
) -> ChartStorageResult:
    settings = settings or get_settings()
    engine = get_engine(settings=settings)
    if engine is None:
        return ChartStorageResult(
            attempted=False,
            stored=False,
            destination="postgres",
            message="DATABASE_URL not configured",
            record_id=record_id,
        )

    await ensure_database_schema(settings=settings)

    try:
        async with engine.begin() as connection:
            result = await connection.execute(
                text(
                    """
                    update charts
                    set
                        updated_at = now(),
                        chart_svg = :chart_svg,
                        chart_svg_updated_at = cast(:chart_svg_updated_at as timestamptz)
                    where record_id = :record_id
                    """
                ),
                {
                    "record_id": record_id,
                    "chart_svg": chart_svg,
                    "chart_svg_updated_at": chart_svg_updated_at,
                },
            )

        updated = (result.rowcount or 0) > 0
        return ChartStorageResult(
            attempted=True,
            stored=updated,
            destination="postgres",
            message="stored" if updated else "record_not_found",
            record_id=record_id,
        )
    except Exception as exc:
        return ChartStorageResult(
            attempted=True,
            stored=False,
            destination="postgres",
            message=str(exc),
            record_id=record_id,
        )


async def fetch_chart_record_postgres(
    record_id: str,
    settings: AppSettings | None = None,
) -> dict[str, object] | None:
    settings = settings or get_settings()
    engine = get_engine(settings=settings)
    if engine is None:
        return None

    await ensure_database_schema(settings=settings)

    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    """
                    select
                        record_id, chart_id, engine_name, status, source_type, extraction_mode, classification, notes,
                        person_name, phone, email, counselor_code, tester_local_id,
                        birth_date, birth_time_local, timezone, birth_place_name, country_code, latitude, longitude,
                        zodiac_type, house_system, node_mode, lilith_mode, fortune_formula,
                        core_complete, soft_missing_json, warnings_json, chart_json, chart_svg, chart_svg_updated_at,
                        report_preset, report_addons_json, report_id, viewer_code, product_code, payment_status,
                        report_request_json, report_payload_json, report_html, report_html_url,
                        created_at, updated_at
                    from charts
                    where record_id = :record_id
                    """
                ),
                {"record_id": record_id},
            )
            row = result.mappings().first()
    except Exception:
        return None

    if not row:
        return None

    raw = dict(row)
    raw["chart"] = raw.get("chart_json")
    raw["report_request"] = raw.get("report_request_json")
    raw["report_payload"] = raw.get("report_payload_json")
    return raw
