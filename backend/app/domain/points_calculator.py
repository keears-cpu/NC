from __future__ import annotations

from dataclasses import dataclass

import swisseph as swe

from ..schemas import ChartBody, ChartExtractRequest
from .house_assignment import build_formatted, house_from_longitude, normalize_lon, sign_of

OPTIONAL_POINT_MAP = {
    "chiron": ("chiron", "Chiron", "asteroid", "chiron", getattr(swe, "CHIRON", None)),
    "juno": ("juno", "Juno", "asteroid", "juno", getattr(swe, "JUNO", None)),
    "vesta": ("vesta", "Vesta", "asteroid", "vesta", getattr(swe, "VESTA", None)),
    "ceres": ("ceres", "Ceres", "asteroid", "ceres", getattr(swe, "CERES", None)),
    "pallas": ("pallas", "Pallas Athena", "asteroid", "pallas", getattr(swe, "PALLAS", None)),
    "vulcan": ("vulcan", "Vulcan", "hypothetical", "vulcan", getattr(swe, "VULCAN", None)),
}


@dataclass
class ComputedPoint:
    id: str
    label: str
    classification: str
    definition: str | None
    lon: float
    retrograde: bool | None = None


@dataclass
class PointsComputation:
    points: list[ChartBody]
    warnings: list[str]
    soft_missing: list[str]


def point_from_longitude(point: ComputedPoint, house: int | None = None) -> ChartBody:
    sign = sign_of(point.lon)
    formatted, sign_degree = build_formatted(sign, point.lon)
    return ChartBody(
        id=point.id,
        label=point.label,
        classification=point.classification,
        definition=point.definition,
        sign=sign,
        degree=round(sign_degree, 6),
        formatted=formatted,
        lon=round(normalize_lon(point.lon), 6),
        house=house,
        retrograde=point.retrograde,
    )


def compute_fortune(asc: float, sun: float, moon: float, sun_house: int, formula: str) -> float:
    if formula != "day_night":
        return normalize_lon(asc + moon - sun)
    is_day = 7 <= sun_house <= 12
    return normalize_lon(asc + moon - sun if is_day else asc + sun - moon)


def calculate_points(
    payload: ChartExtractRequest,
    jd_ut: float,
    cusp_values: list[float],
    asc: float,
    vertex: float,
    bodies: list[ChartBody],
    flags: int,
) -> PointsComputation:
    warnings: list[str] = []
    soft_missing: list[str] = []
    points: list[ChartBody] = []

    node_const = swe.TRUE_NODE if payload.node_mode == "true" else swe.MEAN_NODE
    node_id = "north_node_true" if payload.node_mode == "true" else "north_node_mean"
    node_label = "True Node" if payload.node_mode == "true" else "Mean Node"
    node_values, _ = swe.calc_ut(jd_ut, node_const, flags)
    node_lon = float(node_values[0])
    points.append(
        point_from_longitude(
            ComputedPoint(node_id, node_label, "mathematical_point", payload.node_mode + "_node", node_lon, float(node_values[3]) < 0),
            house_from_longitude(node_lon, cusp_values),
        )
    )

    lilith_const = swe.MEAN_APOG if payload.lilith_mode == "mean_apogee" else swe.OSCU_APOG
    lilith_id = "lilith_mean" if payload.lilith_mode == "mean_apogee" else "lilith_true"
    lilith_values, _ = swe.calc_ut(jd_ut, lilith_const, flags)
    lilith_lon = float(lilith_values[0])
    points.append(
        point_from_longitude(
            ComputedPoint(lilith_id, "Lilith", "mathematical_point", payload.lilith_mode, lilith_lon, float(lilith_values[3]) < 0),
            house_from_longitude(lilith_lon, cusp_values),
        )
    )

    for key, enabled in {
        "chiron": payload.include_chiron,
        "juno": payload.include_juno,
        "vesta": payload.include_vesta,
        "ceres": payload.include_ceres,
        "pallas": payload.include_pallas,
        "vulcan": payload.include_vulcan,
    }.items():
        if not enabled:
            continue
        item_id, label, classification, definition, constant = OPTIONAL_POINT_MAP[key]
        if constant is None:
            soft_missing.append(item_id)
            warnings.append(f"{item_id}_constant_unavailable")
            continue
        try:
            values, _ = swe.calc_ut(jd_ut, constant, flags)
            lon = float(values[0])
            points.append(
                point_from_longitude(
                    ComputedPoint(item_id, label, classification, definition, lon, float(values[3]) < 0),
                    house=house_from_longitude(lon, cusp_values),
                )
            )
        except swe.Error as e:
            soft_missing.append(item_id)
            warnings.append(f"{item_id}_ephemeris_error: {str(e)}")

    if payload.include_vertex:
        points.append(
            point_from_longitude(
                ComputedPoint("vertex", "Vertex", "mathematical_point", "vertex", vertex),
                house_from_longitude(vertex, cusp_values),
            )
        )

    if payload.include_fortune:
        sun_lon = next(item.lon for item in bodies if item.id == "sun")
        moon_lon = next(item.lon for item in bodies if item.id == "moon")
        sun_house = next(item.house for item in bodies if item.id == "sun") or 1
        fortune_lon = compute_fortune(asc, sun_lon, moon_lon, sun_house, payload.fortune_formula)
        points.append(
            point_from_longitude(
                ComputedPoint("fortune", "Part of Fortune", "mathematical_point", payload.fortune_formula, fortune_lon),
                house_from_longitude(fortune_lon, cusp_values),
            )
        )

    return PointsComputation(points=points, warnings=warnings, soft_missing=soft_missing)
