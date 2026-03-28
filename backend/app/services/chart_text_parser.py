from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain.house_assignment import build_formatted, normalize_lon, sign_of
from ..schemas import (
    AnglePoint,
    Availability,
    ChartBody,
    ChartInput,
    ChartMetadata,
    ChartSettings,
    ExtractionProvenance,
    HouseCusp,
    NatalChartRecord,
    TextChartExtractRequest,
    TextChartExtractionResponse,
)

SIGN_BASE = {
    "Aries": 0,
    "Taurus": 30,
    "Gemini": 60,
    "Cancer": 90,
    "Leo": 120,
    "Virgo": 150,
    "Libra": 180,
    "Scorpio": 210,
    "Sagittarius": 240,
    "Capricorn": 270,
    "Aquarius": 300,
    "Pisces": 330,
}

BODY_SPECS = {
    "Sun": ("sun", "planet", None),
    "Moon": ("moon", "planet", None),
    "Mercury": ("mercury", "planet", None),
    "Venus": ("venus", "planet", None),
    "Mars": ("mars", "planet", None),
    "Jupiter": ("jupiter", "planet", None),
    "Saturn": ("saturn", "planet", None),
    "Uranus": ("uranus", "planet", None),
    "Neptune": ("neptune", "planet", None),
    "Pluto": ("pluto", "planet", None),
}

POINT_SPECS = {
    "North Node": ("north_node_true", "mathematical_point", "true_node"),
    "Lilith": ("lilith_mean", "mathematical_point", "mean_apogee"),
    "Chiron": ("chiron", "asteroid", "chiron"),
    "Fortune": ("fortune", "mathematical_point", "day_night_formula"),
    "Vertex": ("vertex", "mathematical_point", "vertex"),
}

ANGLE_SPECS = {
    "ASC": ("asc", "Ascendant"),
    "MC": ("mc", "Midheaven"),
}

BODY_LINE_RE = re.compile(
    r"^(?P<label>Sun|Moon|Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto|North Node|Lilith|Chiron|Fortune|Vertex|ASC|MC)"
    r"\s+in\s+(?P<sign>[A-Za-z]+)\s+(?P<deg>\d{1,2})°(?P<minute>\d{1,2})’,?"
    r"(?:\s+(?P<status>Retrograde|Stationary),?)?"
    r"(?:\s+in\s+(?P<house>\d+)(?:st|nd|rd|th)\s+House)?$"
)
HOUSE_LINE_RE = re.compile(
    r"^(?P<house>\d+)(?:st|nd|rd|th)\s+House\s+in\s+(?P<sign>[A-Za-z]+)\s+(?P<deg>\d{1,2})°(?P<minute>\d{1,2})’$"
)
COORD_RE = re.compile(
    r"(?P<lat_deg>\d{1,2})°(?P<lat_min>\d{1,2})'(?P<lat_hem>[NS]),\s*(?P<lon_deg>\d{1,3})°(?P<lon_min>\d{1,2})'(?P<lon_hem>[EW])"
)
DATE_RE = re.compile(
    r"Date of Birth \(local time\):\s*(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]+)\s+(?P<year>\d{4})\s*-\s*(?P<time>\d{1,2}:\d{2})\s*\((?P<tz>[A-Za-z/_+-]+)\)"
)
CITY_RE = re.compile(r"City:(?P<city>.+)")
COUNTRY_RE = re.compile(r"Country:(?P<country>.+)")
HOUSE_SYSTEM_RE = re.compile(r"House system:(?P<house_system>[A-Za-z ]+)")
UT_RE = re.compile(r"Universal Time \(UT/GMT\):\s*(?P<ut>.+?)\s{2,}")
LST_RE = re.compile(r"Local Sidereal Time \(LST\):(?P<lst>\S+)")
ASPECT_LINE_RE = re.compile(
    r"^(?P<a>.+?)\s+(?P<aspect>Conjunction|Sextile|Square|Trine|Opposition)\s+(?P<b>.+?)\s+\(Orb:\s+(?P<orb>\d+°\d{2}’),\s+(?P<motion>Applying|Separating)\)$"
)

MONTHS = {
    "January": "01",
    "February": "02",
    "March": "03",
    "April": "04",
    "May": "05",
    "June": "06",
    "July": "07",
    "August": "08",
    "September": "09",
    "October": "10",
    "November": "11",
    "December": "12",
}


@dataclass
class ParsedTextChart:
    chart: NatalChartRecord
    parse_warnings: list[str]


def _lon_from_sign(sign: str, degree: int, minute: int) -> float:
    return normalize_lon(SIGN_BASE[sign] + degree + minute / 60)


