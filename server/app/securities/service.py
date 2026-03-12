import logging
import math
from datetime import date, datetime, timedelta
from typing import Optional

import numpy as np
from beanie import PydanticObjectId
from beanie.operators import Text
from fastapi import HTTPException, status

from app.models.market import Exchange
from app.models.price_history import PriceHistoryDaily
from app.models.security import RiskLevel, Sector, Security

from .data_provider import yfinance_provider
from .schemas import (
    AnalysisResponse,
    ExchangeDetailResponse,
    ExchangeSummary,
    PaginationMeta,
    PriceDataPoint,
    PriceHistoryResponse,
    SecurityDetailResponse,
    SecurityListResponse,
    SecuritySearchResponse,
    SecuritySearchResult,
    SecuritySummary,
)

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_HISTORY_YEARS = 2


# ── Helpers ──────────────────────────────────────────────────────────────────


def _clamp_page_size(limit: int) -> int:
    return max(1, min(limit, MAX_PAGE_SIZE))


def _security_to_summary(sec: Security) -> SecuritySummary:
    return SecuritySummary(
        id=str(sec.id),
        symbol=sec.symbol,
        name=sec.name,
        security_type=sec.security_type,
        sector=sec.sector,
        primary_exchange_code=sec.primary_exchange_code,
        currency=sec.currency,
        country_code=sec.country_code,
        computed_risk=sec.computed_risk,
        last_price=sec.quote.last_price if sec.quote else None,
        change_pct=sec.quote.change_pct if sec.quote else None,
        is_active=sec.is_active,
    )


def _security_to_detail(sec: Security) -> SecurityDetailResponse:
    return SecurityDetailResponse(
        id=str(sec.id),
        symbol=sec.symbol,
        name=sec.name,
        isin=sec.isin,
        security_type=sec.security_type,
        sector=sec.sector,
        industry=sec.industry,
        description=sec.description,
        listings=sec.listings,
        primary_exchange_code=sec.primary_exchange_code,
        currency=sec.currency,
        country_code=sec.country_code,
        fundamentals=sec.fundamentals,
        quote=sec.quote,
        computed_risk=sec.computed_risk,
        risk_updated_at=sec.risk_updated_at,
        data_source=sec.data_source,
        data_source_id=sec.data_source_id,
        has_historical_data=sec.has_historical_data,
        historical_data_from=sec.historical_data_from,
        historical_data_to=sec.historical_data_to,
        is_active=sec.is_active,
        created_at=sec.created_at,
        updated_at=sec.updated_at,
    )


# ── List securities ─────────────────────────────────────────────────────────


async def list_securities(
    exchange_code: Optional[str] = None,
    sector: Optional[Sector] = None,
    page: int = 1,
    limit: int = DEFAULT_PAGE_SIZE,
) -> SecurityListResponse:
    limit = _clamp_page_size(limit)
    page = max(1, page)
    skip = (page - 1) * limit

    # Build filter
    filters: dict = {"is_active": True}
    if exchange_code:
        filters["primary_exchange_code"] = exchange_code.upper()
    if sector:
        filters["sector"] = sector.value

    total = await Security.find(filters).count()
    total_pages = math.ceil(total / limit) if total else 0

    securities = await Security.find(filters).skip(skip).limit(limit).to_list()

    return SecurityListResponse(
        items=[_security_to_summary(s) for s in securities],
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
        ),
    )


# ── Search securities ────────────────────────────────────────────────────────


async def search_securities(
    query: str,
    limit: int = DEFAULT_PAGE_SIZE,
) -> SecuritySearchResponse:
    limit = _clamp_page_size(limit)

    if not query or not query.strip():
        return SecuritySearchResponse(query=query, results=[], count=0)

    # Try text search first (uses the text index on name + symbol)
    try:
        securities = await Security.find(
            Text(query),
            {"is_active": True},
        ).limit(limit).to_list()
    except Exception:
        # Fallback: regex-based search if text index is not available
        logger.warning("Text search failed, falling back to regex search")
        pattern = {"$regex": query, "$options": "i"}
        securities = await Security.find(
            {"$or": [{"symbol": pattern}, {"name": pattern}]},
            {"is_active": True},
        ).limit(limit).to_list()

    results = [
        SecuritySearchResult(
            id=str(s.id),
            symbol=s.symbol,
            name=s.name,
            primary_exchange_code=s.primary_exchange_code,
            security_type=s.security_type,
            sector=s.sector,
            last_price=s.quote.last_price if s.quote else None,
        )
        for s in securities
    ]

    return SecuritySearchResponse(query=query, results=results, count=len(results))


# ── Get security detail ─────────────────────────────────────────────────────


async def get_security_detail(security_id: str) -> SecurityDetailResponse:
    try:
        oid = PydanticObjectId(security_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid security ID format.",
        )

    sec = await Security.get(oid)
    if sec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security '{security_id}' not found.",
        )
    return _security_to_detail(sec)


# ── Fetch and store historical data ──────────────────────────────────────────


