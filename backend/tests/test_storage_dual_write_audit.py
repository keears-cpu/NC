from __future__ import annotations

from app.schemas import ChartStorageResult
from app.services.chart_storage_service import _merge_storage_results


def build_result(
    *,
    destination: str,
    attempted: bool = True,
    stored: bool,
    message: str,
    status_code: int | None = None,
) -> ChartStorageResult:
    return ChartStorageResult(
        attempted=attempted,
        stored=stored,
        destination=destination,
        status_code=status_code,
        message=message,
    )


def test_merge_storage_results_reports_both_success():
    merged = _merge_storage_results(
        build_result(destination="https://script.google.com/macros/s/fake/exec", stored=True, message="stored", status_code=200),
        build_result(destination="postgres", stored=True, message="stored"),
    )

    assert merged.stored is True
    assert merged.message == "stored_both"
    assert merged.storage_state == "stored_both"
    assert merged.stores["apps_script"].stored is True
    assert merged.stores["postgres"].stored is True


def test_merge_storage_results_reports_apps_script_only():
    merged = _merge_storage_results(
        build_result(destination="https://script.google.com/macros/s/fake/exec", stored=True, message="stored", status_code=200),
        build_result(destination="postgres", stored=False, message="timeout"),
    )

    assert merged.stored is True
    assert merged.message == "stored_apps_script_only; postgres=timeout"
    assert merged.storage_state == "stored_apps_script_only"
    assert merged.stores["apps_script"].stored is True
    assert merged.stores["postgres"].message == "timeout"


def test_merge_storage_results_reports_postgres_only():
    merged = _merge_storage_results(
        build_result(destination="https://script.google.com/macros/s/fake/exec", stored=False, message="apps_script_request_failed", status_code=500),
        build_result(destination="postgres", stored=True, message="stored"),
    )

    assert merged.stored is True
    assert merged.message == "stored_postgres_only; apps_script=apps_script_request_failed"
    assert merged.storage_state == "stored_postgres_only"
    assert merged.stores["apps_script"].stored is False
    assert merged.stores["postgres"].stored is True


def test_merge_storage_results_reports_complete_failure():
    merged = _merge_storage_results(
        build_result(destination="https://script.google.com/macros/s/fake/exec", stored=False, message="apps_script_request_failed", status_code=500),
        build_result(destination="postgres", stored=False, message="DATABASE_URL not configured", attempted=False),
    )

    assert merged.stored is False
    assert merged.message == "apps_script=apps_script_request_failed; postgres=DATABASE_URL not configured"
    assert merged.storage_state == "stored_neither"
    assert merged.stores["apps_script"].stored is False
    assert merged.stores["postgres"].attempted is False
