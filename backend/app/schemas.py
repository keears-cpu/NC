from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, model_validator


AngleKey = Literal["asc", "mc", "dsc", "ic"]
Classification = Literal["planet", "asteroid", "mathematical_point", "angle", "hypothetical"]
ReportPreset = Literal[
    "core_snapshot",
    "core_report",
    "adult_deep_blueprint",
    "teen_growth_report",
    "child_parenting_report",
    "later_life_integration_report",
]
ReportAddon = Literal["career", "money", "relationship", "wellbeing", "parenting"]
PaymentStatus = Literal["pending", "paid", "expired", "cancelled"]
PaymentProvider = Literal["portone"]
SECONDS_PER_YEAR = 365.2425 * 24 * 60 * 60


def _resolve_reference_date(value: str | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    return date.fromisoformat(value)


def _resolve_birth_datetime_utc(
    birth_date: str,
    birth_time_local: str,
    timezone_name: str,
) -> datetime:
    birth_dt_local = datetime.fromisoformat(f"{birth_date}T{birth_time_local}:00")
    resolved_timezone = ZoneInfo(timezone_name)
    return birth_dt_local.replace(tzinfo=resolved_timezone).astimezone(timezone.utc)


def _require_later_life_age(
    birth_date: str,
    birth_time_local: str,
    timezone_name: str,
    reference_date: str | None,
) -> None:
    resolved_reference_date = _resolve_reference_date(reference_date)
    birth_dt_utc = _resolve_birth_datetime_utc(birth_date, birth_time_local, timezone_name)
    reference_dt_utc = datetime.combine(resolved_reference_date, datetime.min.time(), tzinfo=timezone.utc)
    current_age = (reference_dt_utc - birth_dt_utc).total_seconds() / SECONDS_PER_YEAR
    if current_age < 40:
        raise ValueError("later-life requests require current_age >= 40")


class ChartMetadata(BaseModel):
    chart_id: str
    engine_name: str
    status: str
    birth_datetime_utc: str | None = None
    jd_ut: float | None = None
    warnings: list[str] = Field(default_factory=list)


class ChartInput(BaseModel):
    person_name: str | None = None
    birth_date: str
    birth_time_local: str
    timezone: str = "Asia/Seoul"
    birth_place_name: str
    country_code: str | None = None
    latitude: float
    longitude: float


class ChartSettings(BaseModel):
    zodiac_type: str = "tropical"
    house_system: str = "placidus"
    node_mode: str = "true"
    lilith_mode: str = "mean_apogee"
    fortune_formula: str = "day_night"


class ChartBody(BaseModel):
    id: str
    label: str
    classification: Classification
    definition: str | None = None
    sign: str
    degree: float
    formatted: str
    lon: float
    house: int | None = None
    retrograde: bool | None = None


class HouseCusp(BaseModel):
    house: int
    sign: str
    degree: float
    formatted: str
    lon: float


class AnglePoint(BaseModel):
    id: AngleKey
    label: str
    sign: str
    degree: float
    formatted: str
    lon: float


class Aspect(BaseModel):
    id: str
    point_a: str
    point_b: str
    aspect_type: str
    orb_text: str


class Availability(BaseModel):
    core_complete: bool
    soft_missing: list[str] = Field(default_factory=list)


class TraditionalRuler(BaseModel):
    id: str
    label: str


class TraditionalPoint(BaseModel):
    id: str
    label: str
    formula_key: str
    sign: str
    degree: float
    formatted: str
    lon: float
    house: int | None = None
    source_house: int | None = None
    source_sign: str | None = None
    ruler_id: str | None = None


class ProfectionSnapshot(BaseModel):
    reference_date: str
    current_age: float
    completed_years: int
    profection_house: int
    activated_sign: str
    annual_lord: TraditionalRuler
    rotation_degrees: float
    cycle_start_date: str
    cycle_end_date: str


class TraditionalLayer(BaseModel):
    reference_date: str | None = None
    arabic_parts: list[TraditionalPoint] = Field(default_factory=list)
    profection: ProfectionSnapshot | None = None


class NatalChartRecord(BaseModel):
    metadata: ChartMetadata
    input: ChartInput
    settings: ChartSettings
    angles: dict[AngleKey, AnglePoint]
    houses: list[HouseCusp]
    bodies: list[ChartBody]
    points: list[ChartBody]
    aspects: list[Aspect]
    availability: Availability
    traditional: TraditionalLayer | None = None


class ChartExtractRequest(BaseModel):
    person_name: str | None = None
    phone: str | None = None
    email: str | None = None
    counselor_code: str | None = None
    tester_local_id: str | None = None
    birth_date: str
    birth_time_local: str
    timezone: str = "Asia/Seoul"
    birth_place_name: str
    country_code: str | None = None
    latitude: float
    longitude: float
    zodiac_type: str = "tropical"
    house_system: str = "placidus"
    node_mode: str = "true"
    lilith_mode: str = "mean_apogee"
    fortune_formula: str = "day_night"
    include_chiron: bool = True
    include_juno: bool = True
    include_vesta: bool = True
    include_ceres: bool = True
    include_pallas: bool = True
    include_vulcan: bool = False
    include_vertex: bool = True
    include_fortune: bool = True
    report_preset: ReportPreset | None = None
    report_addons: list[ReportAddon] = Field(default_factory=list)
    report_id: str | None = None
    report_viewer_code: str | None = Field(default=None, pattern=r"^\d{4}$")
    report_product_code: str | None = None
    report_payment_status: PaymentStatus | None = None


class ChartExtractWithReferenceDateRequest(ChartExtractRequest):
    reference_date: str | None = None

    @model_validator(mode="after")
    def validate_reference_date(self) -> "ChartExtractWithReferenceDateRequest":
        if self.reference_date is not None:
            try:
                date.fromisoformat(self.reference_date)
            except ValueError as exc:
                raise ValueError("reference_date must be a valid ISO date (YYYY-MM-DD)") from exc
        return self


class ChartExtractAndStoreRequest(ChartExtractWithReferenceDateRequest):
    @model_validator(mode="after")
    def validate_later_life_store_request(self) -> "ChartExtractAndStoreRequest":
        if self.report_preset != "later_life_integration_report":
            return self

        try:
            _require_later_life_age(
                self.birth_date,
                self.birth_time_local,
                self.timezone,
                self.reference_date,
            )
        except ValueError as exc:
            message = str(exc)
            if message.startswith("Invalid isoformat string"):
                raise ValueError("birth_date and birth_time_local must form a valid datetime") from exc
            if message.startswith("'No time zone found"):
                raise ValueError("timezone must be a valid IANA timezone") from exc
            raise
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc

        return self


class LaterLifeChartExtractRequest(ChartExtractWithReferenceDateRequest):
    @model_validator(mode="after")
    def validate_later_life_request(self) -> "LaterLifeChartExtractRequest":
        try:
            _require_later_life_age(
                self.birth_date,
                self.birth_time_local,
                self.timezone,
                self.reference_date,
            )
        except ValueError as exc:
            message = str(exc)
            if message.startswith("Invalid isoformat string"):
                raise ValueError("birth_date and birth_time_local must form a valid datetime") from exc
            raise
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return self


class ChartArtworkUpdateRequest(BaseModel):
    chart_svg: str = Field(min_length=1)
    chart_svg_updated_at: str | None = None
    chart: NatalChartRecord | None = None
    request_payload: ChartExtractRequest | None = None


class PaymentPrepareRequest(BaseModel):
    record_id: str
    product_code: str
    viewer_code: str = Field(pattern=r"^\d{4}$")
    customer_name: str | None = None
    email: str | None = None
    phone: str | None = None
    provider: PaymentProvider = "portone"
    pay_method: str = "CARD"


class PaymentPrepareResponse(BaseModel):
    ok: bool
    provider: PaymentProvider = "portone"
    record_id: str
    product_code: str
    product_name: str
    payment_order_id: str
    payment_id: str
    amount: int
    currency: str
    payment_status: PaymentStatus
    client_payload: dict[str, object] = Field(default_factory=dict)
    message: str | None = None


class PaymentCompleteRequest(BaseModel):
    payment_id: str
    record_id: str | None = None
    product_code: str | None = None


class PaymentSyncResponse(BaseModel):
    ok: bool
    provider: PaymentProvider = "portone"
    record_id: str | None = None
    payment_id: str | None = None
    payment_order_id: str | None = None
    payment_status: PaymentStatus | None = None
    message: str | None = None
    payment: dict[str, object] | None = None


class GeoSuggestion(BaseModel):
    label: str
    local_label: str | None = None
    country_code: str | None = None
    timezone: str = "Asia/Seoul"
    latitude: float
    longitude: float
    source: Literal["preset", "api"]
    aliases: list[str] = Field(default_factory=list)


class GeoAutocompleteResponse(BaseModel):
    items: list[GeoSuggestion]


class TextChartExtractRequest(BaseModel):
    raw_text: str
    source_label: str | None = None
    default_timezone: str = "Asia/Seoul"
    default_country_code: str | None = None
    default_zodiac_type: str = "tropical"


class ExtractionProvenance(BaseModel):
    source_type: Literal["user_provided_text"]
    extraction_mode: Literal["parsed_not_computed"]
    source_label: str | None = None
    parse_warnings: list[str] = Field(default_factory=list)


class TextChartExtractionResponse(BaseModel):
    chart: NatalChartRecord
    provenance: ExtractionProvenance


class StorageDestinationResult(BaseModel):
    attempted: bool
    stored: bool
    destination: str | None = None
    status_code: int | None = None
    message: str | None = None


class ChartStorageResult(BaseModel):
    attempted: bool
    stored: bool
    destination: str | None = None
    status_code: int | None = None
    message: str | None = None
    record_id: str | None = None
    row_number: int | None = None
    row_updated: bool | None = None
    row_appended: bool | None = None
    storage_state: str | None = None
    stores: dict[str, StorageDestinationResult] = Field(default_factory=dict)


class ChartExtractAndStoreResponse(BaseModel):
    chart: NatalChartRecord
    storage: ChartStorageResult


class LaterLifePhaseWindow(BaseModel):
    phase_label: str
    start_age: float
    end_age: float | None = None
    start_date: str
    end_date: str | None = None
    theme_tags: list[str] = Field(default_factory=list)


class LaterLifeCycleEvent(BaseModel):
    event_id: str
    transit_body: str
    aspect_type: str
    natal_target: str
    start_age: float
    peak_age: float
    end_age: float
    start_date: str
    peak_date: str
    end_date: str
    phase_bucket: str
    theme_tags: list[str] = Field(default_factory=list)
    event_status: Literal["recent", "current", "upcoming", "future"]
    years_to_peak: float = Field(
        description="Signed offset from reference_date to peak_date in years; positive means the peak is in the future."
    )
    days_to_peak: float = Field(
        description="Signed offset from reference_date to peak_date in days; positive means the peak is in the future."
    )
    is_within_active_window: bool
    priority_score: float


class LaterLifeTimingLayer(BaseModel):
    reference_date: str
    current_age: float
    age_phase: str
    phase_windows: list[LaterLifePhaseWindow] = Field(default_factory=list)
    cycle_events: list[LaterLifeCycleEvent] = Field(default_factory=list)
    active_cycle_events: list[LaterLifeCycleEvent] = Field(default_factory=list)
    upcoming_cycle_events: list[LaterLifeCycleEvent] = Field(default_factory=list)
    recent_cycle_events: list[LaterLifeCycleEvent] = Field(default_factory=list)
    primary_transition_event: LaterLifeCycleEvent | None = None
    top_theme_tags: list[str] = Field(default_factory=list)


class LaterLifeChartExtractResponse(BaseModel):
    chart: NatalChartRecord
    later_life: LaterLifeTimingLayer


class StoredChartListItem(BaseModel):
    record_id: str
    chart_id: str | None = None
    person_name: str | None = None
    phone: str | None = None
    birth_date: str
    birth_time_local: str | None = None
    birth_place_name: str | None = None
    email: str | None = None
    created_at: str | None = None
    report_preset: ReportPreset | None = None
    report_addons: list[ReportAddon] = Field(default_factory=list)
    report_id: str | None = None
    report_viewer_code: str | None = None
    report_product_code: str | None = None
    report_payment_status: PaymentStatus | None = None
    report_request: dict[str, object] | None = None
    report_payload: dict[str, object] | None = None
    report_html: str | None = None
    report_html_url: str | None = None
    chart_svg: str | None = None
    chart_svg_updated_at: str | None = None
    chart: NatalChartRecord | None = None


class StoredChartListResponse(BaseModel):
    ok: bool
    items: list[StoredChartListItem] = Field(default_factory=list)
    source: str | None = None
    message: str | None = None


class StoredChartDetailResponse(BaseModel):
    ok: bool
    item: StoredChartListItem | None = None
    source: str | None = None
    message: str | None = None
