from __future__ import annotations

from sqlalchemy import text

from ..core.config import AppSettings, get_settings
from ..core.database import AUDIT_TABLES, CORE_STORAGE_TABLES, PHASE1_FOUNDATION_TABLES, get_engine


async def get_storage_audit(settings: AppSettings | None = None) -> dict[str, object]:
    settings = settings or get_settings()
    core_tables = {table_name: {"exists": False, "row_count": None} for table_name in CORE_STORAGE_TABLES}
    phase1_tables = {table_name: False for table_name in PHASE1_FOUNDATION_TABLES}
    engine = get_engine(settings=settings)

    if engine is None:
        database_state = "unconfigured"
        return {
            "operational_hub": "google_apps_script",
            "durable_store": "postgres",
            "storage_backend": settings.storage_backend,
            "google_apps_script_url_configured": bool(settings.google_apps_script_url),
            "database": {
                "configured": False,
                "reachable": False,
                "state": database_state,
                "blocking_reason": "DATABASE_URL not configured",
                "next_action": "DATABASE_URL을 설정한 뒤 다시 점검하세요.",
                "reachability_gate_passed": False,
                "backend": settings.storage_backend,
                "message": "DATABASE_URL not configured",
            },
            "core_tables": core_tables,
            "phase1_schema": {
                "ready": False,
                "tables": phase1_tables,
            },
            "summary": _build_summary(database_state=database_state, gate_passed=False, core_tables=core_tables, phase1_tables=phase1_tables),
        }

    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
            existing_tables = await _fetch_existing_tables(connection)
            for table_name in CORE_STORAGE_TABLES:
                exists = table_name in existing_tables
                row_count = await _fetch_row_count(connection, table_name) if exists else None
                core_tables[table_name] = {"exists": exists, "row_count": row_count}
            for table_name in PHASE1_FOUNDATION_TABLES:
                phase1_tables[table_name] = table_name in existing_tables
    except Exception as exc:  # pragma: no cover - depends on runtime env
        database_state = "unreachable"
        return {
            "operational_hub": "google_apps_script",
            "durable_store": "postgres",
            "storage_backend": settings.storage_backend,
            "google_apps_script_url_configured": bool(settings.google_apps_script_url),
            "database": {
                "configured": True,
                "reachable": False,
                "state": database_state,
                "blocking_reason": "DATABASE_URL configured but connection failed",
                "next_action": "DATABASE_URL와 네트워크/호스트 연결을 점검한 뒤 다시 시도하세요.",
                "reachability_gate_passed": False,
                "backend": settings.storage_backend,
                "message": str(exc),
            },
            "core_tables": core_tables,
            "phase1_schema": {
                "ready": False,
                "tables": phase1_tables,
            },
            "summary": _build_summary(database_state=database_state, gate_passed=False, core_tables=core_tables, phase1_tables=phase1_tables),
        }

    database_state = "reachable"
    phase1_ready = all(phase1_tables.values())
    return {
        "operational_hub": "google_apps_script",
        "durable_store": "postgres",
        "storage_backend": settings.storage_backend,
        "google_apps_script_url_configured": bool(settings.google_apps_script_url),
        "database": {
            "configured": True,
            "reachable": True,
            "state": database_state,
            "blocking_reason": None,
            "next_action": "Apps Script ↔ Postgres parity audit를 실행하세요." if phase1_ready else "Phase 1 foundation schema를 채운 뒤 parity audit를 실행하세요.",
            "reachability_gate_passed": True,
            "backend": settings.storage_backend,
            "message": "database reachable",
        },
        "core_tables": core_tables,
        "phase1_schema": {
            "ready": phase1_ready,
            "tables": phase1_tables,
        },
        "summary": _build_summary(database_state=database_state, gate_passed=True, core_tables=core_tables, phase1_tables=phase1_tables),
    }


async def _fetch_existing_tables(connection) -> set[str]:
    table_names = ", ".join(f"'{table_name}'" for table_name in AUDIT_TABLES)
    result = await connection.execute(
        text(
            f"""
            select table_name
            from information_schema.tables
            where table_schema = 'public'
              and table_name in ({table_names})
            """
        )
    )
    return {str(table_name) for table_name in result.scalars().all()}


async def _fetch_row_count(connection, table_name: str) -> int:
    result = await connection.execute(text(f"select count(*) from {table_name}"))
    return int(result.scalar_one())


def _build_summary(
    *,
    database_state: str,
    gate_passed: bool,
    core_tables: dict[str, dict[str, int | bool | None]],
    phase1_tables: dict[str, bool],
) -> str:
    core_present = sum(1 for details in core_tables.values() if details["exists"] is True)
    core_rows = sum(int(details["row_count"] or 0) for details in core_tables.values())
    phase1_present = sum(1 for present in phase1_tables.values() if present)
    return (
        f"database={database_state}; "
        f"reachability_gate_passed={'true' if gate_passed else 'false'}; "
        f"core_tables={core_present}/{len(CORE_STORAGE_TABLES)}; "
        f"core_rows={core_rows}; "
        f"phase1_tables={phase1_present}/{len(PHASE1_FOUNDATION_TABLES)}"
    )
