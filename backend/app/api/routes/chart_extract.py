from __future__ import annotations

from fastapi import APIRouter

from ...schemas import (
    ChartArtworkUpdateRequest,
    ChartExtractAndStoreResponse,
    ChartExtractRequest,
    ChartStorageResult,
    NatalChartRecord,
    StoredChartDetailResponse,
    StoredChartListResponse,
    TextChartExtractRequest,
    TextChartExtractionResponse,
)
from ...services.chart_service import build_chart_record
from ...services.chart_storage_service import fetch_stored_chart, fetch_stored_charts, store_chart_record, update_stored_chart_artwork
from ...services.chart_text_parser import extract_chart_from_text

router = APIRouter()


@router.post("/api/chart/extract", response_model=NatalChartRecord)
async def post_chart_extract(payload: ChartExtractRequest) -> NatalChartRecord:
    return build_chart_record(payload)


@router.post("/api/chart/extract-and-store", response_model=ChartExtractAndStoreResponse)
async def post_chart_extract_and_store(payload: ChartExtractRequest) -> ChartExtractAndStoreResponse:
    chart = build_chart_record(payload)
    storage = await store_chart_record(chart, request_payload=payload)
    return ChartExtractAndStoreResponse(chart=chart, storage=storage)


@router.post("/api/chart/extract-text", response_model=TextChartExtractionResponse)
async def post_chart_extract_text(payload: TextChartExtractRequest) -> TextChartExtractionResponse:
    return extract_chart_from_text(payload)


@router.get("/api/chart/stored-charts", response_model=StoredChartListResponse)
async def get_stored_charts(limit: int = 100) -> StoredChartListResponse:
    return await fetch_stored_charts(limit=limit)



@router.get("/api/chart/stored-charts/{record_id}", response_model=StoredChartDetailResponse)
async def get_stored_chart(record_id: str) -> StoredChartDetailResponse:
    return await fetch_stored_chart(record_id=record_id)


@router.post("/api/chart/stored-charts/{record_id}/chart-art", response_model=ChartStorageResult)
async def post_stored_chart_art(record_id: str, payload: ChartArtworkUpdateRequest) -> ChartStorageResult:
    return await update_stored_chart_artwork(
        record_id=record_id,
        chart_svg=payload.chart_svg,
        chart_svg_updated_at=payload.chart_svg_updated_at,
    )
