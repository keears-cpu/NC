from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .schemas import ChartBody, ChartExtractRequest, NatalChartRecord


DATASET_PATH = Path(__file__).resolve().parents[2] / "docs" / "astro_cases.csv"
KOREA_SUPPLEMENTAL_DATASET_PATH = Path(__file__).resolve().parents[2] / "docs" / "korea_supplemental_cases.json"

BODY_COLUMNS = [
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
    "node",
    "lilith",
    "chiron",
    "fortune",
    "vertex",
    "asc",
    "mc",
]

POSITION_RE = re.compile(
    r"^(?P<sign>[A-Za-z]+)\s+(?P<deg>\d{1,2})°(?P<minute>\d{1,2})['’]\s*(?:h(?P<house>\d{1,2}))?$"
)
COORD_RE = re.compile(
    r"^(?P<deg>\d{1,3})°(?P<minute>\d{1,2})'(?P<hemisphere>[NSEW])$"
)

SIGN_INDEX = {
    "Aries": 0,
    "Taurus": 1,
    "Gemini": 2,
    "Cancer": 3,
    "Leo": 4,
    "Virgo": 5,
    "Libra": 6,
    "Scorpio": 7,
    "Sagittarius": 8,
    "Capricorn": 9,
    "Aquarius": 10,
    "Pisces": 11,
}


@dataclass(frozen=True)
class ValidationCaseSpec:
    case_id: str
    status: Literal["stable", "ambiguous", "deferred", "supplemental"]
    reason: str
    timezone_hint: str | None = None
    include_in_live: bool = False
    node_source: Literal["true", "mean", "unknown"] = "unknown"
    asc_mc_provenance: Literal["independent_source", "duplicated_from_preview_and_csv", "unknown"] = "unknown"
    asc_mc_confidence: Literal["high", "medium", "unresolved"] = "unresolved"
    provenance_note: str | None = None


@dataclass(frozen=True)
class ValidationTolerances:
    default_longitude_deg: float = 1.0
    planet_longitude_deg: float = 1.0
    point_longitude_deg: float = 1.0
    angle_longitude_deg: float = 1.0

    def for_kind(self, kind: str) -> float:
        if kind == "angle":
            return self.angle_longitude_deg
        if kind == "planet":
            return self.planet_longitude_deg
        if kind == "point":
            return self.point_longitude_deg
        return self.default_longitude_deg


DEFAULT_TOLERANCES = ValidationTolerances()
STRICT_TOLERANCES = ValidationTolerances(
    default_longitude_deg=0.5,
    planet_longitude_deg=0.5,
    point_longitude_deg=0.5,
    angle_longitude_deg=0.3,
)


@dataclass(frozen=True)
class ExpectedPosition:
    sign: str
    lon: float
    house: int | None


@dataclass(frozen=True)
class ActualPosition:
    sign: str
    lon: float
    house: int | None


@dataclass(frozen=True)
class ComparableFieldSpec:
    key: str
    csv_column: str
    source: Literal["body", "point", "angle"]
    source_id: str
    kind: Literal["planet", "point", "angle"]


@dataclass(frozen=True)
class FieldMismatch:
    field: str
    check: Literal["sign", "longitude", "house"]
    expected: str
    actual: str
    delta: float | None = None
    tolerance: float | None = None


@dataclass(frozen=True)
class CaseValidationResult:
    case_id: str
    person_name: str
    mode: Literal["default", "strict"]
    passed: bool
    checked_fields: tuple[str, ...]
    mismatches: tuple[FieldMismatch, ...]


@dataclass(frozen=True)
class SupplementalCaseDiagnostic:
    case_id: str
    fixture_status: str
    city: str
    country: str
    timezone_hint: str
    house_system_confidence: str
    house_system_signal: str
    node_source_consistency: str
    extra_points_storage: str
    live_promotion_requirements: tuple[str, ...]


