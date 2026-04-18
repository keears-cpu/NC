from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.chart_extract import router as chart_extract_router
from .core.config import get_settings
from .core.database import ensure_database_schema, get_database_status
from .domain.chart_calculator import ephemeris_runtime_status
from .geo import fetch_geo_suggestions
from .schemas import GeoAutocompleteResponse
from .services.storage_audit_service import get_storage_audit
from .services.storage_reconciliation_service import reconcile_storage

app = FastAPI(title="Astro Chart Extractor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chart_extract_router)


@app.on_event("startup")
async def prepare_database_schema() -> None:
    settings = get_settings()
    if settings.database_url:
        await ensure_database_schema(settings)


@app.get("/health")
async def healthcheck() -> dict[str, object]:
    settings = get_settings()
    database = await get_database_status(settings)
    return {
        "status": "ok",
        **ephemeris_runtime_status(),
        "storage_backend": settings.storage_backend,
        "google_apps_script_url_configured": bool(settings.google_apps_script_url),
        "supabase_url_configured": bool(settings.supabase_url),
        "database_url_configured": bool(settings.database_url),
        "database_reachable": database.reachable,
        "database_message": database.message,
    }


@app.get("/api/storage/audit")
async def storage_audit() -> dict[str, object]:
    return await get_storage_audit(get_settings())


@app.get("/api/storage/reconcile")
async def storage_reconcile(limit: int = Query(default=100, ge=1, le=500)) -> dict[str, object]:
    return await reconcile_storage(get_settings(), limit=limit)


@app.get("/api/geo/autocomplete", response_model=GeoAutocompleteResponse)
async def get_geo_autocomplete(q: str = Query(..., min_length=1, max_length=120)) -> GeoAutocompleteResponse:
    return GeoAutocompleteResponse(items=await fetch_geo_suggestions(q))
