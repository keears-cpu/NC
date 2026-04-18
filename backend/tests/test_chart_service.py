from __future__ import annotations

from datetime import datetime, timezone

from app.domain.chart_calculator import RawChartComputation
from app.schemas import AnglePoint, ChartBody, ChartExtractRequest, HouseCusp
from app.services.chart_service import build_chart_record


def test_build_chart_record_attaches_traditional_layer(monkeypatch):
    fake_result = RawChartComputation(
        jd_ut=2444340.5,
        birth_datetime_utc=datetime(1980, 4, 17, tzinfo=timezone.utc),
        cusp_values=[float(index * 30) for index in range(12)],
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
        angles={
            "asc": AnglePoint(id="asc", label="Ascendant", sign="Aries", degree=0.0, formatted="Aries 0°00’", lon=0.0),
            "mc": AnglePoint(id="mc", label="Midheaven", sign="Capricorn", degree=0.0, formatted="Capricorn 0°00’", lon=270.0),
            "dsc": AnglePoint(id="dsc", label="Descendant", sign="Libra", degree=0.0, formatted="Libra 0°00’", lon=180.0),
            "ic": AnglePoint(id="ic", label="Imum Coeli", sign="Cancer", degree=0.0, formatted="Cancer 0°00’", lon=90.0),
        },
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
        warnings=[],
        soft_missing=[],
        aspect_items=[],
    )

    monkeypatch.setattr("app.services.chart_service.calculate_chart", lambda payload: fake_result)
    monkeypatch.setattr("app.services.chart_service.compute_aspects", lambda items: [])

    chart = build_chart_record(
        ChartExtractRequest(
            birth_date="1980-04-17",
            birth_time_local="00:00",
            timezone="UTC",
            birth_place_name="Seoul, Korea",
            latitude=37.5665,
            longitude=126.9780,
        ),
        reference_date="2026-04-17",
    )

    assert chart.traditional is not None
    assert [point.id for point in chart.traditional.arabic_parts] == ["fortune", "spirit", "substance"]
    assert chart.traditional.profection is not None
    assert chart.traditional.profection.annual_lord.id == "saturn"


def test_build_chart_record_skips_profection_without_reference_date(monkeypatch):
    fake_result = RawChartComputation(
        jd_ut=2444340.5,
        birth_datetime_utc=datetime(1980, 4, 17, tzinfo=timezone.utc),
        cusp_values=[float(index * 30) for index in range(12)],
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
        angles={
            "asc": AnglePoint(id="asc", label="Ascendant", sign="Aries", degree=0.0, formatted="Aries 0°00’", lon=0.0),
            "mc": AnglePoint(id="mc", label="Midheaven", sign="Capricorn", degree=0.0, formatted="Capricorn 0°00’", lon=270.0),
            "dsc": AnglePoint(id="dsc", label="Descendant", sign="Libra", degree=0.0, formatted="Libra 0°00’", lon=180.0),
            "ic": AnglePoint(id="ic", label="Imum Coeli", sign="Cancer", degree=0.0, formatted="Cancer 0°00’", lon=90.0),
        },
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
        warnings=[],
        soft_missing=[],
        aspect_items=[],
    )

    monkeypatch.setattr("app.services.chart_service.calculate_chart", lambda payload: fake_result)
    monkeypatch.setattr("app.services.chart_service.compute_aspects", lambda items: [])

    chart = build_chart_record(
        ChartExtractRequest(
            birth_date="1980-04-17",
            birth_time_local="00:00",
            timezone="UTC",
            birth_place_name="Seoul, Korea",
            latitude=37.5665,
            longitude=126.9780,
        )
    )

    assert chart.traditional is not None
    assert [point.id for point in chart.traditional.arabic_parts] == ["fortune", "spirit", "substance"]
    assert chart.traditional.reference_date is None
    assert chart.traditional.profection is None