@dataclass(frozen=True)
class SupplementalCaseEvaluation:
    case_id: str
    person_label: str
    asc_actual: str
    mc_actual: str
    provided_house_pattern_summary: str
    placidus_house_cusps_summary: tuple[str, ...]
    sun_house_provided: int | None
    sun_house_actual: int | None
    moon_house_provided: int | None
    moon_house_actual: int | None
    node_house_provided: int | None
    node_house_actual: int | None
    whole_sign_compatibility: Literal["high", "medium", "low"]
    placidus_compatibility: Literal["high", "medium", "low"]
    node_source_confidence: Literal["unresolved", "likely_true", "likely_mean"]
    recommendation: Literal[
        "keep supplemental_whole_sign",
        "keep supplemental_unknown",
        "candidate_for_future_live",
        "remain_non_live",
    ]
    rationale: tuple[str, ...]


CASE_SPECS: dict[str, ValidationCaseSpec] = {
    "C001": ValidationCaseSpec(
        case_id="C001",
        status="stable",
        include_in_live=True,
        reason="Single-timezone Korea case with explicit coordinates and a user-provided baseline.",
        node_source="unknown",
        asc_mc_provenance="duplicated_from_preview_and_csv",
        asc_mc_confidence="unresolved",
        provenance_note="CSV expected ASC/MC and preview sample chart currently share the same hard-coded values, so the ASC/MC expectation is not independently proven yet.",
    ),
    "C011": ValidationCaseSpec(
        case_id="C011",
        status="stable",
        include_in_live=True,
        timezone_hint="America/New_York",
        reason="US case with explicit New York location in the post-standard-time era.",
        node_source="unknown",
        asc_mc_provenance="independent_source",
        asc_mc_confidence="medium",
        provenance_note="Screenshot-derived fixture does not explicitly label Node as true or mean.",
    ),
    "C012": ValidationCaseSpec(
        case_id="C012",
        status="stable",
        include_in_live=True,
        timezone_hint="America/New_York",
        reason="Second US case sharing the same stable timezone region for repeatability.",
        node_source="unknown",
        asc_mc_provenance="independent_source",
        asc_mc_confidence="medium",
        provenance_note="Screenshot-derived fixture does not explicitly label Node as true or mean.",
    ),
    "C014": ValidationCaseSpec(
        case_id="C014",
        status="stable",
        include_in_live=True,
        reason="London case with explicit city and a usable Europe/London timezone mapping.",
        node_source="unknown",
        asc_mc_provenance="independent_source",
        asc_mc_confidence="medium",
        provenance_note="Screenshot-derived fixture does not explicitly label Node as true or mean.",
    ),
    "C010": ValidationCaseSpec(
        case_id="C010",
        status="deferred",
        reason="Florence 1265 predates standardized civil time, so timezone handling is historically ambiguous.",
    ),
    "C016": ValidationCaseSpec(
        case_id="C016",
        status="deferred",
        reason="GB screenshot does not preserve the exact city text, so place-to-timezone provenance is incomplete.",
    ),
    "C025": ValidationCaseSpec(
        case_id="C025",
        status="deferred",
        reason="Boston 1706 predates standardized US timezones and needs historical local-time treatment.",
    ),
    "C028": ValidationCaseSpec(
        case_id="C028",
        status="deferred",
        timezone_hint="Europe/Rome",
        reason="Vinci 1452 remains deferred because local mean time and historical civil-time provenance are not stable enough for live regression.",
        node_source="unknown",
        asc_mc_provenance="independent_source",
        asc_mc_confidence="medium",
        provenance_note="Historical LMT ambiguity remains unresolved; screenshot-derived Node source is also not labeled as true or mean.",
    ),
}

REGRESSION_REFERENCE_CASES = {
    "korea_reference": "C001",
    "global_reference": "C011",
}

COMPARABLE_FIELDS: tuple[ComparableFieldSpec, ...] = (
    ComparableFieldSpec("sun", "sun", "body", "sun", "planet"),
    ComparableFieldSpec("moon", "moon", "body", "moon", "planet"),
    ComparableFieldSpec("node", "node", "point", "north_node_true", "point"),
    ComparableFieldSpec("asc", "asc", "angle", "asc", "angle"),
    ComparableFieldSpec("mc", "mc", "angle", "mc", "angle"),
)

