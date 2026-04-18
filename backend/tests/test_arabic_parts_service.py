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
from app.services.arabic_parts_service import build_arabic_parts


def build_sample_chart() -> NatalChartRecord:
    return NatalChartRecord(
        metadata=ChartMetadata(
            chart_id="traditional-sample",
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
            ChartBody(id="sun", label="Sun", classification="planet", sign="Leo", degree=10.0, formatted="Leo 10°00’", lon=130.0, house=5),
            ChartBody(id="moon", label="Moon", classification="planet", sign="Libra", degree=20.0, formatted="Libra 20°00’", lon=200.0, house=7),
            ChartBody(id="mercury", label="Mercury", classification="planet", sign="Cancer", degree=5.0, formatted="Cancer 5°00’", lon=95.0, house=4),
            ChartBody(id="venus", label="Venus", classification="planet", sign="Virgo", degree=15.0, formatted="Virgo 15°00’", lon=165.0, house=6),
            ChartBody(id="mars", label="Mars", classification="planet", sign="Scorpio", degree=2.0, formatted="Scorpio 2°00’", lon=212.0, house=8),
            ChartBody(id="jupiter", label="Jupiter", classification="planet", sign="Capricorn", degree=9.0, formatted="Capricorn 9°00’", lon=279.0, house=10),
            ChartBody(id="saturn", label="Saturn", classification="planet", sign="Virgo", degree=22.0, formatted="Virgo 22°00’", lon=172.0, house=6),
        ],
        points=[],
        aspects=[],
        availability=Availability(core_complete=True, soft_missing=[]),
    )


def test_build_arabic_parts_returns_fortune_spirit_and_substance():
    chart = build_sample_chart()

    parts = build_arabic_parts(chart)

    assert [part.id for part in parts] == ["fortune", "spirit", "substance"]

    fortune = parts[0]
    spirit = parts[1]
    substance = parts[2]

    assert fortune.sign == "Capricorn"
    assert round(fortune.lon, 6) == 290.0
    assert spirit.sign == "Gemini"
    assert round(spirit.lon, 6) == 70.0
    assert substance.sign == "Scorpio"
    assert round(substance.lon, 6) == 225.0
    assert substance.source_house == 2
    assert substance.source_sign == "Taurus"
    assert substance.ruler_id == "venus"

