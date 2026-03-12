from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app.models.security import Sector

from .schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    ExchangeDetailResponse,
    ExchangeSummary,
    PriceHistoryResponse,
    SecurityDetailResponse,
    SecurityListResponse,
    SecuritySearchResponse,
)
from .service import (
    analyze_security,
    get_exchange_detail,
    get_price_history,
    get_security_analysis,
    get_security_detail,
    list_exchanges,
    list_securities,
    search_securities,
)

router = APIRouter()


# ── List securities ──────────────────────────────────────────────────────────


@router.get("", response_model=SecurityListResponse)
async def list_securities_endpoint(
    exchange_code: Optional[str] = Query(None, description="Filter by exchange code (e.g. BSE, NSE, NASDAQ)"),
    sector: Optional[Sector] = Query(None, description="Filter by sector"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> SecurityListResponse:
    """List securities with optional filtering and pagination."""
    return await list_securities(
        exchange_code=exchange_code,
        sector=sector,
        page=page,
        limit=limit,
    )


# ── Search securities ────────────────────────────────────────────────────────


@router.get("/search", response_model=SecuritySearchResponse)
async def search_securities_endpoint(
    q: str = Query("", description="Search query (matches symbol and name)"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
) -> SecuritySearchResponse:
    """Full-text search for securities by name or symbol."""
    return await search_securities(query=q, limit=limit)


# ── Exchanges ────────────────────────────────────────────────────────────────


@router.get("/exchanges", response_model=list[ExchangeSummary])
async def list_exchanges_endpoint() -> list[ExchangeSummary]:
    """List all available exchanges."""
    return await list_exchanges()


@router.get("/exchanges/{code}", response_model=ExchangeDetailResponse)
async def get_exchange_detail_endpoint(code: str) -> ExchangeDetailResponse:
    """Get details for a specific exchange by its code."""
    return await get_exchange_detail(code)


# ── Security detail ──────────────────────────────────────────────────────────


@router.get("/{security_id}", response_model=SecurityDetailResponse)
async def get_security_detail_endpoint(security_id: str) -> SecurityDetailResponse:
    """Get full details for a single security."""
    return await get_security_detail(security_id)


# ── Price history ────────────────────────────────────────────────────────────


@router.get("/{security_id}/history", response_model=PriceHistoryResponse)
async def get_security_history_endpoint(
    security_id: str,
    start: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
) -> PriceHistoryResponse:
    """Get historical price data for a security."""
    return await get_price_history(
        security_id=security_id,
        start_date=start,
        end_date=end,
    )


# ── Analysis ─────────────────────────────────────────────────────────────────


@router.post("/{security_id}/analyze", response_model=AnalysisResponse)
async def analyze_security_endpoint(
    security_id: str,
    body: Optional[AnalyzeRequest] = None,
) -> AnalysisResponse:
    """Trigger a risk analysis: fetches market data, computes returns, and classifies risk."""
    start_date = body.start_date if body else None
    end_date = body.end_date if body else None
    return await analyze_security(
        security_id=security_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{security_id}/analysis", response_model=AnalysisResponse)
async def get_security_analysis_endpoint(security_id: str) -> AnalysisResponse:
    """Get the most recent analysis results for a security."""
    return await get_security_analysis(security_id)
