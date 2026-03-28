from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import swisseph as swe

from ..schemas import AnglePoint, ChartBody, ChartExtractRequest
from .house_assignment import build_formatted, export_house_cusps, house_from_longitude, normalize_lon, sign_of
from .points_calculator import ComputedPoint, calculate_points, point_from_longitude

PLANETS = [
    ("sun", "Sun", "planet", None, swe.SUN),
    ("moon", "Moon", "planet", None, swe.MOON),
    ("mercury", "Mercury", "planet", None, swe.MERCURY),
    ("venus", "Venus", "planet", None, swe.VENUS),
    ("mars", "Mars", "planet", None, swe.MARS),
    ("jupiter", "Jupiter", "planet", None, swe.JUPITER),
    ("saturn", "Saturn", "planet", None, swe.SATURN),
    ("uranus", "Uranus", "planet", None, swe.URANUS),
    ("neptune", "Neptune", "planet", None, swe.NEPTUNE),
    ("pluto", "Pluto", "planet", None, swe.PLUTO),
]

@dataclass
class RawChartComputation:
    jd_ut: float
    cusp_values: list[float]
    houses: list
    angles: dict[str, AnglePoint]
    bodies: list[ChartBody]
    points: list[ChartBody]
    warnings: list[str]
    soft_missing: list[str]
    aspect_items: list[ChartBody]


def choose_house_system(system: str) -> bytes:
    return {
        "placidus": b"P",
        "equal": b"E",
        "whole_sign": b"W",
    }.get(system, b"P")


def choose_flags(zodiac_type: str) -> int:
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    if zodiac_type == "sidereal":
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags |= swe.FLG_SIDEREAL
    return flags


def parse_local_datetime(birth_date: str, birth_time_local: str, timezone_name: str) -> datetime:
    local_dt = datetime.fromisoformat(f"{birth_date}T{birth_time_local}:00")
    return local_dt.replace(tzinfo=ZoneInfo(timezone_name))


def julian_day_ut(local_dt: datetime) -> float:
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)


def ensure_ephemeris_path() -> None:
    ephe_path = Path(__file__).resolve().parents[2] / "ephe"
    swe.set_ephe_path(str(ephe_path))


def ephemeris_runtime_status() -> dict[str, object]:
    ephe_path = Path(__file__).resolve().parents[2] / "ephe"
    data_files = sorted(path.name for path in ephe_path.iterdir() if path.is_file() and path.name != ".gitkeep") if ephe_path.exists() else []
    main_asteroid_file = "seas_18.se1"
    has_main_asteroid_file = main_asteroid_file in data_files
    return {
        "ephe_path": str(ephe_path),
        "ephemeris_files_present": bool(data_files),
        "ephemeris_file_count": len(data_files),
        "ephemeris_files": data_files,
        "main_asteroid_file": main_asteroid_file,
        "main_asteroid_file_present": has_main_asteroid_file,
        "optional_points_degraded": not has_main_asteroid_file,
        "optional_points_affected": ["chiron", "juno", "vesta"],
    }

def _build_angles(asc: float, mc: float) -> dict[str, AnglePoint]:
    return {
        "asc": AnglePoint(id="asc", label="Ascendant", sign=sign_of(asc), degree=round(build_formatted(sign_of(asc), asc)[1], 6), formatted=build_formatted(sign_of(asc), asc)[0], lon=round(normalize_lon(asc), 6)),
        "mc": AnglePoint(id="mc", label="Midheaven", sign=sign_of(mc), degree=round(build_formatted(sign_of(mc), mc)[1], 6), formatted=build_formatted(sign_of(mc), mc)[0], lon=round(normalize_lon(mc), 6)),
        "dsc": AnglePoint(id="dsc", label="Descendant", sign=sign_of(asc + 180), degree=round(build_formatted(sign_of(asc + 180), asc + 180)[1], 6), formatted=build_formatted(sign_of(asc + 180), asc + 180)[0], lon=round(normalize_lon(asc + 180), 6)),
        "ic": AnglePoint(id="ic", label="Imum Coeli", sign=sign_of(mc + 180), degree=round(build_formatted(sign_of(mc + 180), mc + 180)[1], 6), formatted=build_formatted(sign_of(mc + 180), mc + 180)[0], lon=round(normalize_lon(mc + 180), 6)),
    }


def calculate_chart(payload: ChartExtractRequest) -> RawChartComputation:
    ensure_ephemeris_path()
    flags = choose_flags(payload.zodiac_type)
    local_dt = parse_local_datetime(payload.birth_date, payload.birth_time_local, payload.timezone)
    jd_ut = julian_day_ut(local_dt)

    cusps_raw, ascmc = swe.houses_ex(jd_ut, payload.latitude, payload.longitude, choose_house_system(payload.house_system), flags)
    cusp_values = [float(value) for value in cusps_raw]
    asc = float(ascmc[0])
    mc = float(ascmc[1])
    vertex = float(ascmc[3])

    houses = export_house_cusps(cusp_values)
    angles = _build_angles(asc, mc)

    bodies: list[ChartBody] = []
    for item_id, label, classification, definition, planet_const in PLANETS:
        values, _ = swe.calc_ut(jd_ut, planet_const, flags)
        lon = float(values[0])
        speed = float(values[3])
        bodies.append(point_from_longitude(ComputedPoint(item_id, label, classification, definition, lon, speed < 0), house=house_from_longitude(lon, cusp_values)))

    point_result = calculate_points(
        payload=payload,
        jd_ut=jd_ut,
        cusp_values=cusp_values,
        asc=asc,
        vertex=vertex,
        bodies=bodies,
        flags=flags,
    )
    points = point_result.points
    warnings = point_result.warnings
    soft_missing = point_result.soft_missing

    aspect_items = bodies + [point for point in points if point.id in {"north_node_true", "north_node_mean", "chiron", "fortune", "vertex"}]

    return RawChartComputation(
        jd_ut=jd_ut,
        cusp_values=cusp_values,
        houses=houses,
        angles=angles,
        bodies=bodies,
        points=points,
        warnings=warnings,
        soft_missing=soft_missing,
        aspect_items=aspect_items,
    )
