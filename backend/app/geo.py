from __future__ import annotations

import httpx

from .schemas import GeoSuggestion

KOREA_CITY_PRESETS: list[GeoSuggestion] = [
    GeoSuggestion(label="Seoul, South Korea", local_label="서울", country_code="KR", timezone="Asia/Seoul", latitude=37.5665, longitude=126.9780, source="preset", aliases=["seoul", "서울", "서울특별시"]),
    GeoSuggestion(label="Busan, South Korea", local_label="부산", country_code="KR", timezone="Asia/Seoul", latitude=35.1796, longitude=129.0756, source="preset", aliases=["busan", "pusan", "부산", "부산광역시"]),
    GeoSuggestion(label="Incheon, South Korea", local_label="인천", country_code="KR", timezone="Asia/Seoul", latitude=37.4563, longitude=126.7052, source="preset", aliases=["incheon", "인천", "인천광역시"]),
    GeoSuggestion(label="Daegu, South Korea", local_label="대구", country_code="KR", timezone="Asia/Seoul", latitude=35.8714, longitude=128.6014, source="preset", aliases=["daegu", "대구", "대구광역시"]),
    GeoSuggestion(label="Daejeon, South Korea", local_label="대전", country_code="KR", timezone="Asia/Seoul", latitude=36.3504, longitude=127.3845, source="preset", aliases=["daejeon", "대전", "대전광역시"]),
    GeoSuggestion(label="Gwangju, South Korea", local_label="광주", country_code="KR", timezone="Asia/Seoul", latitude=35.1595, longitude=126.8526, source="preset", aliases=["gwangju", "광주", "광주광역시"]),
    GeoSuggestion(label="Ulsan, South Korea", local_label="울산", country_code="KR", timezone="Asia/Seoul", latitude=35.5384, longitude=129.3114, source="preset", aliases=["ulsan", "울산", "울산광역시"]),
    GeoSuggestion(label="Suwon, South Korea", local_label="수원", country_code="KR", timezone="Asia/Seoul", latitude=37.2636, longitude=127.0286, source="preset", aliases=["suwon", "수원", "수원시"]),
    GeoSuggestion(label="Anyang, South Korea", local_label="안양", country_code="KR", timezone="Asia/Seoul", latitude=37.3943, longitude=126.9568, source="preset", aliases=["anyang", "안양", "안양시"]),
    GeoSuggestion(label="Guri, South Korea", local_label="구리", country_code="KR", timezone="Asia/Seoul", latitude=37.5943, longitude=127.1296, source="preset", aliases=["guri", "구리", "구리시"]),
    GeoSuggestion(label="Namyangju, South Korea", local_label="남양주", country_code="KR", timezone="Asia/Seoul", latitude=37.6360, longitude=127.2165, source="preset", aliases=["namyangju", "남양주", "남양주시"]),
    GeoSuggestion(label="Cheongju, South Korea", local_label="청주", country_code="KR", timezone="Asia/Seoul", latitude=36.6424, longitude=127.4890, source="preset", aliases=["cheongju", "청주", "청주시"]),
    GeoSuggestion(label="Jeonju, South Korea", local_label="전주", country_code="KR", timezone="Asia/Seoul", latitude=35.8242, longitude=127.1480, source="preset", aliases=["jeonju", "전주", "전주시"]),
    GeoSuggestion(label="Jeju, South Korea", local_label="제주", country_code="KR", timezone="Asia/Seoul", latitude=33.4996, longitude=126.5312, source="preset", aliases=["jeju", "제주", "제주시"]),
]


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _score(query: str, item: GeoSuggestion) -> int:
    q = _normalize(query)
    if not q:
        return 0
    corpus = " ".join([item.label, item.local_label or "", *item.aliases]).lower()
    if corpus.startswith(q):
        return 300
    if q in corpus:
        return 200
    return 0


def _timezone_for_country(country_code: str | None) -> str:
    if country_code == "KR":
        return "Asia/Seoul"
    return "UTC"


async def fetch_geo_suggestions(query: str, limit: int = 10) -> list[GeoSuggestion]:
    preset_items = sorted(
        [item for item in KOREA_CITY_PRESETS if _score(query, item) > 0],
        key=lambda item: (-_score(query, item), item.label),
    )

    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "jsonv2", "addressdetails": 1, "limit": limit},
                headers={"User-Agent": "astro-chart-extractor/0.1"},
            )
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return preset_items[:limit]

    merged: list[GeoSuggestion] = list(preset_items)
    for item in payload:
        lat = float(item["lat"])
        lon = float(item["lon"])
        address = item.get("address", {})
        country_code = (address.get("country_code") or "").upper() or None
        timezone = "Asia/Seoul" if country_code == "KR" else _timezone_for_country(country_code)
        suggestion = GeoSuggestion(
            label=item.get("display_name", query),
            local_label=address.get("city") or address.get("town") or address.get("county"),
            country_code=country_code,
            timezone=timezone,
            latitude=lat,
            longitude=lon,
            source="api",
            aliases=[],
        )
        if not any(existing.label == suggestion.label for existing in merged):
            merged.append(suggestion)

    return merged[:limit]