async def fetch_and_store_historical_data(
    security_id: str,
    symbol: str,
    exchange_code: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
) -> int:
    """Fetch historical data from yfinance and persist as PriceHistoryDaily records.

    Returns the number of records stored.
    """
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=365 * DEFAULT_HISTORY_YEARS)

    df = await yfinance_provider.get_historical_data(symbol, exchange_code, start, end)
    if df.empty:
        logger.warning("No historical data for %s/%s", symbol, exchange_code)
        return 0

    stored = 0
    for idx, row in df.iterrows():
        row_date = idx.date() if hasattr(idx, "date") else idx

        # Skip rows with NaN close
        if row.get("close") is None or (isinstance(row.get("close"), float) and np.isnan(row["close"])):
            continue

        # Upsert: avoid duplicates
        existing = await PriceHistoryDaily.find_one(
            PriceHistoryDaily.security_id == security_id,
            PriceHistoryDaily.date == row_date,
        )
        if existing:
            continue

        volume_val = int(row.get("volume", 0)) if not np.isnan(row.get("volume", 0)) else 0

        record = PriceHistoryDaily(
            security_id=security_id,
            date=row_date,
            open=float(row.get("open", 0)),
            high=float(row.get("high", 0)),
            low=float(row.get("low", 0)),
            close=float(row.get("close", 0)),
            volume=volume_val,
            adj_close=float(row["adj_close"]) if "adj_close" in row and not np.isnan(row.get("adj_close", float("nan"))) else None,
            exchange_code=exchange_code,
            data_source="yfinance",
        )
        await record.insert()
        stored += 1

    # Update the security record with historical data metadata
    try:
        sec = await Security.get(PydanticObjectId(security_id))
        if sec:
            sec.has_historical_data = True
            sec.historical_data_from = start
            sec.historical_data_to = end
            sec.updated_at = datetime.utcnow()
            await sec.save()
    except Exception as exc:
        logger.error("Failed to update security metadata: %s", exc)

    logger.info("Stored %d price records for %s", stored, symbol)
    return stored


# ── Get price history ────────────────────────────────────────────────────────


async def get_price_history(
    security_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> PriceHistoryResponse:
    try:
        oid = PydanticObjectId(security_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid security ID format.",
        )

    sec = await Security.get(oid)
    if sec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security '{security_id}' not found.",
        )

    filters: dict = {"security_id": security_id}
    if start_date:
        filters.setdefault("date", {})["$gte"] = start_date
    if end_date:
        filters.setdefault("date", {})["$lte"] = end_date

    records = await PriceHistoryDaily.find(filters).sort("+date").to_list()

    data_points = [
        PriceDataPoint(
            date=r.date,
            open=r.open,
            high=r.high,
            low=r.low,
            close=r.close,
            volume=r.volume,
            adj_close=r.adj_close,
            change_pct=r.change_pct,
        )
        for r in records
    ]

    return PriceHistoryResponse(
        security_id=security_id,
        symbol=sec.symbol,
        exchange_code=sec.primary_exchange_code,
        data=data_points,
        count=len(data_points),
        start_date=data_points[0].date if data_points else None,
        end_date=data_points[-1].date if data_points else None,
    )


# ── Analyze security ────────────────────────────────────────────────────────


def _classify_risk(avg_annual_return: float, annual_log_return: float) -> RiskLevel:
    """Classify risk based on return thresholds.

    Preserves logic from xt-ai-trading:
        avg_annual_return > 10% AND annual_log_return > 5% -> LOW
        avg_annual_return > 5%  AND annual_log_return > 2% -> MEDIUM
        Otherwise -> HIGH
    """
    if avg_annual_return > 10 and annual_log_return > 5:
        return RiskLevel.LOW
    elif avg_annual_return > 5 and annual_log_return > 2:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.HIGH


