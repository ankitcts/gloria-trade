from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.security import (
    ExchangeListing,
    Fundamentals,
    QuoteSnapshot,
    RiskLevel,
    Sector,
    SecurityType,
)


# ── Pagination ───────────────────────────────────────────────────────────────


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


# ── Security list / detail ───────────────────────────────────────────────────


class SecuritySummary(BaseModel):
    id: str
    symbol: str
    name: str
    security_type: SecurityType
    sector: Optional[Sector] = None
    primary_exchange_code: str
    currency: str
    country_code: str
    computed_risk: Optional[RiskLevel] = None
    last_price: Optional[float] = None
    change_pct: Optional[float] = None
    is_active: bool = True


class SecurityListResponse(BaseModel):
    items: list[SecuritySummary]
    pagination: PaginationMeta


class SecurityDetailResponse(BaseModel):
    id: str
    symbol: str
    name: str
    isin: Optional[str] = None
    security_type: SecurityType
    sector: Optional[Sector] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    listings: list[ExchangeListing]
    primary_exchange_code: str
    currency: str
    country_code: str
    fundamentals: Fundamentals
    quote: QuoteSnapshot
    computed_risk: Optional[RiskLevel] = None
    risk_updated_at: Optional[datetime] = None
    data_source: Optional[str] = None
    data_source_id: Optional[str] = None
    has_historical_data: bool = False
    historical_data_from: Optional[date] = None
    historical_data_to: Optional[date] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


# ── Search ───────────────────────────────────────────────────────────────────


class SecuritySearchResult(BaseModel):
    id: str
    symbol: str
    name: str
    primary_exchange_code: str
    security_type: SecurityType
    sector: Optional[Sector] = None
    last_price: Optional[float] = None


class SecuritySearchResponse(BaseModel):
    query: str
    results: list[SecuritySearchResult]
    count: int


# ── Analysis ─────────────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    exchange_code: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AnalysisResponse(BaseModel):
    security_id: str
    symbol: str
    name: str
    risk_level: RiskLevel
    simple_daily_return: float
    simple_annual_return: float
    log_daily_return: float
    log_annual_return: float
    volatility: float
    data_points: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    analyzed_at: datetime


# ── Price history ────────────────────────────────────────────────────────────


class PriceDataPoint(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: Optional[float] = None
    change_pct: Optional[float] = None


class PriceHistoryResponse(BaseModel):
    security_id: str
    symbol: str
    exchange_code: Optional[str] = None
    data: list[PriceDataPoint]
    count: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ── Exchange ─────────────────────────────────────────────────────────────────


class ExchangeSummary(BaseModel):
    id: str
    code: str
    name: str
    country_code: str
    currency: str
    timezone: str
    is_active: bool = True


class ExchangeDetailResponse(BaseModel):
    id: str
    code: str
    name: str
    mic_code: Optional[str] = None
    country_code: str
    currency: str
    timezone: str
    lot_size: int = 1
    tick_size: float = 0.01
    circuit_breaker_pct: Optional[float] = None
    is_active: bool = True
    data_source: Optional[str] = None
    securities_count: int = 0
