from __future__ import annotations

import httpx

from ..core.config import AppSettings, get_settings
from ..schemas import ChartStorageResult, NatalChartRecord


def build_apps_script_payload(chart: NatalChartRecord) -> dict[str, object]:
    return {
        "record_id": chart.metadata.chart_id,
        "chart_id": chart.metadata.chart_id,
        "engine_name": chart.metadata.engine_name,
        "status": chart.metadata.status,
        "source_type": "computed_by_fastapi",
        "extraction_mode": "computed_by_swiss_ephemeris",
        "classification": "computed_chart",
        "notes": "stored_from_api_extract_and_store",
        "birth_date": chart.input.birth_date,
        "birth_time_local": chart.input.birth_time_local,
        "timezone": chart.input.timezone,
        "birth_place_name": chart.input.birth_place_name,
        "country_code": chart.input.country_code,
        "latitude": chart.input.latitude,
        "longitude": chart.input.longitude,
        "provenance": {
            "source_type": "computed_by_fastapi",
            "extraction_mode": "computed_by_swiss_ephemeris",
            "engine_name": chart.metadata.engine_name,
        },
        "chart": chart.model_dump(mode="json"),
    }


async def store_chart_record(
    chart: NatalChartRecord,
    settings: AppSettings | None = None,
) -> ChartStorageResult:
    settings = settings or get_settings()
    if not settings.google_apps_script_url:
        return ChartStorageResult(
            attempted=False,
            stored=False,
            destination=None,
            message="GOOGLE_APPS_SCRIPT_URL not configured",
        )

    payload = build_apps_script_payload(chart)
    try:
        async with httpx.AsyncClient(
            timeout=settings.google_apps_script_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.post(settings.google_apps_script_url, json=payload)
        stored = False
        message = response.text[:500] or "apps_script_request_failed"

        try:
            payload_json = response.json()
        except ValueError:
            payload_json = None

        if isinstance(payload_json, dict):
            if payload_json.get("ok") is True and payload_json.get("row_number"):
                stored = True
                message = "stored"
            elif payload_json.get("ok") is False:
                message = str(payload_json.get("error") or payload_json)
            else:
                message = str(payload_json)
        elif not response.is_success:
            message = response.text[:500] or "apps_script_request_failed"
        else:
            message = "apps_script_non_json_response"

        return ChartStorageResult(
            attempted=True,
            stored=stored,
            destination=settings.google_apps_script_url,
            status_code=response.status_code,
            message=message,
            record_id=payload_json.get("record_id") if isinstance(payload_json, dict) else None,
            row_number=payload_json.get("row_number") if isinstance(payload_json, dict) else None,
            row_updated=payload_json.get("row_updated") if isinstance(payload_json, dict) else None,
            row_appended=payload_json.get("row_appended") if isinstance(payload_json, dict) else None,
        )
    except Exception as exc:
        return ChartStorageResult(
            attempted=True,
            stored=False,
            destination=settings.google_apps_script_url,
            message=str(exc),
        )
