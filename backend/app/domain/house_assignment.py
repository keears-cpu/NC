from __future__ import annotations

from math import fabs

from ..schemas import HouseCusp

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


def normalize_lon(lon: float) -> float:
    value = lon % 360.0
    return value + 360.0 if value < 0 else value


def format_degree(abs_lon: float) -> tuple[str, float]:
    sign_degree = normalize_lon(abs_lon) % 30
    deg = int(sign_degree)
    minute = round((sign_degree - deg) * 60)
    if minute == 60:
        deg += 1
        minute = 0
    return f"{deg}°{minute:02d}’", sign_degree


def sign_of(lon: float) -> str:
    return SIGNS[int(normalize_lon(lon) // 30)]


def build_formatted(sign: str, lon: float) -> tuple[str, float]:
    text, sign_degree = format_degree(lon)
    return f"{sign} {text}", sign_degree


def export_house_cusps(cusps: list[float]) -> list[HouseCusp]:
    return [
        HouseCusp(
            house=index + 1,
            sign=sign_of(lon),
            degree=round(build_formatted(sign_of(lon), lon)[1], 6),
            formatted=build_formatted(sign_of(lon), lon)[0],
            lon=round(normalize_lon(lon), 6),
        )
        for index, lon in enumerate(cusps)
    ]


def house_from_longitude(lon: float, cusps: list[float]) -> int:
    normalized_cusps = [normalize_lon(value) for value in cusps]
    target = normalize_lon(lon)
    num_houses = len(normalized_cusps)
    for index, start in enumerate(normalized_cusps):
        end = normalized_cusps[(index + 1) % num_houses]
        span = normalize_lon(end - start)
        rel = normalize_lon(target - start)
        if rel < span or fabs(rel - span) < 1e-6:
            return index + 1
    return 12
