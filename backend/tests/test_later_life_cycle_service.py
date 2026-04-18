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
from app.services.later_life_cycle_service import build_later_life_timing_layer


def build_sample_chart() -> NatalChartRecord:
    return NatalChartRecord(
        metadata=ChartMetadata(
            chart_id="later-life-sample",
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
            "asc": AnglePoint(id="asc", label="Ascendant", sign="Virgo", degree=12.8, formatted="Virgo 12°48’", lon=162.8),
            "mc": AnglePoint(id="mc", label="Midheaven", sign="Gemini", degree=10.5667, formatted="Gemini 10°34’", lon=70.5667),
            "dsc": AnglePoint(id="dsc", label="Descendant", sign="Pisces", degree=12.8, formatted="Pisces 12°48’", lon=342.8),
            "ic": AnglePoint(id="ic", label="Imum Coeli", sign="Sagittarius", degree=10.5667, formatted="Sagittarius 10°34’", lon=250.5667),
        },
        houses=[HouseCusp(house=1, sign="Virgo", degree=12.8, formatted="Virgo 12°48’", lon=162.8)],
        bodies=[ChartBody(id="sun", label="Sun", classification="planet", sign="Aries", degree=28.65, formatted="Aries 28°39’", lon=28.65, house=8)],
        points=[],
        aspects=[],
        availability=Availability(core_complete=True, soft_missing=[]),
    )


def test_build_later_life_timing_layer_returns_phase_windows_and_cycle_events():
    chart = build_sample_chart()
    timing = build_later_life_timing_layer(chart, reference_date="2026-04-17")

    assert timing.reference_date == "2026-04-17"
    assert timing.age_phase == "40-50"
    assert 45.0 < timing.current_age < 47.0
    assert [window.phase_label for window in timing.phase_windows] == ["40-50", "50-60", "60-70", "70-80", "80+"]

    event_ids = {event.event_id for event in timing.cycle_events}
    assert any(event_id.startswith("saturn_conjunction_saturn") for event_id in event_ids)
    assert any(event_id.startswith("saturn_opposition_saturn") for event_id in event_ids)
    assert any(event_id.startswith("uranus_opposition_uranus") for event_id in event_ids)
    assert any(event_id.startswith("jupiter_conjunction_jupiter") for event_id in event_ids)
    assert any(event_id.startswith("chiron_conjunction_chiron") for event_id in event_ids)
    assert any(event_id.startswith("pluto_square_pluto") for event_id in event_ids)

    first_saturn = next(event for event in timing.cycle_events if event.event_id.startswith("saturn_opposition_saturn"))
    assert first_saturn.phase_bucket in {"40-50", "50-60"}
    assert first_saturn.start_date <= first_saturn.peak_date <= first_saturn.end_date


def test_build_later_life_timing_layer_enriches_current_upcoming_and_primary_events():
    chart = build_sample_chart()
    timing = build_later_life_timing_layer(chart, reference_date="2024-07-01")

    assert timing.reference_date == "2024-07-01"
    assert timing.age_phase == "40-50"
    assert 44.0 < timing.current_age < 45.0

    current_events = timing.active_cycle_events
    upcoming_events = timing.upcoming_cycle_events
    recent_events = timing.recent_cycle_events

    assert len(current_events) == 1
    assert current_events[0].event_status == "current"
    assert current_events[0].is_within_active_window is True
    assert current_events[0].years_to_peak > 0
    assert current_events[0].days_to_peak > 0

    assert upcoming_events
    assert upcoming_events[0].event_status == "upcoming"
    assert upcoming_events[0].years_to_peak < 0
    assert upcoming_events[0].days_to_peak < 0

    assert timing.primary_transition_event is not None
    assert timing.primary_transition_event.event_id == current_events[0].event_id
    assert timing.primary_transition_event.priority_score >= current_events[0].priority_score

    assert "reality-check" in timing.top_theme_tags
    assert "integration" in timing.top_theme_tags
    assert all(event.event_status == "recent" for event in recent_events)
