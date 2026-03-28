from __future__ import annotations

import pytest

from app.case_validation import (
    BODY_COLUMNS,
    CASE_SPECS,
    DATASET_PATH,
    DEFAULT_TOLERANCES,
    REGRESSION_REFERENCE_CASES,
    get_korea_supplemental_case_ids,
    get_korea_supplemental_diagnostics,
    format_compact_result,
    get_case_specs_by_status,
    get_live_case_specs,
    load_cases,
    load_cases_by_id,
    parse_coordinate,
    parse_position,
    validate_live_case,
)


def test_case_dataset_exists_and_has_rows():
    rows = load_cases()
    assert DATASET_PATH.exists()
    assert len(rows) >= 10


def test_case_dataset_core_fields_parse():
    rows = load_cases()

    for row in rows:
        assert row["case_id"]
        assert row["birth_date"]
        assert row["birth_time_local"]
        assert row["birth_place_name"]

        latitude = parse_coordinate(row["latitude"])
        longitude = parse_coordinate(row["longitude"])

        assert -90.0 <= latitude <= 90.0
        assert -180.0 <= longitude <= 180.0
        assert row["house_system"].lower() == "placidus"
        assert row["zodiac_type"].lower() == "tropical"


def test_case_dataset_positions_follow_expected_format():
    rows = load_cases()

    for row in rows:
        for column in BODY_COLUMNS:
            parsed = parse_position(row[column])
            assert 0 <= parsed.lon % 30 < 30

        assert parse_position(row["asc"]).house is None
        assert parse_position(row["mc"]).house is None


def test_live_case_metadata_is_explicit():
    live_case_ids = {spec.case_id for spec in get_live_case_specs()}
    assert live_case_ids == {"C001", "C011", "C012", "C014"}
    assert REGRESSION_REFERENCE_CASES["korea_reference"] in live_case_ids
    assert REGRESSION_REFERENCE_CASES["global_reference"] in live_case_ids

    deferred_case_ids = {spec.case_id for spec in get_case_specs_by_status("deferred")}
    assert {"C010", "C016", "C025", "C028"}.issubset(deferred_case_ids)


def test_korea_supplemental_cases_are_registered_separately():
    assert get_korea_supplemental_case_ids() == ["SEOUL_SUPP_001", "SEOUL_SUPP_002"]

    diagnostics = get_korea_supplemental_diagnostics()
    assert len(diagnostics) == 2
    for item in diagnostics:
        assert item.fixture_status == "supplemental"
        assert item.city == "Seoul"
        assert item.country == "KR"
        assert item.timezone_hint == "Asia/Seoul"
        assert item.house_system_confidence == "needs_verification"
        assert item.house_system_signal == "whole_sign_style_possible"


@pytest.mark.parametrize("case_id", [spec.case_id for spec in get_live_case_specs()])
def test_selected_cases_match_live_extraction(case_id: str):
    pytest.importorskip("swisseph")

    row = load_cases_by_id()[case_id]
    result = validate_live_case(row, CASE_SPECS[case_id], tolerances=DEFAULT_TOLERANCES, mode="default")

    assert result.passed, format_compact_result(result)
