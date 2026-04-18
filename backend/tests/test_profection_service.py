from __future__ import annotations

from app.schemas import (
    AnglePoint,
    Availability,
    ChartBody,
    ChartInput,
    ChartMetadata,
    ChartSettings,
    HouseCusp,
    NatalChartRecord,
)
from app.services.profection_service import build_profection_snapshot


def build_sample_chart() -> NatalChartRecord:
    return NatalChartRecord(
        metadata=ChartMetadata(
            chart_id="profection-sample",
            engine_name="swiss_ephemeris",
            status="ready",
            birth_datetime_utc="1980-04-17T00:00:00+00:00",
            jd_ut=2444340.5,
            warnings=[],
        ),
        input=ChartInput(
            person_name="Sample",
            birth_date="1980-04-17",
            birth_time_local="00:00",
            timezone="UTC",
            birth_place_name="Seoul, Korea",
            country_code="KR",
            latitude=37.5665,
            longitude=126.9780,
        ),
        settings=ChartSettings(),
        angles={
            "asc": AnglePoint(id="asc", label="Ascendant", sign="Aries", degree=0.0, formatted="Aries 0°00’", lon=0.0),
            "mc": AnglePoint(id="mc", label="Midheaven", sign="Capricorn", degree=0.0, formatted="Capricorn 0°00’", lon=270.0),
            "dsc": AnglePoint(id="dsc", label="Descendant", sign="Libra", degree=0.0, formatted="Libra 0°00’", lon=180.0),
            "ic": AnglePoint(id="ic", label="Imum Coeli", sign="Cancer", degree=0.0, formatted="Cancer 0°00’", lon=90.0),
        },
        houses=[
            HouseCusp(house=index + 1, sign=sign, degree=0.0, formatted=f"{sign} 0°00’", lon=float(index * 30))
            for index, sign in enumerate(
                [
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
            )
        ],
        bodies=[
            ChartBody(id="sun", label="Sun", classification="planet", sign="Aries", degree=28.0, formatted="Aries 28°00’", lon=28.0, house=1),
            ChartBody(id="moon", label="Moon", classification="planet", sign="Cancer", degree=1.0, formatted="Cancer 1°00’", lon=91.0, house=4),
            ChartBody(id="mercury", label="Mercury", classification="planet", sign="Taurus", degree=12.0, formatted="Taurus 12°00’", lon=42.0, house=2),
            ChartBody(id="venus", label="Venus", classification="planet", sign="Gemini", degree=9.0, formatted="Gemini 9°00’", lon=69.0, house=3),
            ChartBody(id="mars", label="Mars", classification="planet", sign="Leo", degree=3.0, formatted="Leo 3°00’", lon=123.0, house=5),
            ChartBody(id="jupiter", label="Jupiter", classification="planet", sign="Virgo", degree=15.0, formatted="Virgo 15°00’", lon=165.0, house=6),
            ChartBody(id="saturn", label="Saturn", classification="planet", sign="Libra", degree=18.0, formatted="Libra 18°00’", lon=198.0, house=7),
        ],
        points=[],
        aspects=[],
        availability=Availability(core_complete=True, soft_missing=[]),
    )


def test_build_profection_snapshot_returns_house_sign_lord_and_rotation():
    chart = build_sample_chart()

    snapshot = build_profection_snapshot(chart, reference_date="2026-04-17")

    assert snapshot.reference_date == "2026-04-17"
    assert round(snapshot.current_age, 6) == 46.0
    assert snapshot.completed_years == 46
    assert snapshot.profection_house == 11
    assert snapshot.activated_sign == "Aquarius"
    assert snapshot.annual_lord.id == "saturn"
    assert snapshot.annual_lord.label == "Saturn"
    assert snapshot.rotation_degrees == 1380.0
    assert snapshot.cycle_start_date == "2026-04-17"
    assert snapshot.cycle_end_date == "2027-04-17"