async def analyze_security(
    security_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> AnalysisResponse:
    """Run risk analysis on a security using its stored price history.

    1. Fetch data if not already present
    2. Calculate simple and log returns
    3. Classify risk
    4. Update the security document
    """
    try:
        oid = PydanticObjectId(security_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid security ID format.",
        )

    sec = await Security.get(oid)
    if sec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security '{security_id}' not found.",
        )

    # Determine the symbol to use for fetching
    symbol = sec.data_source_id or sec.symbol
    exchange_code = sec.primary_exchange_code

    # Fetch and store data if needed
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=365 * DEFAULT_HISTORY_YEARS)

    await fetch_and_store_historical_data(
        security_id=security_id,
        symbol=symbol,
        exchange_code=exchange_code,
        start=start_date,
        end=end_date,
    )

    # Load price history from DB
    records = await PriceHistoryDaily.find(
        PriceHistoryDaily.security_id == security_id,
    ).sort("+date").to_list()

    if len(records) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Not enough price data to perform analysis. Need at least 2 data points.",
        )

    # Extract close prices
    closes = np.array([r.close for r in records], dtype=np.float64)

    # Simple daily return: (P_t / P_{t-1}) - 1
    simple_returns = (closes[1:] / closes[:-1]) - 1.0
    avg_daily_simple = float(np.mean(simple_returns))
    # Annualized: ((1 + avg_daily)^250 - 1) * 100
    avg_annual_simple = (((avg_daily_simple + 1) ** 250) - 1) * 100

    # Log daily return: ln(P_t / P_{t-1})
    log_returns = np.log(closes[1:] / closes[:-1])
    avg_daily_log = float(np.mean(log_returns))
    # Annualized: ((1 + avg_daily_log)^250 - 1) * 100
    avg_annual_log = (((avg_daily_log + 1) ** 250) - 1) * 100

    # Volatility: standard deviation of simple daily returns (annualized)
    daily_volatility = float(np.std(simple_returns, ddof=1))
    annualized_volatility = daily_volatility * np.sqrt(250) * 100

    # Classify risk
    risk_level = _classify_risk(avg_annual_simple, avg_annual_log)

    # Update the security document
    sec.computed_risk = risk_level
    sec.risk_updated_at = datetime.utcnow()
    sec.updated_at = datetime.utcnow()
    await sec.save()

    return AnalysisResponse(
        security_id=security_id,
        symbol=sec.symbol,
        name=sec.name,
        risk_level=risk_level,
        simple_daily_return=round(avg_daily_simple * 100, 5),
        simple_annual_return=round(avg_annual_simple, 5),
        log_daily_return=round(avg_daily_log * 100, 5),
        log_annual_return=round(avg_annual_log, 5),
        volatility=round(annualized_volatility, 5),
        data_points=len(records),
        period_start=records[0].date,
        period_end=records[-1].date,
        analyzed_at=datetime.utcnow(),
    )


# ── Get analysis (cached) ───────────────────────────────────────────────────


async def get_security_analysis(security_id: str) -> AnalysisResponse:
    """Return the most recent analysis result for a security without re-running it."""
    try:
        oid = PydanticObjectId(security_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid security ID format.",
        )

    sec = await Security.get(oid)
    if sec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security '{security_id}' not found.",
        )

    if sec.computed_risk is None or sec.risk_updated_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis available for this security. Trigger an analysis first via POST.",
        )

    # Re-compute the stats from stored data so we can return the full response
    records = await PriceHistoryDaily.find(
        PriceHistoryDaily.security_id == security_id,
    ).sort("+date").to_list()

    if len(records) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Insufficient price data for analysis results.",
        )

    closes = np.array([r.close for r in records], dtype=np.float64)

    simple_returns = (closes[1:] / closes[:-1]) - 1.0
    avg_daily_simple = float(np.mean(simple_returns))
    avg_annual_simple = (((avg_daily_simple + 1) ** 250) - 1) * 100

    log_returns = np.log(closes[1:] / closes[:-1])
    avg_daily_log = float(np.mean(log_returns))
    avg_annual_log = (((avg_daily_log + 1) ** 250) - 1) * 100

    daily_volatility = float(np.std(simple_returns, ddof=1))
    annualized_volatility = daily_volatility * np.sqrt(250) * 100

    return AnalysisResponse(
        security_id=security_id,
        symbol=sec.symbol,
        name=sec.name,
        risk_level=sec.computed_risk,
        simple_daily_return=round(avg_daily_simple * 100, 5),
        simple_annual_return=round(avg_annual_simple, 5),
        log_daily_return=round(avg_daily_log * 100, 5),
        log_annual_return=round(avg_annual_log, 5),
        volatility=round(annualized_volatility, 5),
        data_points=len(records),
        period_start=records[0].date,
        period_end=records[-1].date,
        analyzed_at=sec.risk_updated_at,
    )


# ── Exchange endpoints ───────────────────────────────────────────────────────


async def list_exchanges() -> list[ExchangeSummary]:
    exchanges = await Exchange.find(Exchange.is_active == True).to_list()
    return [
        ExchangeSummary(
            id=str(e.id),
            code=e.code,
            name=e.name,
            country_code=e.country_code,
            currency=e.currency,
            timezone=e.timezone,
            is_active=e.is_active,
        )
        for e in exchanges
    ]


async def get_exchange_detail(code: str) -> ExchangeDetailResponse:
    exchange = await Exchange.find_one(Exchange.code == code.upper())
    if exchange is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exchange '{code}' not found.",
        )

    # Count securities listed on this exchange
    securities_count = await Security.find(
        Security.primary_exchange_code == exchange.code,
        Security.is_active == True,
    ).count()

    return ExchangeDetailResponse(
        id=str(exchange.id),
        code=exchange.code,
        name=exchange.name,
        mic_code=exchange.mic_code,
        country_code=exchange.country_code,
        currency=exchange.currency,
        timezone=exchange.timezone,
        lot_size=exchange.lot_size,
        tick_size=exchange.tick_size,
        circuit_breaker_pct=exchange.circuit_breaker_pct,
        is_active=exchange.is_active,
        data_source=exchange.data_source,
        securities_count=securities_count,
    )
