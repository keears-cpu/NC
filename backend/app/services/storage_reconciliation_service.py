from __future__ import annotations

import json
from collections import Counter

from sqlalchemy import text

from ..core.config import AppSettings, get_settings
from ..core.database import get_engine
from ..schemas import StoredChartListItem
from .chart_storage_service import fetch_stored_charts
from .storage_audit_service import get_storage_audit

RECONCILIATION_FIELDS = (
    ("chart_id", "chart_id", "chart_id"),
    ("report_id", "report_id", "report_id"),
    ("viewer_code", "viewer_code", "viewer_code"),
    ("product_code", "product_code", "product_code"),
    ("payment_status", "payment_status", "payment_status"),
    ("report_request_json", "report_request_json", "report_request_json"),
    ("report_payload_json", "report_payload_json", "report_payload_json"),
    ("report_html", "report_html", "report_html"),
    ("report_html_url", "report_html_url", "report_html_url"),
    ("chart_svg", "chart_svg", "chart_svg"),
)


async def reconcile_storage(
    settings: AppSettings | None = None,
    limit: int = 100,
) -> dict[str, object]:
    settings = settings or get_settings()
    audit = await get_storage_audit(settings=settings)
    database = audit["database"]

    if not database["reachability_gate_passed"]:
        return _build_blocked_response(
            audit=audit,
            status="blocked",
            blocking_reason=str(database["blocking_reason"] or database["message"] or "database_reachability_gate_failed"),
            next_action=str(database["next_action"] or "DATABASE_URL와 연결 상태를 점검한 뒤 다시 시도하세요."),
            limit=limit,
        )

    apps_script_result = await fetch_stored_charts(settings=settings, limit=limit)
    if not apps_script_result.ok and not apps_script_result.items:
        return _build_blocked_response(
            audit=audit,
            status="blocked",
            blocking_reason=str(apps_script_result.message or "apps_script_unreachable"),
            next_action="Apps Script current record bus를 복구한 뒤 다시 reconcile 하세요.",
            limit=limit,
        )

    postgres_rows, postgres_error = await _fetch_postgres_rows(settings=settings, limit=limit)
    if postgres_error is not None:
        return _build_blocked_response(
            audit=audit,
            status="blocked",
            blocking_reason=postgres_error,
            next_action="Postgres mirror와 foundation schema를 점검한 뒤 다시 reconcile 하세요.",
            limit=limit,
        )

    apps_script_rows = [_item_to_record_dict(item) for item in apps_script_result.items]
    comparison = _compare_rows(apps_script_rows=apps_script_rows, postgres_rows=postgres_rows)
    summary = _build_summary(comparison, limit=limit)

    return {
        "ok": True,
        "status": "ok",
        "scope": "apps_script_vs_postgres",
        "sample_limit": limit,
        "reachability_gate_passed": True,
        "blocking_reason": None,
        "next_action": "차이가 있으면 record_id 기준으로 개별 field drift를 점검하세요.",
        "audit": audit,
        "comparison": comparison,
        "summary": summary,
    }


async def _fetch_postgres_rows(
    *,
    settings: AppSettings,
    limit: int,
) -> tuple[list[dict[str, object]], str | None]:
    engine = get_engine(settings=settings)
    if engine is None:
        return [], "DATABASE_URL not configured"

    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    """
                    select
                        record_id,
                        chart_id,
                        report_id,
                        viewer_code,
                        product_code,
                        payment_status,
                        report_request_json,
                        report_payload_json,
                        report_html,
                        report_html_url,
                        chart_svg
                    from charts
                    order by updated_at desc
                    limit :limit
                    """
                ),
                {"limit": limit},
            )
            rows = [dict(row) for row in result.mappings().all()]
    except Exception as exc:  # pragma: no cover - depends on runtime env
        return [], str(exc)

    return rows, None


def _item_to_record_dict(item: StoredChartListItem) -> dict[str, object]:
    return {
        "record_id": item.record_id,
        "chart_id": item.chart_id or item.record_id,
        "report_id": item.report_id,
        "viewer_code": item.report_viewer_code,
        "product_code": item.report_product_code,
        "payment_status": item.report_payment_status,
        "report_request_json": item.report_request,
        "report_payload_json": item.report_payload,
        "report_html": item.report_html,
        "report_html_url": item.report_html_url,
        "chart_svg": item.chart_svg,
    }