COUNTRY_TIMEZONE_DEFAULTS = {
    "GB": "Europe/London",
    "IT": "Europe/Rome",
    "KR": "Asia/Seoul",
}


class ValidationTimezoneProvider:
    def resolve(self, row: dict[str, str], spec: ValidationCaseSpec) -> str:
        if spec.timezone_hint:
            return spec.timezone_hint
        country_code = (row.get("country_code") or "").upper()
        if country_code in COUNTRY_TIMEZONE_DEFAULTS:
            return COUNTRY_TIMEZONE_DEFAULTS[country_code]
        raise ValueError(
            f"No validation timezone mapping for case {spec.case_id} ({row.get('birth_place_name', 'unknown place')})"
        )


TIMEZONE_PROVIDER = ValidationTimezoneProvider()


def load_cases() -> list[dict[str, str]]:
    with DATASET_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_cases_by_id() -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in load_cases()}


def parse_coordinate(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        match = COORD_RE.match(value.strip())
        if not match:
            raise ValueError(f"Unsupported coordinate format: {value}") from None
        degrees = float(match.group("deg"))
        minutes = float(match.group("minute"))
        decimal = degrees + minutes / 60.0
        if match.group("hemisphere") in {"S", "W"}:
            decimal *= -1
        return decimal


def parse_position(value: str) -> ExpectedPosition:
    match = POSITION_RE.match(value.strip())
    if not match:
        raise ValueError(f"Unsupported position format: {value}")
    house_raw = match.group("house")
    sign = match.group("sign")
    degree = int(match.group("deg"))
    minute = int(match.group("minute"))
    lon = SIGN_INDEX[sign] * 30.0 + degree + minute / 60.0
    return ExpectedPosition(sign=sign, lon=lon, house=int(house_raw) if house_raw else None)


def angular_distance(left: float, right: float) -> float:
    delta = abs(left - right) % 360.0
    return min(delta, 360.0 - delta)


def get_live_case_specs() -> list[ValidationCaseSpec]:
    return [spec for spec in CASE_SPECS.values() if spec.include_in_live]


def get_case_specs_by_status(status: Literal["stable", "ambiguous", "deferred", "supplemental"]) -> list[ValidationCaseSpec]:
    return [spec for spec in CASE_SPECS.values() if spec.status == status]


def load_korea_supplemental_cases() -> list[dict[str, Any]]:
    with KOREA_SUPPLEMENTAL_DATASET_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["cases"]


def get_korea_supplemental_case_ids() -> list[str]:
    return [case["case_id"] for case in load_korea_supplemental_cases()]


def house_positions_look_whole_sign(house_positions: list[dict[str, Any]]) -> bool:
    if len(house_positions) != 12:
        return False
    return all(str(item.get("degree_text", "")).endswith("0°00’") for item in house_positions)


def parse_sign_only_position(value: str) -> ExpectedPosition:
    normalized = value.strip()
    if " h" in normalized:
        normalized = normalized.replace(" h", " h")
    normalized = normalized.replace(" Rx", "")
    return parse_position(normalized)


def summarize_house_pattern(house_positions: list[dict[str, Any]]) -> str:
    first = house_positions[0]
    last = house_positions[-1]
    if house_positions_look_whole_sign(house_positions):
        return (
            f"12 sign cusps all at 0°00’, starting house 1 in {first['sign']} "
            f"and house 12 in {last['sign']}"
        )
    return "house pattern is not a pure 0°00’ sign-cusp sequence"


def whole_sign_pattern_matches_asc(case_payload: dict[str, Any]) -> bool:
    raw = case_payload["raw_fixture"]
    house_positions = raw["house_positions"]
    if not house_positions_look_whole_sign(house_positions):
        return False
    asc_sign = parse_position(raw["positions"]["asc"]).sign
    return house_positions[0]["sign"] == asc_sign


def diagnose_korea_supplemental_case(case_payload: dict[str, Any]) -> SupplementalCaseDiagnostic:
    metadata = case_payload["metadata"]
    raw = case_payload["raw_fixture"]
    whole_sign_signal = house_positions_look_whole_sign(raw["house_positions"])

    return SupplementalCaseDiagnostic(
        case_id=case_payload["case_id"],
        fixture_status=metadata["fixture_status"],
        city=metadata["city"],
        country=metadata["country"],
        timezone_hint=metadata["timezone_hint"],
        house_system_confidence=metadata["house_system_confidence"],
        house_system_signal="whole_sign_style_possible" if whole_sign_signal else "not_detected",
        node_source_consistency="unresolved_from_user_text",
        extra_points_storage="raw_fixture_preserved_for_juno_vesta_vulcan",
        live_promotion_requirements=(
            "Confirm whether the source chart is whole-sign or placidus before numeric regression.",
            "Verify Node source as true vs mean node against the originating chart.",
            "Normalize extra points into a canonical supplemental schema if they become validation targets.",
        ),
    )


def get_korea_supplemental_diagnostics() -> list[SupplementalCaseDiagnostic]:
    return [diagnose_korea_supplemental_case(case) for case in load_korea_supplemental_cases()]


def build_request_for_supplemental_case(case_payload: dict[str, Any]) -> ChartExtractRequest:
    raw = case_payload["raw_fixture"]
    metadata = case_payload["metadata"]
    return ChartExtractRequest(
        person_name=raw.get("person_name"),
        birth_date=raw["birth_date"],
        birth_time_local=raw["birth_time_local"],
        timezone=metadata["timezone_hint"],
        birth_place_name=raw["birth_place_name"],
        country_code=metadata["country"],
        latitude=37.5665,
        longitude=126.9780,
        zodiac_type="tropical",
        house_system="placidus",
        node_mode="true",
        lilith_mode="mean_apogee",
        include_chiron=True,
        include_juno=True,
        include_vesta=True,
        include_vulcan=True,
        include_vertex=True,
        include_fortune=True,
    )


def summarize_placidus_cusps(record: NatalChartRecord) -> tuple[str, ...]:
    return tuple(f"H{item.house} {item.formatted}" for item in record.houses)


def evaluate_korea_supplemental_case(case_payload: dict[str, Any]) -> SupplementalCaseEvaluation:
    from .astrology import extract_chart

    raw = case_payload["raw_fixture"]
    record = extract_chart(build_request_for_supplemental_case(case_payload))

    bodies = {item.id: item for item in record.bodies}
    points = {item.id: item for item in record.points}
    positions = raw["positions"]
    provided_sun = parse_sign_only_position(positions["sun"])
    provided_moon = parse_sign_only_position(positions["moon"])
    provided_node = parse_sign_only_position(positions["north_node"])

    actual_sun = bodies["sun"]
    actual_moon = bodies["moon"]
    actual_node = points["north_node_true"]

    whole_sign_signal = whole_sign_pattern_matches_asc(case_payload)
    house_matches = sum(
        [
            int(provided_sun.house == actual_sun.house),
            int(provided_moon.house == actual_moon.house),
            int(provided_node.house == actual_node.house),
        ]
    )

    if whole_sign_signal:
        whole_sign_compatibility: Literal["high", "medium", "low"] = "high"
    else:
        whole_sign_compatibility = "medium"

    if house_matches == 3 and not whole_sign_signal:
        placidus_compatibility: Literal["high", "medium", "low"] = "high"
    elif house_matches >= 1:
        placidus_compatibility = "medium"
    else:
        placidus_compatibility = "low"

    if whole_sign_compatibility == "high" and placidus_compatibility != "high":
        recommendation: Literal[
            "keep supplemental_whole_sign",
            "keep supplemental_unknown",
            "candidate_for_future_live",
            "remain_non_live",
        ] = "keep supplemental_whole_sign"
    elif placidus_compatibility == "high":
        recommendation = "candidate_for_future_live"
    elif whole_sign_compatibility == "medium":
        recommendation = "keep supplemental_unknown"
    else:
        recommendation = "remain_non_live"

    rationale = [
        summarize_house_pattern(raw["house_positions"]),
        "Placidus diagnostic is computed with tropical + placidus + true node backend defaults.",
        "Node source in the user-provided text is not labeled as true or mean, so source confidence remains unresolved.",
    ]
    if len(record.houses) != 12:
        rationale.append(f"Backend returned {len(record.houses)} house cusp entries instead of 12; cusp indexing/export needs separate audit.")
    if record.houses and record.houses[0].formatted != record.angles["asc"].formatted:
        rationale.append("First exported house cusp does not match ASC, so placidus cusp labeling should be treated as diagnostic-only for now.")

    return SupplementalCaseEvaluation(
        case_id=case_payload["case_id"],
        person_label=raw.get("person_name") or raw["local_label"],
        asc_actual=record.angles["asc"].formatted,
        mc_actual=record.angles["mc"].formatted,
        provided_house_pattern_summary=summarize_house_pattern(raw["house_positions"]),
        placidus_house_cusps_summary=summarize_placidus_cusps(record),
        sun_house_provided=provided_sun.house,
        sun_house_actual=actual_sun.house,
        moon_house_provided=provided_moon.house,
        moon_house_actual=actual_moon.house,
        node_house_provided=provided_node.house,
        node_house_actual=actual_node.house,
        whole_sign_compatibility=whole_sign_compatibility,
        placidus_compatibility=placidus_compatibility,
        node_source_confidence="unresolved",
        recommendation=recommendation,
        rationale=tuple(rationale),
    )


def get_korea_supplemental_evaluations() -> list[SupplementalCaseEvaluation]:
    return [evaluate_korea_supplemental_case(case) for case in load_korea_supplemental_cases()]


def build_request_for_case(row: dict[str, str], spec: ValidationCaseSpec) -> ChartExtractRequest:
    return ChartExtractRequest(
        person_name=row["person_name"] or None,
        birth_date=row["birth_date"],
        birth_time_local=row["birth_time_local"],
        timezone=TIMEZONE_PROVIDER.resolve(row, spec),
        birth_place_name=row["birth_place_name"],
        country_code=row["country_code"] or None,
        latitude=parse_coordinate(row["latitude"]),
        longitude=parse_coordinate(row["longitude"]),
        house_system=row["house_system"].lower(),
        zodiac_type=row["zodiac_type"].lower(),
        include_juno=False,
        include_vesta=False,
        include_vulcan=False,
    )


def extract_comparable_points(record: NatalChartRecord) -> dict[str, ActualPosition]:
    bodies = {item.id: item for item in record.bodies}
    points = {item.id: item for item in record.points}
    extracted: dict[str, ActualPosition] = {}
    for spec in COMPARABLE_FIELDS:
        if spec.source == "body":
            item = bodies[spec.source_id]
            extracted[spec.key] = position_from_chart_body(item)
        elif spec.source == "point":
            item = points[spec.source_id]
            extracted[spec.key] = position_from_chart_body(item)
        else:
            angle = record.angles[spec.source_id]  # type: ignore[index]
            extracted[spec.key] = ActualPosition(sign=angle.sign, lon=angle.lon, house=None)
    return extracted


def position_from_chart_body(item: ChartBody) -> ActualPosition:
    return ActualPosition(sign=item.sign, lon=item.lon, house=item.house)


def compare_sign(field: str, expected: ExpectedPosition, actual: ActualPosition) -> FieldMismatch | None:
    if expected.sign == actual.sign:
        return None
    return FieldMismatch(field=field, check="sign", expected=expected.sign, actual=actual.sign)


def compare_longitude(
    field: str,
    kind: str,
    expected: ExpectedPosition,
    actual: ActualPosition,
    tolerances: ValidationTolerances,
) -> FieldMismatch | None:
    tolerance = tolerances.for_kind(kind)
    delta = angular_distance(expected.lon, actual.lon)
    if delta <= tolerance:
        return None
    return FieldMismatch(
        field=field,
        check="longitude",
        expected=f"{expected.lon:.4f}",
        actual=f"{actual.lon:.4f}",
        delta=delta,
        tolerance=tolerance,
    )


def compare_house(field: str, expected: ExpectedPosition, actual: ActualPosition) -> FieldMismatch | None:
    if expected.house is None:
        return None
    if expected.house == actual.house:
        return None
    return FieldMismatch(
        field=field,
        check="house",
        expected=str(expected.house),
        actual=str(actual.house),
    )


def compare_expected_actual(
    field_spec: ComparableFieldSpec,
    expected: ExpectedPosition,
    actual: ActualPosition,
    tolerances: ValidationTolerances,
) -> list[FieldMismatch]:
    mismatches: list[FieldMismatch] = []
    sign_mismatch = compare_sign(field_spec.key, expected, actual)
    if sign_mismatch:
        mismatches.append(sign_mismatch)
    longitude_mismatch = compare_longitude(field_spec.key, field_spec.kind, expected, actual, tolerances)
    if longitude_mismatch:
        mismatches.append(longitude_mismatch)
    house_mismatch = compare_house(field_spec.key, expected, actual)
    if house_mismatch:
        mismatches.append(house_mismatch)
    return mismatches


def validate_live_case(
    row: dict[str, str],
    spec: ValidationCaseSpec,
    tolerances: ValidationTolerances = DEFAULT_TOLERANCES,
    mode: Literal["default", "strict"] = "default",
) -> CaseValidationResult:
    from .astrology import extract_chart

    payload = build_request_for_case(row, spec)
    record = extract_chart(payload)
    actual_positions = extract_comparable_points(record)
    mismatches: list[FieldMismatch] = []

    for field_spec in COMPARABLE_FIELDS:
        expected = parse_position(row[field_spec.csv_column])
        actual = actual_positions[field_spec.key]
        mismatches.extend(compare_expected_actual(field_spec, expected, actual, tolerances))

    return CaseValidationResult(
        case_id=spec.case_id,
        person_name=row["person_name"],
        mode=mode,
        passed=not mismatches,
        checked_fields=tuple(field.key for field in COMPARABLE_FIELDS),
        mismatches=tuple(mismatches),
    )


def format_compact_result(result: CaseValidationResult) -> str:
    prefix = "PASS" if result.passed else "FAIL"
    label = f"{prefix} {result.case_id} [{result.mode}]"
    if result.passed:
        checks = ",".join(result.checked_fields)
        return f"{label} {result.person_name} :: checks={checks}"

    details = " | ".join(format_mismatch_compact(item) for item in result.mismatches)
    return f"{label} {result.person_name} :: {details}"


def format_mismatch_compact(mismatch: FieldMismatch) -> str:
    if mismatch.check == "longitude":
        return (
            f"{mismatch.field}.lon exp={mismatch.expected} act={mismatch.actual} "
            f"delta={mismatch.delta:.3f}>{mismatch.tolerance:.3f}"
        )
    return f"{mismatch.field}.{mismatch.check} exp={mismatch.expected} act={mismatch.actual}"


def format_mismatch_detail(mismatch: FieldMismatch) -> str:
    if mismatch.check == "longitude":
        return (
            f"{mismatch.field}: longitude mismatch "
            f"(expected {mismatch.expected}, actual {mismatch.actual}, "
            f"delta {mismatch.delta:.3f}°, tolerance {mismatch.tolerance:.3f}°)"
        )
    return f"{mismatch.field}: {mismatch.check} mismatch (expected {mismatch.expected}, actual {mismatch.actual})"


def build_case_provenance_hints(spec: ValidationCaseSpec) -> tuple[str, ...]:
    hints: list[str] = []
    if spec.node_source == "unknown":
        hints.append("fixture node source unresolved")
        hints.append("backend currently assumes true node")
    if spec.asc_mc_confidence == "unresolved":
        hints.append("ASC/MC expectation provenance unresolved")
    if spec.provenance_note:
        hints.append(spec.provenance_note)
    return tuple(hints)
