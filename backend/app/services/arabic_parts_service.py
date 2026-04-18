from __future__ import annotations

from ..domain.house_assignment import build_formatted, house_from_longitude, normalize_lon, sign_of
from ..domain.points_calculator import compute_fortune
from ..schemas import NatalChartRecord, TraditionalPoint


TRADITIONAL_RULERS: dict[str, tuple[str, str]] = {
    "Aries": ("mars", "Mars"),
    "Taurus": ("venus", "Venus"),
    "Gemini": ("mercury", "Mercury"),
    "Cancer": ("moon", "Moon"),
    "Leo": ("sun", "Sun"),
    "Virgo": ("mercury", "Mercury"),
    "Libra": ("venus", "Venus"),
    "Scorpio": ("mars", "Mars"),
    "Sagittarius": ("jupiter", "Jupiter"),
    "Capricorn": ("saturn", "Saturn"),
    "Aquarius": ("saturn", "Saturn"),
    "Pisces": ("jupiter", "Jupiter"),
}


def _find_body_lon(chart: NatalChartRecord, body_id: str) -> float:
    for body in chart.bodies:
        if body.id == body_id:
            return body.lon
    raise ValueError(f"{body_id}_not_found")


def _build_point(
    *,
    point_id: str,
    label: str,
    formula_key: str,
    lon: float,
    chart: NatalChartRecord,
    source_house: int | None = None,
    source_sign: str | None = None,
    ruler_id: str | None = None,
) -> TraditionalPoint:
    normalized_lon = normalize_lon(lon)
    sign = sign_of(normalized_lon)
    formatted, sign_degree = build_formatted(sign, normalized_lon)
    house = house_from_longitude(normalized_lon, [house_cusp.lon for house_cusp in chart.houses]) if chart.houses else None
    return TraditionalPoint(
        id=point_id,
        label=label,
        formula_key=formula_key,
        sign=sign,
        degree=round(sign_degree, 6),
        formatted=formatted,
        lon=round(normalized_lon, 6),
        house=house,
        source_house=source_house,
        source_sign=source_sign,
        ruler_id=ruler_id,
    )


def build_arabic_parts(chart: NatalChartRecord) -> list[TraditionalPoint]:
    asc = chart.angles["asc"].lon
    sun_lon = _find_body_lon(chart, "sun")
    moon_lon = _find_body_lon(chart, "moon")
    sun_house = next((body.house for body in chart.bodies if body.id == "sun"), None) or 1
    fortune_lon = compute_fortune(asc, sun_lon, moon_lon, sun_house, chart.settings.fortune_formula)

    is_day = 7 <= sun_house <= 12
    spirit_lon = normalize_lon(asc + sun_lon - moon_lon if is_day else asc + moon_lon - sun_lon)

    house_2 = next((house for house in chart.houses if house.house == 2), None)
    if house_2 is None:
        raise ValueError("house_2_not_found")
    ruler_id, _ = TRADITIONAL_RULERS[house_2.sign]
    ruler_lon = _find_body_lon(chart, ruler_id)
    substance_lon = normalize_lon(asc + house_2.lon - ruler_lon)

    return [
        _build_point(
            point_id="fortune",
            label="Part of Fortune",
            formula_key="fortune",
            lon=fortune_lon,
            chart=chart,
        ),
        _build_point(
            point_id="spirit",
            label="Part of Spirit",
            formula_key="spirit",
            lon=spirit_lon,
            chart=chart,
        ),
        _build_point(
            point_id="substance",
            label="Part of Substance",
            formula_key="substance",
            lon=substance_lon,
            chart=chart,
            source_house=2,
            source_sign=house_2.sign,
            ruler_id=ruler_id,
        ),
    ]
