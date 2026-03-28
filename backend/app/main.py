from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.chart_extract import router as chart_extract_router
from .domain.chart_calculator import ephemeris_runtime_status
from .geo import fetch_geo_suggestions
from .schemas import GeoAutocompleteResponse

app = FastAPI(title="Astro Chart Extractor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chart_extract_router)


@app.get("/health")
async def healthcheck() -> dict[str, object]:
    return {"status": "ok", **ephemeris_runtime_status()}


@app.get("/api/geo/autocomplete", response_model=GeoAutocompleteResponse)
async def get_geo_autocomplete(q: str = Query(..., min_length=1, max_length=120)) -> GeoAutocompleteResponse:
    return GeoAutocompleteResponse(items=await fetch_geo_suggestions(q))
