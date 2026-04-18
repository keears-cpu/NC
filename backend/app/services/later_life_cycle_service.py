from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from ..schemas import LaterLifeCycleEvent, LaterLifePhaseWindow, LaterLifeTimingLayer, NatalChartRecord

SECONDS_PER_YEAR = 365.2425 * 24 * 60 * 60
DEFAULT_MIN_LATER_LIFE_AGE = 40.0
DEFAULT_MAX_LATER_LIFE_AGE = 100.0
EVENT_HALF_WINDOW_YEARS = 1.0
NEARBY_TRANSITION_WINDOW_YEARS = 4.0


@dataclass(frozen=True)
class CycleDefinition:
    event_id: str
    transit_body: str
    aspect_type: str
    natal_target: str
    period_years: float
    offset_years: float
    theme_tags: tuple[str, ...]


PHASE_WINDOWS: tuple[tuple[str, float, float | None], ...] = (
    ("40-50", 40.0, 50.0),
    ("50-60", 50.0, 60.0),
    ("60-70", 60.0, 70.0),
    ("70-80", 70.0, 80.0),
    ("80+", 80.0, None),
)

LATER_LIFE_CYCLE_DEFINITIONS: tuple[CycleDefinition, ...] = (
    CycleDefinition(
        event_id="saturn_conjunction_saturn",
        transit_body="Saturn",
        aspect_type="conjunction",
        natal_target="Saturn",
        period_years=29.4571,
        offset_years=1.0,
        theme_tags=("responsibility", "boundary", "maturity"),
    ),
    CycleDefinition(
        event_id="saturn_opposition_saturn",
        transit_body="Saturn",
        aspect_type="opposition",
        natal_target="Saturn",
        period_years=29.4571,
        offset_years=0.5,
        theme_tags=("reality-check", "adjustment", "integration"),
    ),
    CycleDefinition(
        event_id="uranus_opposition_uranus",
        transit_body="Uranus",
        aspect_type="opposition",
        natal_target="Uranus",
        period_years=84.011,
        offset_years=0.5,
        theme_tags=("freedom", "change", "repatterning"),
    ),
    CycleDefinition(
        event_id="jupiter_conjunction_jupiter",
        transit_body="Jupiter",
        aspect_type="conjunction",
        natal_target="Jupiter",
        period_years=11.8626,
        offset_years=1.0,
        theme_tags=("growth", "expansion", "renewal"),
    ),
    CycleDefinition(
        event_id="chiron_conjunction_chiron",
        transit_body="Chiron",
        aspect_type="conjunction",
        natal_target="Chiron",
        period_years=50.7,
        offset_years=1.0,
        theme_tags=("healing", "integration", "wound-reframing"),
    ),
    CycleDefinition(
        event_id="pluto_square_pluto",
        transit_body="Pluto",
        aspect_type="square",
        natal_target="Pluto",
        period_years=247.94,
        offset_years=0.25,
        theme_tags=("transformation", "release", "value-reordering"),
    ),
)


def _parse_reference_date(reference_date: str | date | None) -> date:
    if reference_date is None:
        return datetime.now(timezone.utc).date()
    if isinstance(reference_date, date):
        return reference_date
    return date.fromisoformat(reference_date)


def _parse_datetime_utc(chart: NatalChartRecord) -> datetime:
    if chart.metadata.birth_datetime_utc:
        return datetime.fromisoformat(chart.metadata.birth_datetime_utc)

    local_dt = datetime.fromisoformat(f"{chart.input.birth_date}T{chart.input.birth_time_local}:00")
    local_dt = local_dt.replace(tzinfo=ZoneInfo(chart.input.timezone))
    return local_dt.astimezone(timezone.utc)


def _age_years(birth_dt_utc: datetime, reference_date: date) -> float:
    reference_dt_utc = datetime.combine(reference_date, datetime.min.time(), tzinfo=timezone.utc)
    return round((reference_dt_utc - birth_dt_utc).total_seconds() / SECONDS_PER_YEAR, 2)


