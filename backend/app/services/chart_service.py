from __future__ import annotations

from ..domain.aspect_calculator import compute_aspects
from ..domain.chart_calculator import calculate_chart
from ..schemas import Availability, ChartExtractRequest, ChartInput, ChartMetadata, ChartSettings, NatalChartRecord


def build_chart_record(payload: ChartExtractRequest) -> NatalChartRecord:
    result = calculate_chart(payload)
    return NatalChartRecord(
        metadata=ChartMetadata(
            chart_id=f"{payload.birth_date}-{payload.birth_time_local}-{payload.birth_place_name}".replace(" ", "_").replace(",", "").lower(),
            engine_name="swiss_ephemeris",
            status="ready" if not result.warnings else "partial",
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
