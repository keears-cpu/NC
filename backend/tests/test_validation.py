from app.astrology import house_from_longitude, normalize_lon
from app.schemas import NatalChartRecord


def test_house_assignment_wraparound():
    cusps = [350.0, 20.0, 45.0, 80.0, 110.0, 140.0, 170.0, 200.0, 225.0, 260.0, 290.0, 320.0]
    assert house_from_longitude(355.0, cusps) == 1
    assert house_from_longitude(10.0, cusps) == 1
    assert house_from_longitude(172.0, cusps) == 7


def test_normalize_longitude_bounds():
    assert normalize_lon(361.5) == 1.5
    assert normalize_lon(-10.0) == 350.0


def test_canonical_schema_accepts_fixture():
    fixture = {
        "metadata": {"chart_id": "kr-seoul", "engine_name": "swiss_ephemeris", "status": "ready", "warnings": []},
        "input": {
            "person_name": "홍길동",
            "birth_date": "1994-08-12",
            "birth_time_local": "14:30",
            "timezone": "Asia/Seoul",
            "birth_place_name": "Seoul, South Korea",
            "country_code": "KR",
            "latitude": 37.5665,
            "longitude": 126.978,
        },
        "settings": {
            "zodiac_type": "tropical",
            "house_system": "placidus",
            "node_mode": "true",
            "lilith_mode": "mean_apogee",
            "fortune_formula": "day_night",
        },
        "angles": {
            "asc": {"id": "asc", "label": "Ascendant", "sign": "Scorpio", "degree": 9.4, "formatted": "Scorpio 9°24’", "lon": 219.4},
            "mc": {"id": "mc", "label": "Midheaven", "sign": "Leo", "degree": 16.2, "formatted": "Leo 16°12’", "lon": 136.2},
            "dsc": {"id": "dsc", "label": "Descendant", "sign": "Taurus", "degree": 9.4, "formatted": "Taurus 9°24’", "lon": 39.4},
            "ic": {"id": "ic", "label": "Imum Coeli", "sign": "Aquarius", "degree": 16.2, "formatted": "Aquarius 16°12’", "lon": 316.2},
        },
        "houses": [
            {"house": index + 1, "sign": "Aries", "degree": 0.0, "formatted": "Aries 0°00’", "lon": float((219.4 + index * 30) % 360)}
            for index in range(12)
        ],
        "bodies": [
            {"id": "sun", "label": "Sun", "classification": "planet", "sign": "Leo", "degree": 19.2, "formatted": "Leo 19°12’", "lon": 139.2, "house": 10},
            {"id": "moon", "label": "Moon", "classification": "planet", "sign": "Sagittarius", "degree": 6.1, "formatted": "Sagittarius 6°06’", "lon": 246.1, "house": 2},
        ],
        "points": [
            {"id": "north_node_true", "label": "True Node", "classification": "mathematical_point", "definition": "true_node", "sign": "Scorpio", "degree": 17.4, "formatted": "Scorpio 17°24’", "lon": 227.4, "house": 1, "retrograde": True}
        ],
        "aspects": [{"id": "asp_001", "point_a": "sun", "point_b": "moon", "aspect_type": "trine", "orb_text": "3°06’"}],
        "availability": {"core_complete": True, "soft_missing": []},
    }

    record = NatalChartRecord.model_validate(fixture)
    assert record.angles["asc"].lon == 219.4
    assert record.houses[0].house == 1
