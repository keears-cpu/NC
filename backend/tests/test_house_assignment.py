from __future__ import annotations

from app.domain.house_assignment import export_house_cusps, house_from_longitude, normalize_lon


def test_exported_cusps_keep_all_12_houses_and_h1_matches_asc():
    cusps = [240.5546, 272.0, 304.0, 334.0, 4.0, 34.0, 60.5546, 92.0, 124.0, 162.8223, 194.0, 224.0]
    houses = export_house_cusps(cusps)

    assert len(houses) == 12
    assert houses[0].house == 1
    assert houses[0].lon == round(normalize_lon(cusps[0]), 6)
    assert houses[9].house == 10
    assert houses[9].lon == round(normalize_lon(cusps[9]), 6)


def test_house_from_longitude_respects_exported_house_boundaries():
    cusps = [240.5546, 272.0, 304.0, 334.0, 4.0, 34.0, 60.5546, 92.0, 124.0, 162.8223, 194.0, 224.0]

    assert house_from_longitude(243.0667, cusps) == 1
    assert house_from_longitude(132.9, cusps) == 9
    assert house_from_longitude(76.4333, cusps) == 7