def _compare_rows(
    *,
    apps_script_rows: list[dict[str, object]],
    postgres_rows: list[dict[str, object]],
) -> dict[str, object]:
    apps_script_by_record_id = _index_rows(apps_script_rows)
    postgres_by_record_id = _index_rows(postgres_rows)

    missing_record_id_apps_script = sum(1 for row in apps_script_rows if not _clean_record_id(row.get("record_id")))
    missing_record_id_postgres = sum(1 for row in postgres_rows if not _clean_record_id(row.get("record_id")))

    apps_script_ids = set(apps_script_by_record_id)
    postgres_ids = set(postgres_by_record_id)
    shared_ids = sorted(apps_script_ids & postgres_ids)

    apps_script_only_ids = sorted(apps_script_ids - postgres_ids)
    postgres_only_ids = sorted(postgres_ids - apps_script_ids)

    record_status_counts: Counter[str] = Counter()
    field_diff_counts: Counter[str] = Counter()
    samples: list[dict[str, object]] = []

    for record_id in apps_script_only_ids:
        record_status_counts["apps_script_only"] += 1
        if len(samples) < 10:
            samples.append(
                {
                    "record_id": record_id,
                    "status": "apps_script_only",
                    "differences": [],
                }
            )

    for record_id in postgres_only_ids:
        record_status_counts["postgres_only"] += 1
        if len(samples) < 10:
            samples.append(
                {
                    "record_id": record_id,
                    "status": "postgres_only",
                    "differences": [],
                }
            )

    for record_id in shared_ids:
        apps_script_row = apps_script_by_record_id[record_id]
        postgres_row = postgres_by_record_id[record_id]
        differences = _diff_record(apps_script_row, postgres_row)
        if differences:
            record_status_counts["parity_diff"] += 1
            for diff in differences:
                field_diff_counts[diff["field"]] += 1
            if len(samples) < 10:
                samples.append(
                    {
                        "record_id": record_id,
                        "status": "parity_diff",
                        "differences": differences,
                    }
                )
        else:
            record_status_counts["parity_ok"] += 1

    return {
        "apps_script_total_rows": len(apps_script_rows),
        "postgres_total_rows": len(postgres_rows),
        "shared_record_rows": len(shared_ids),
        "apps_script_only_rows": len(apps_script_only_ids),
        "postgres_only_rows": len(postgres_only_ids),
        "parity_ok_rows": int(record_status_counts.get("parity_ok", 0)),
        "parity_diff_rows": int(record_status_counts.get("parity_diff", 0)),
        "missing_record_id_rows": missing_record_id_apps_script + missing_record_id_postgres,
        "record_status_counts": {
            "apps_script_only": int(record_status_counts.get("apps_script_only", 0)),
            "postgres_only": int(record_status_counts.get("postgres_only", 0)),
            "parity_ok": int(record_status_counts.get("parity_ok", 0)),
            "parity_diff": int(record_status_counts.get("parity_diff", 0)),
            "missing_record_id": missing_record_id_apps_script + missing_record_id_postgres,
        },
        "field_diff_counts": dict(sorted(field_diff_counts.items())),
        "samples": samples,
    }


def _diff_record(apps_script_row: dict[str, object], postgres_row: dict[str, object]) -> list[dict[str, object]]:
    differences: list[dict[str, object]] = []
    for field_name, apps_script_key, postgres_key in RECONCILIATION_FIELDS:
        apps_script_value = _normalize_value(apps_script_row.get(apps_script_key))
        postgres_value = _normalize_value(postgres_row.get(postgres_key))
        if apps_script_value != postgres_value:
            differences.append(
                {
                    "field": field_name,
                    "apps_script": apps_script_row.get(apps_script_key),
                    "postgres": postgres_row.get(postgres_key),
                }
            )
    return differences


def _index_rows(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    indexed: dict[str, dict[str, object]] = {}
    for row in rows:
        record_id = _clean_record_id(row.get("record_id"))
        if not record_id:
            continue
        indexed[record_id] = row
    return indexed


def _clean_record_id(value: object | None) -> str:
    return str(value or "").strip()


def _normalize_value(value: object | None) -> object | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
        except Exception:
            return stripped
        return json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return value


def _build_blocked_response(
    *,
    audit: dict[str, object],
    status: str,
    blocking_reason: str,
    next_action: str,
    limit: int,
) -> dict[str, object]:
    return {
        "ok": False,
        "status": status,
        "scope": "apps_script_vs_postgres",
        "sample_limit": limit,
        "reachability_gate_passed": bool(audit["database"]["reachability_gate_passed"]),
        "blocking_reason": blocking_reason,
        "next_action": next_action,
        "audit": audit,
        "comparison": {
            "apps_script_total_rows": 0,
            "postgres_total_rows": 0,
            "shared_record_rows": 0,
            "apps_script_only_rows": 0,
            "postgres_only_rows": 0,
            "parity_ok_rows": 0,
            "parity_diff_rows": 0,
            "missing_record_id_rows": 0,
            "record_status_counts": {
                "apps_script_only": 0,
                "postgres_only": 0,
                "parity_ok": 0,
                "parity_diff": 0,
                "missing_record_id": 0,
            },
            "field_diff_counts": {},
            "samples": [],
        },
        "summary": f"status={status}; blocked={blocking_reason}",
    }


def _build_summary(comparison: dict[str, object], *, limit: int) -> str:
    return (
        f"sample_limit={limit}; "
        f"apps_script_total_rows={comparison['apps_script_total_rows']}; "
        f"postgres_total_rows={comparison['postgres_total_rows']}; "
        f"shared_record_rows={comparison['shared_record_rows']}; "
        f"apps_script_only_rows={comparison['apps_script_only_rows']}; "
        f"postgres_only_rows={comparison['postgres_only_rows']}; "
        f"parity_ok_rows={comparison['parity_ok_rows']}; "
        f"parity_diff_rows={comparison['parity_diff_rows']}; "
        f"missing_record_id_rows={comparison['missing_record_id_rows']}"
    )