def _age_phase_label(current_age: float) -> str:
    if current_age < 40:
        return "under_40"
    if current_age < 50:
        return "40-50"
    if current_age < 60:
        return "50-60"
    if current_age < 70:
        return "60-70"
    if current_age < 80:
        return "70-80"
    return "80+"


def _age_to_date(birth_dt_utc: datetime, age_years: float) -> str:
    target_dt = birth_dt_utc + timedelta(days=age_years * 365.2425)
    return target_dt.date().isoformat()


def _age_to_phase_bucket(age_years: float) -> str:
    return _age_phase_label(age_years)


def _phase_window_dates(birth_dt_utc: datetime, start_age: float, end_age: float | None) -> tuple[str, str | None]:
    start_date = _age_to_date(birth_dt_utc, start_age)
    if end_age is None:
        return start_date, None
    return start_date, _age_to_date(birth_dt_utc, end_age)


def _build_phase_windows(birth_dt_utc: datetime) -> list[LaterLifePhaseWindow]:
    windows: list[LaterLifePhaseWindow] = []
    for phase_label, start_age, end_age in PHASE_WINDOWS:
        start_date, end_date = _phase_window_dates(birth_dt_utc, start_age, end_age)
        windows.append(
            LaterLifePhaseWindow(
                phase_label=phase_label,
                start_age=start_age,
                end_age=end_age,
                start_date=start_date,
                end_date=end_date,
                theme_tags=[phase_label],
            )
        )
    return windows


def _generate_event_ages(definition: CycleDefinition) -> list[float]:
    ages: list[float] = []
    age = definition.period_years * definition.offset_years
    while age < DEFAULT_MIN_LATER_LIFE_AGE:
        age += definition.period_years
    while age <= DEFAULT_MAX_LATER_LIFE_AGE:
        ages.append(round(age, 2))
        age += definition.period_years
    return ages


def _build_cycle_events(birth_dt_utc: datetime) -> list[LaterLifeCycleEvent]:
    events: list[LaterLifeCycleEvent] = []
    for definition in LATER_LIFE_CYCLE_DEFINITIONS:
        for index, peak_age in enumerate(_generate_event_ages(definition), start=1):
            start_age = round(max(0.0, peak_age - EVENT_HALF_WINDOW_YEARS), 2)
            end_age = round(peak_age + EVENT_HALF_WINDOW_YEARS, 2)
            start_date = _age_to_date(birth_dt_utc, start_age)
            peak_date = _age_to_date(birth_dt_utc, peak_age)
            end_date = _age_to_date(birth_dt_utc, end_age)
            events.append(
                LaterLifeCycleEvent(
                    event_id=f"{definition.event_id}_{index}",
                    transit_body=definition.transit_body,
                    aspect_type=definition.aspect_type,
                    natal_target=definition.natal_target,
                    start_age=start_age,
                    peak_age=peak_age,
                    end_age=end_age,
                    start_date=start_date,
                    peak_date=peak_date,
                    end_date=end_date,
                    phase_bucket=_age_to_phase_bucket(peak_age),
                    theme_tags=list(definition.theme_tags),
                    event_status="future",
                    years_to_peak=0.0,
                    days_to_peak=0.0,
                    is_within_active_window=False,
                    priority_score=0.0,
                )
            )
    return sorted(events, key=lambda item: item.peak_age)


def _signed_days_to_peak(reference_date: date, peak_date: str) -> float:
    resolved_peak_date = date.fromisoformat(peak_date)
    return float((reference_date - resolved_peak_date).days)


def _event_status(current_age: float, event: LaterLifeCycleEvent) -> str:
    if event.start_age <= current_age <= event.end_age:
        return "current"

    distance_to_peak = abs(event.peak_age - current_age)
    if event.peak_age > current_age and distance_to_peak <= NEARBY_TRANSITION_WINDOW_YEARS:
        return "upcoming"
    if event.peak_age < current_age and distance_to_peak <= NEARBY_TRANSITION_WINDOW_YEARS:
        return "recent"
    return "future"


