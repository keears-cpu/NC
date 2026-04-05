from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AngleKey = Literal["asc", "mc", "dsc", "ic"]
Classification = Literal["planet", "asteroid", "mathematical_point", "angle", "hypothetical"]
ReportPreset = Literal[
    "core_snapshot",
    "core_report",
    "adult_deep_blueprint",
    "teen_growth_report",
    "child_parenting_report",
]
ReportAddon = Literal["career", "money", "relationship", "wellbeing", "parenting"]
PaymentStatus = Literal["pending", "paid", "expired", "cancelled"]
PaymentProvider = Literal["portone"]


class ChartMetadata(BaseModel):
    chart_id: str
    engine_name: str
    status: str
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


class ChartArtworkUpdateRequest(BaseModel):
    chart_svg: str = Field(min_length=1)
    chart_svg_updated_at: str | None = None


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


class ChartExtractAndStoreResponse(BaseModel):
    chart: NatalChartRecord
    storage: ChartStorageResult


class StoredChartListItem(BaseModel):
    record_id: str
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