def _format_position(sign: str, lon: float) -> tuple[str, float]:
    formatted, sign_degree = build_formatted(sign, lon)
    return formatted, round(sign_degree, 6)


def _parse_coord_component(deg: str, minute: str, hemisphere: str) -> float:
    value = int(deg) + int(minute) / 60
    if hemisphere in {"S", "W"}:
        value *= -1
    return value


def _extract_section(lines: list[str], header: str, next_headers: set[str]) -> list[str]:
    in_section = False
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == header:
            in_section = True
            continue
        if in_section and stripped in next_headers:
            break
        if in_section and stripped:
            result.append(stripped)
    return result


def _normalize_country(raw_country: str | None, default_country_code: str | None) -> tuple[str | None, str | None]:
    if not raw_country:
        return default_country_code, None
    match = re.search(r"\(([A-Z]{2})\)", raw_country)
    country_code = match.group(1) if match else default_country_code
    country_name = raw_country.split("(")[0].strip()
    return country_code, country_name


def _build_chart_body(item_id: str, label: str, classification: str, definition: str | None, sign: str, degree: int, minute: int, house: int | None, retrograde: bool | None) -> ChartBody:
    lon = _lon_from_sign(sign, degree, minute)
    formatted, sign_degree = _format_position(sign, lon)
    return ChartBody(
        id=item_id,
        label=label,
        classification=classification,
        definition=definition,
        sign=sign,
        degree=sign_degree,
        formatted=formatted,
        lon=round(lon, 6),
        house=house,
        retrograde=retrograde,
    )