def _priority_score(event_status: str, days_to_peak: float, peak_age: float, current_age: float) -> float:
    status_weight = {
        "current": 400.0,
        "upcoming": 300.0,
        "recent": 200.0,
        "future": 100.0,
    }[event_status]
    proximity_bonus = max(0.0, 50.0 - abs(days_to_peak) / 30.0)
    age_alignment_bonus = max(0.0, 25.0 - abs(peak_age - current_age) * 10.0)
    return round(status_weight + proximity_bonus + age_alignment_bonus, 2)


def _enrich_cycle_events(
    events: list[LaterLifeCycleEvent],
    current_age: float,
    reference_date: date,
) -> list[LaterLifeCycleEvent]:
    enriched_events: list[LaterLifeCycleEvent] = []
    for event in events:
        days_to_peak = _signed_days_to_peak(reference_date, event.peak_date)
        years_to_peak = round(days_to_peak / 365.2425, 2)
        event_status = _event_status(current_age, event)
        enriched_events.append(
            event.model_copy(
                update={
                    "event_status": event_status,
                    "years_to_peak": years_to_peak,
                    "days_to_peak": days_to_peak,
                    "is_within_active_window": event_status == "current",
                    "priority_score": _priority_score(event_status, days_to_peak, event.peak_age, current_age),
                }
            )
        )
    return enriched_events


def _pick_primary_transition_event(
    events: list[LaterLifeCycleEvent],
) -> LaterLifeCycleEvent | None:
    if not events:
        return None

    status_rank = {"current": 0, "upcoming": 1, "recent": 2, "future": 3}
    ordered_events = sorted(
        events,
        key=lambda event: (
            status_rank.get(event.event_status, 4),
            -event.priority_score,
            abs(event.days_to_peak),
            abs(event.peak_age - event.start_age),
            event.peak_age,
            event.event_id,
        ),
    )
    return ordered_events[0]


def _build_top_theme_tags(
    active_cycle_events: list[LaterLifeCycleEvent],
    primary_transition_event: LaterLifeCycleEvent | None,
) -> list[str]:
    tags: list[str] = []
    for event in active_cycle_events:
        for tag in event.theme_tags:
            if tag not in tags:
                tags.append(tag)
    if primary_transition_event is not None:
        for tag in primary_transition_event.theme_tags:
            if tag not in tags:
                tags.append(tag)
    return tags


def build_later_life_timing_layer(
    chart: NatalChartRecord,
    reference_date: str | date | None = None,
) -> LaterLifeTimingLayer:
    birth_dt_utc = _parse_datetime_utc(chart)
    resolved_reference_date = _parse_reference_date(reference_date)
    current_age = _age_years(birth_dt_utc, resolved_reference_date)
    enriched_cycle_events = _enrich_cycle_events(_build_cycle_events(birth_dt_utc), current_age, resolved_reference_date)
    active_cycle_events = [event for event in enriched_cycle_events if event.event_status == "current"]
    upcoming_cycle_events = [event for event in enriched_cycle_events if event.event_status == "upcoming"]
    recent_cycle_events = [event for event in enriched_cycle_events if event.event_status == "recent"]
    primary_transition_event = _pick_primary_transition_event(enriched_cycle_events)
    return LaterLifeTimingLayer(
        reference_date=resolved_reference_date.isoformat(),
        current_age=current_age,
        age_phase=_age_phase_label(current_age),
        phase_windows=_build_phase_windows(birth_dt_utc),
        cycle_events=enriched_cycle_events,
        active_cycle_events=active_cycle_events,
        upcoming_cycle_events=upcoming_cycle_events,
        recent_cycle_events=recent_cycle_events,
        primary_transition_event=primary_transition_event,
        top_theme_tags=_build_top_theme_tags(active_cycle_events, primary_transition_event),
    )
