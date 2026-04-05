from __future__ import annotations

import json

from ..schemas import ChartExtractRequest, NatalChartRecord


def build_report_request_payload(
    chart: NatalChartRecord,
    request_payload: ChartExtractRequest | None = None,
) -> dict[str, object]:
    return {
        "chart": chart.model_dump(mode="json"),
        "preset": request_payload.report_preset if request_payload and request_payload.report_preset else "adult_deep_blueprint",
        "addons": request_payload.report_addons if request_payload else [],
        "options": {
            "language": "ko-KR",
            "tone": "parent_friendly",
            "format": "both",
            "audience": "parent",
        },
        "access": {
            "report_id": request_payload.report_id if request_payload else None,
            "viewer_code": request_payload.report_viewer_code if request_payload else None,
            "product_code": request_payload.report_product_code if request_payload else None,
            "payment_status": request_payload.report_payment_status if request_payload else None,
        },
    }


def build_apps_script_payload(
    chart: NatalChartRecord,
    request_payload: ChartExtractRequest | None = None,
) -> dict[str, object]:
    chart_json = chart.model_dump(mode="json")
    report_request = build_report_request_payload(chart, request_payload=request_payload)
    return {
        "record_id": chart.metadata.chart_id,
        "chart_id": chart.metadata.chart_id,
        "engine_name": chart.metadata.engine_name,
        "status": chart.metadata.status,
        "person_name": chart.input.person_name,
        "phone": request_payload.phone if request_payload else None,
        "email": request_payload.email if request_payload else None,
        "counselor_code": request_payload.counselor_code if request_payload else None,
        "tester_local_id": request_payload.tester_local_id if request_payload else None,
        "report_preset": request_payload.report_preset if request_payload else None,
        "report_addons_json": json.dumps(request_payload.report_addons if request_payload else [], ensure_ascii=False),
        "report_id": request_payload.report_id if request_payload else None,
        "viewer_code": request_payload.report_viewer_code if request_payload else None,
        "product_code": request_payload.report_product_code if request_payload else None,
        "payment_status": request_payload.report_payment_status if request_payload else None,
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
        "report_request_json": json.dumps(report_request, ensure_ascii=False),
        "report_payload_json": None,
        "report_html": None,
        "report_html_url": None,
        "chart_svg": None,
        "chart_svg_updated_at": None,
        "provenance": {
            "source_type": "computed_by_fastapi",
            "extraction_mode": "computed_by_swiss_ephemeris",
        },
    }