def parse_chart_text(payload: TextChartExtractRequest) -> ParsedTextChart:
    lines = [line.strip() for line in payload.raw_text.splitlines() if line.strip()]
    warnings: list[str] = []

    date_match = DATE_RE.search(payload.raw_text)
    if not date_match:
        raise ValueError("Date of Birth (local time) line is required")
    birth_date = f"{date_match.group('year')}-{MONTHS[date_match.group('month')]}-{int(date_match.group('day')):02d}"
    birth_time_local = date_match.group("time")
    timezone = "Asia/Seoul" if date_match.group("tz") == "KST" else date_match.group("tz")

    city_match = CITY_RE.search(payload.raw_text)
    birth_place_name = city_match.group("city").strip() if city_match else "Unknown"
    if not city_match:
        warnings.append("city_missing")

    country_match = COUNTRY_RE.search(payload.raw_text)
    country_code, country_name = _normalize_country(country_match.group("country").strip() if country_match else None, payload.default_country_code)
    if country_match is None:
        warnings.append("country_missing")

    coord_match = COORD_RE.search(payload.raw_text)
    if not coord_match:
        raise ValueError("Latitude/Longitude line is required")
    latitude = _parse_coord_component(coord_match.group("lat_deg"), coord_match.group("lat_min"), coord_match.group("lat_hem"))
    longitude = _parse_coord_component(coord_match.group("lon_deg"), coord_match.group("lon_min"), coord_match.group("lon_hem"))

    house_system_match = HOUSE_SYSTEM_RE.search(payload.raw_text)
    house_system = "placidus"
    if house_system_match:
        house_system = house_system_match.group("house_system").strip().lower().replace(" system", "").replace(" ", "_")
    else:
        warnings.append("house_system_missing_assumed_placidus")

    ut_match = UT_RE.search(payload.raw_text)
    lst_match = LST_RE.search(payload.raw_text)
    if ut_match:
        warnings.append(f"ut_provided_not_recomputed:{ut_match.group('ut').strip()}")
    if lst_match:
        warnings.append(f"lst_provided_not_recomputed:{lst_match.group('lst').strip()}")

    section_headers = {"Planet positions:", "House positions:", "Planet aspects:", "Other aspects:"}
    position_lines = _extract_section(lines, "Planet positions:", {"House positions:", "Planet aspects:", "Other aspects:"})
    house_lines = _extract_section(lines, "House positions:", {"Planet aspects:", "Other aspects:"})
    planet_aspect_lines = _extract_section(lines, "Planet aspects:", {"Other aspects:"})
    other_aspect_lines = _extract_section(lines, "Other aspects:", set())

    bodies: list[ChartBody] = []
    points: list[ChartBody] = []
    angles: dict[str, AnglePoint] = {}

    for line in position_lines:
        if line == "Copy PositionsCopy":
            continue
        match = BODY_LINE_RE.match(line)
        if not match:
            warnings.append(f"unparsed_position_line:{line}")
            continue
        label = match.group("label")
        sign = match.group("sign")
        degree = int(match.group("deg"))
        minute = int(match.group("minute"))
        house = int(match.group("house")) if match.group("house") else None
        status = match.group("status")
        retrograde = True if status == "Retrograde" else None
        if status == "Stationary":
            warnings.append(f"stationary_status_preserved_as_warning:{label}")

        if label in BODY_SPECS:
            item_id, classification, definition = BODY_SPECS[label]
            bodies.append(_build_chart_body(item_id, label, classification, definition, sign, degree, minute, house, retrograde))
        elif label in POINT_SPECS:
            item_id, classification, definition = POINT_SPECS[label]
            points.append(_build_chart_body(item_id, label, classification, definition, sign, degree, minute, house, retrograde))
        elif label in ANGLE_SPECS:
            angle_id, angle_label = ANGLE_SPECS[label]
            lon = _lon_from_sign(sign, degree, minute)
            formatted, sign_degree = _format_position(sign, lon)
            angles[angle_id] = AnglePoint(id=angle_id, label=angle_label, sign=sign, degree=sign_degree, formatted=formatted, lon=round(lon, 6))

    if "asc" not in angles or "mc" not in angles:
        raise ValueError("ASC and MC lines are required")

    asc_lon = angles["asc"].lon
    mc_lon = angles["mc"].lon
    dsc_lon = normalize_lon(asc_lon + 180)
    ic_lon = normalize_lon(mc_lon + 180)
    for angle_id, angle_label, lon in (
        ("dsc", "Descendant", dsc_lon),
        ("ic", "Imum Coeli", ic_lon),
    ):
        sign = sign_of(lon)
        formatted, sign_degree = _format_position(sign, lon)
        angles[angle_id] = AnglePoint(id=angle_id, label=angle_label, sign=sign, degree=sign_degree, formatted=formatted, lon=round(lon, 6))

    houses: list[HouseCusp] = []
    for line in house_lines:
        if line == "Copy PositionsCopy":
            continue
        match = HOUSE_LINE_RE.match(line)
        if not match:
            warnings.append(f"unparsed_house_line:{line}")
            continue
        house_number = int(match.group("house"))
        sign = match.group("sign")
        degree = int(match.group("deg"))
        minute = int(match.group("minute"))
        lon = _lon_from_sign(sign, degree, minute)
        formatted, sign_degree = _format_position(sign, lon)
        houses.append(HouseCusp(house=house_number, sign=sign, degree=sign_degree, formatted=formatted, lon=round(lon, 6)))

    aspects = []
    next_id = 1
    for line in [*planet_aspect_lines, *other_aspect_lines]:
        if line == "Copy PositionsCopy":
            continue
        match = ASPECT_LINE_RE.match(line)
        if not match:
            warnings.append(f"unparsed_aspect_line:{line}")
            continue
        aspects.append(
            {
                "id": f"asp_{next_id:03d}",
                "point_a": match.group("a"),
                "point_b": match.group("b"),
                "aspect_type": match.group("aspect").lower(),
                "orb_text": match.group("orb"),
            }
        )
        next_id += 1

    chart = NatalChartRecord(
        metadata=ChartMetadata(
            chart_id=f"text-{birth_date}-{birth_time_local}-{birth_place_name}".replace(" ", "_").replace(",", "").lower(),
            engine_name="parsed_text_fixture",
            status="parsed",
            warnings=warnings,
        ),
        input=ChartInput(
            person_name=payload.source_label,
            birth_date=birth_date,
            birth_time_local=birth_time_local,
            timezone=timezone or payload.default_timezone,
            birth_place_name=f"{birth_place_name}{', ' + country_name if country_name else ''}",
            country_code=country_code,
            latitude=latitude,
            longitude=longitude,
        ),
        settings=ChartSettings(
            zodiac_type=payload.default_zodiac_type,
            house_system=house_system,
            node_mode="true",
            lilith_mode="mean_apogee",
            fortune_formula="day_night",
        ),
        angles=angles,
        houses=houses,
        bodies=bodies,
        points=points,
        aspects=aspects,  # type: ignore[arg-type]
        availability=Availability(core_complete=True, soft_missing=[]),
    )
    return ParsedTextChart(chart=chart, parse_warnings=warnings)


def extract_chart_from_text(payload: TextChartExtractRequest) -> TextChartExtractionResponse:
    parsed = parse_chart_text(payload)
    return TextChartExtractionResponse(
        chart=parsed.chart,
        provenance=ExtractionProvenance(
            source_type="user_provided_text",
            extraction_mode="parsed_not_computed",
            source_label=payload.source_label,
            parse_warnings=parsed.parse_warnings,
        ),
    )
