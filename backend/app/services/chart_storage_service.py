from __future__ import annotations

import json
import re

import httpx

from ..core.config import AppSettings, get_settings
from ..schemas import ChartStorageResult, NatalChartRecord, StoredChartListItem, StoredChartListResponse


def build_apps_script_payload(chart: NatalChartRecord) -> dict[str, object]:
    chart_json = chart.model_dump(mode="json")
    return {
        "record_id": chart.metadata.chart_id,
        "chart_id": chart.metadata.chart_id,
        "engine_name": chart.metadata.engine_name,
        "status": chart.metadata.status,
        "person_name": chart.input.person_name,
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
        "zodiac_type": chart.settings.zodiac_type,
        "house_system": chart.settings.house_system,
        "node_mode": chart.settings.node_mode,
        "lilith_mode": chart.settings.lilith_mode,
        "core_complete": chart.availability.core_complete,
        "soft_missing_json": json.dumps(chart.availability.soft_missing, ensure_ascii=False),
        "warnings_json": json.dumps(chart.metadata.warnings, ensure_ascii=False),
        "chart_json": json.dumps(chart_json, ensure_ascii=False),
        "provenance": {
            "source_type": "computed_by_fastapi",
            "extraction_mode": "computed_by_swiss_ephemeris",
            "engine_name": chart.metadata.engine_name,
        },
        "chart": chart_json,
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


def _coerce_stored_chart_item(raw: dict[str, object]) -> StoredChartListItem | None:
    record_id = str(raw.get("record_id") or raw.get("chart_id") or "").strip()
    if not record_id:
        return None

    chart_value = raw.get("chart") or raw.get("chart_json")
    chart: NatalChartRecord | None = None
    if isinstance(chart_value, str):
        try:
            chart = NatalChartRecord.model_validate_json(chart_value)
        except Exception:
            chart = None
    elif isinstance(chart_value, dict):
        try:
            chart = NatalChartRecord.model_validate(chart_value)
        except Exception:
            chart = None

    birth_date = str(raw.get("birth_date") or "").strip()
    birth_time_local = raw.get("birth_time_local")
    if chart and not birth_date:
        birth_date = chart.input.birth_date
    if chart and not birth_time_local:
        birth_time_local = chart.input.birth_time_local

    if not birth_date:
        return None

    birth_place_name = str(raw.get("birth_place_name") or (chart.input.birth_place_name if chart else "") or "").strip() or None
    if birth_place_name and ("GMT" in birth_place_name or birth_place_name.startswith("Sat ")):
        birth_place_name = None
    if not birth_place_name:
        created_at = str(raw.get("created_at") or raw.get("timestamp") or "").strip()
        birth_place_name = _recover_birth_place_from_created_at(created_at)

    return StoredChartListItem(
        record_id=record_id,
        person_name=str(raw.get("person_name") or raw.get("name") or (chart.input.person_name if chart else "") or "").strip() or None,
        birth_date=birth_date,
        birth_time_local=str(birth_time_local).strip() if birth_time_local else None,
        birth_place_name=birth_place_name,
        email=str(raw.get("email") or "").strip() or None,
        created_at=str(raw.get("created_at") or raw.get("timestamp") or "").strip() or None,
        chart=chart,
    )


def _recover_birth_place_from_created_at(created_at: str) -> str | None:
    if not created_at:
        return None

    match = re.match(r"^\d{4}-\d{2}-\d{2}(?:[T-]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z?)?-(.+)$", created_at)
    if not match:
        return None

    slug = match.group(1).strip("-_ ").lower()
    if not slug:
        return None

    parts = [part for part in slug.split("_") if part]
    if not parts:
        return None

    words: list[str] = []
    for part in parts:
        if part in {"kr", "korea"}:
            words.append("Korea")
        elif part in {"south", "north"}:
            words.append(part.capitalize())
        elif part == "usa":
            words.append("USA")
        else:
            words.append(part.capitalize())

    if len(words) >= 2 and words[-2:] == ["South", "Korea"]:
        return f'{" ".join(words[:-2])}, South Korea' if words[:-2] else "South Korea"

    return " ".join(words)


async def fetch_stored_charts(
    settings: AppSettings | None = None,
    limit: int = 100,
) -> StoredChartListResponse:
    settings = settings or get_settings()
    if not settings.google_apps_script_url:
        return StoredChartListResponse(ok=False, items=[], source=None, message="GOOGLE_APPS_SCRIPT_URL not configured")

    try:
        async with httpx.AsyncClient(
            timeout=settings.google_apps_script_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                settings.google_apps_script_url,
                params={"action": "list", "limit": str(limit)},
            )
    except Exception as exc:
        return StoredChartListResponse(ok=False, items=[], source=settings.google_apps_script_url, message=str(exc))

    try:
        payload = response.json()
    except ValueError:
        return StoredChartListResponse(ok=False, items=[], source=settings.google_apps_script_url, message="apps_script_non_json_response")

    raw_items: list[dict[str, object]] = []
    if isinstance(payload, dict):
        for key in ("items", "charts", "rows", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                raw_items = [item for item in value if isinstance(item, dict)]
                break
    elif isinstance(payload, list):
        raw_items = [item for item in payload if isinstance(item, dict)]

    items = [item for item in (_coerce_stored_chart_item(raw) for raw in raw_items) if item is not None]
    items.sort(key=lambda item: f"{item.birth_date} {item.birth_time_local or ''}", reverse=True)
    return StoredChartListResponse(
        ok=response.is_success,
        items=items,
        source=settings.google_apps_script_url,
        message=None if response.is_success else response.text[:500],
    )
