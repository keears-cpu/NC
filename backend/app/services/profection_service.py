from __future__ import annotations

from calendar import isleap
from datetime import date, datetime, timezone

from ..schemas import NatalChartRecord, ProfectionSnapshot, TraditionalRuler
from .arabic_parts_service import TRADITIONAL_RULERS


def _parse_birth_datetime(chart: NatalChartRecord) -> datetime:
    if chart.metadata.birth_datetime_utc:
        return datetime.fromisoformat(chart.metadata.birth_datetime_utc)

    birth_dt_local = datetime.fromisoformat(f"{chart.input.birth_date}T{chart.input.birth_time_local}:00")
    return birth_dt_local.replace(tzinfo=timezone.utc)


def _resolve_reference_date(reference_date: str | None) -> date:
    if reference_date is None:
        return datetime.now(timezone.utc).date()
    return date.fromisoformat(reference_date)


def _shift_year(dt: datetime, target_year: int) -> datetime:
    if dt.month == 2 and dt.day == 29 and not isleap(target_year):
        return dt.replace(year=target_year, month=2, day=28)
    return dt.replace(year=target_year)


def _find_cycle_bounds(birth_dt: datetime, reference_dt: datetime) -> tuple[datetime, datetime, int]:
    current_year_anniversary = _shift_year(birth_dt, reference_dt.year)
    if reference_dt >= current_year_anniversary:
        cycle_start = current_year_anniversary
        completed_years = reference_dt.year - birth_dt.year
    else:
        cycle_start = _shift_year(birth_dt, reference_dt.year - 1)
        completed_years = reference_dt.year - birth_dt.year - 1
    cycle_end = _shift_year(cycle_start, cycle_start.year + 1)
    return cycle_start, cycle_end, max(0, completed_years)


def build_profection_snapshot(chart: NatalChartRecord, reference_date: str | None = None) -> ProfectionSnapshot:
    birth_dt = _parse_birth_datetime(chart)
    reference_day = _resolve_reference_date(reference_date)
    reference_dt = datetime.combine(reference_day, datetime.min.time(), tzinfo=timezone.utc)
    cycle_start, cycle_end, completed_years = _find_cycle_bounds(birth_dt, reference_dt)

    cycle_duration = max((cycle_end - cycle_start).total_seconds(), 1.0)
    cycle_elapsed = max((reference_dt - cycle_start).total_seconds(), 0.0)
    current_age = completed_years + cycle_elapsed / cycle_duration
    rotation_degrees = round((completed_years * 30.0) + (cycle_elapsed / cycle_duration * 30.0), 6)

    profection_house = (completed_years % 12) + 1
    activated_house = chart.houses[profection_house - 1]
    annual_lord_id, annual_lord_label = TRADITIONAL_RULERS[activated_house.sign]

    return ProfectionSnapshot(
        reference_date=reference_day.isoformat(),
        current_age=round(current_age, 6),
        completed_years=completed_years,
        profection_house=profection_house,
        activated_sign=activated_house.sign,
        annual_lord=TraditionalRuler(id=annual_lord_id, label=annual_lord_label),
        rotation_degrees=rotation_degrees,
        cycle_start_date=cycle_start.date().isoformat(),
        cycle_end_date=cycle_end.date().isoformat(),
    )
