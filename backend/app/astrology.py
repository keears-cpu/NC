from __future__ import annotations

from .domain.aspect_calculator import compute_aspects
from .domain.chart_calculator import (
    choose_flags,
    choose_house_system,
    ephemeris_runtime_status,
    ensure_ephemeris_path,
    julian_day_ut,
    parse_local_datetime,
)
from .domain.house_assignment import (
    build_formatted,
    export_house_cusps,
    format_degree,
    house_from_longitude,
    normalize_lon,
    sign_of,
)
from .domain.points_calculator import compute_fortune
from .schemas import ChartExtractRequest, NatalChartRecord
from .services.chart_service import build_chart_record


def extract_chart(payload: ChartExtractRequest) -> NatalChartRecord:
    return build_chart_record(payload)
