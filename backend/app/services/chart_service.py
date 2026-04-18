from __future__ import annotations

from ..domain.aspect_calculator import compute_aspects
from ..domain.chart_calculator import calculate_chart
from ..schemas import Availability, ChartExtractRequest, ChartInput, ChartMetadata, ChartSettings, NatalChartRecord, TraditionalLayer
from .arabic_parts_service import build_arabic_parts
from .profection_service import build_profection_snapshot


def build_chart_record(payload: ChartExtractRequest, reference_date: str | None = None) -> NatalChartRecord:
    result = calculate_chart(payload)
    chart = NatalChartRecord(
        metadata=ChartMetadata(
            chart_id=f"{payload.birth_date}-{payload.birth_time_local}-{payload.birth_place_name}".replace(" ", "_").replace(",", "").lower(),
            engine_name="swiss_ephemeris",
            status="ready" if not result.warnings else "partial",
            birth_datetime_utc=result.birth_datetime_utc.isoformat(),
            jd_ut=result.jd_ut,
            warnings=result.warnings,
        ),
        input=ChartInput(
            person_name=payload.person_name,
            birth_date=payload.birth_date,
            birth_time_local=payload.birth_time_local,
            timezone=payload.timezone,
            birth_place_name=payload.birth_place_name,
            country_code=payload.country_code,
            latitude=payload.latitude,
            longitude=payload.longitude,
        ),
        settings=ChartSettings(
            zodiac_type=payload.zodiac_type,
            house_system=payload.house_system,
            node_mode=payload.node_mode,
            lilith_mode=payload.lilith_mode,
            fortune_formula=payload.fortune_formula,
        ),
        angles=result.angles,
        houses=result.houses,
        bodies=result.bodies,
        points=result.points,
        aspects=compute_aspects(result.aspect_items),
        availability=Availability(core_complete=True, soft_missing=result.soft_missing),
    )
    profection = build_profection_snapshot(chart, reference_date=reference_date) if reference_date is not None else None
    chart.traditional = TraditionalLayer(
        reference_date=profection.reference_date if profection is not None else None,
        arabic_parts=build_arabic_parts(chart),
        profection=profection,
    )
    return chart
