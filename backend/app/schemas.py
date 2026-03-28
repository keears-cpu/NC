from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AngleKey = Literal["asc", "mc", "dsc", "ic"]
Classification = Literal["planet", "asteroid", "mathematical_point", "angle", "hypothetical"]


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
    include_vulcan: bool = False
    include_vertex: bool = True
    include_fortune: bool = True


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
