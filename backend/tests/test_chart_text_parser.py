from __future__ import annotations

from app.services.chart_text_parser import extract_chart_from_text
from app.schemas import TextChartExtractRequest


SAMPLE_TEXT = """
Date of Birth (local time):19 April 2016 - 15:20  (KST)
Universal Time (UT/GMT):19 April 2016 - 06:20  Local Sidereal Time (LST):04:39:52
House system:Placidus system
Latitude, Longitude:37°14'N, 127°11'E
City:Yongin-si
Country:South Korea South Korea (KR)

Planet positions:
Sun in Aries 28°39’, in 8th House
Moon in Virgo 15°34’, in 1st House
Mercury in Taurus 18°23’, in 9th House
Venus in Aries 15°30’, in 8th House
Mars in Sagittarius 8°53’, Retrograde, in 3rd House
Jupiter in Virgo 13°56’, Retrograde, in 1st House
Saturn in Sagittarius 15°56’, Retrograde, in 4th House
Uranus in Aries 20°55’, in 8th House
Neptune in Pisces 11°12’, in 6th House
Pluto in Capricorn 17°29’, Stationary, in 5th House
North Node in Virgo 19°52’, Retrograde, in 1st House
Lilith in Libra 26°17’, in 2nd House
Chiron in Pisces 23°14’, in 7th House
Fortune in Capricorn 29°43’, in 5th House
Vertex in Aquarius 12°53’, in 5th House
ASC in Virgo 12°48’
MC in Gemini 10°34’

House positions:
1st House in Virgo 12°48’
2nd House in Libra 8°01’
3rd House in Scorpio 7°40’
4th House in Sagittarius 10°34’
5th House in Capricorn 13°57’
6th House in Aquarius 15°05’
7th House in Pisces 12°48’
8th House in Aries 8°01’
9th House in Taurus 7°40’
10th House in Gemini 10°34’
11th House in Cancer 13°57’
12th House in Leo 15°05’

Planet aspects:
Sun Conjunction Uranus (Orb: 7°43’, Separating)
Moon Trine Mercury (Orb: 2°48’, Applying)

Other aspects:
Ascendant Conjunction Moon (Orb: 2°46’, Applying)
Vertex Trine MC (Orb: 2°18’, Applying)
""".strip()


def test_extract_chart_from_text_parses_sample_fixture():
    response = extract_chart_from_text(
        TextChartExtractRequest(
            raw_text=SAMPLE_TEXT,
            source_label="sample-text",
            default_country_code="KR",
        )
    )

    chart = response.chart
    assert response.provenance.source_type == "user_provided_text"
    assert response.provenance.extraction_mode == "parsed_not_computed"
    assert chart.metadata.engine_name == "parsed_text_fixture"
    assert chart.input.birth_date == "2016-04-19"
    assert chart.input.birth_time_local == "15:20"
    assert chart.input.timezone == "Asia/Seoul"
    assert chart.input.country_code == "KR"
    assert chart.angles["asc"].formatted == "Virgo 12°48’"
    assert chart.angles["mc"].formatted == "Gemini 10°34’"
    assert len(chart.houses) == 12
    assert chart.houses[0].formatted == "Virgo 12°48’"
    assert chart.houses[9].formatted == "Gemini 10°34’"
    assert {body.id for body in chart.bodies} == {
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
    }
    point_ids = {point.id for point in chart.points}
    assert {"north_node_true", "lilith_mean", "chiron", "fortune", "vertex"}.issubset(point_ids)
    mars = next(item for item in chart.bodies if item.id == "mars")
    pluto = next(item for item in chart.bodies if item.id == "pluto")
    assert mars.retrograde is True
    assert pluto.retrograde is None
    assert any(warning.startswith("ut_provided_not_recomputed:") for warning in chart.metadata.warnings)
    assert any(warning == "stationary_status_preserved_as_warning:Pluto" for warning in chart.metadata.warnings)
