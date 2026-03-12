from datetime import date, datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class SecurityType(str, Enum):
    EQUITY = "equity"
    ETF = "etf"
    INDEX = "index"
    MUTUAL_FUND = "mutual_fund"
    BOND = "bond"
    COMMODITY = "commodity"
    DERIVATIVE = "derivative"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Sector(str, Enum):
    TECHNOLOGY = "technology"
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    CONSUMER_CYCLICAL = "consumer_cyclical"
    CONSUMER_DEFENSIVE = "consumer_defensive"
    INDUSTRIALS = "industrials"
    ENERGY = "energy"
    UTILITIES = "utilities"
    REAL_ESTATE = "real_estate"
    COMMUNICATION_SERVICES = "communication_services"
    BASIC_MATERIALS = "basic_materials"
    OTHER = "other"


class ExchangeListing(BaseModel):
    exchange_code: str
    ticker: str
    is_primary: bool = False
    listing_date: Optional[date] = None
    delisting_date: Optional[date] = None
    lot_size: int = 1
    is_active: bool = True


class Fundamentals(BaseModel):
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield_pct: Optional[float] = None
    book_value: Optional[float] = None
    face_value: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    avg_volume_30d: Optional[int] = None
    beta: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe_pct: Optional[float] = None
    updated_at: Optional[datetime] = None


class QuoteSnapshot(BaseModel):
    last_price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    prev_close: Optional[float] = None
    volume: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    timestamp: Optional[datetime] = None


class Security(Document):
    symbol: Indexed(str)
    name: str
    isin: Optional[Indexed(str, unique=True)] = None
    security_type: SecurityType = SecurityType.EQUITY

    sector: Optional[Sector] = None
    industry: Optional[str] = None
    description: Optional[str] = None

    listings: list[ExchangeListing] = Field(default_factory=list)
    primary_exchange_code: str
    currency: str
    country_code: str

    fundamentals: Fundamentals = Field(default_factory=Fundamentals)
    quote: QuoteSnapshot = Field(default_factory=QuoteSnapshot)

    computed_risk: Optional[RiskLevel] = None
    risk_updated_at: Optional[datetime] = None

    data_source: Optional[str] = None
    data_source_id: Optional[str] = None
    has_historical_data: bool = False
    historical_data_from: Optional[date] = None
    historical_data_to: Optional[date] = None

    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "securities"
        indexes = [
            [("symbol", 1), ("primary_exchange_code", 1)],
            [("sector", 1), ("security_type", 1)],
            [("listings.exchange_code", 1), ("listings.ticker", 1)],
            [("country_code", 1), ("is_active", 1)],
            [("name", "text"), ("symbol", "text")],
            [("computed_risk", 1)],
        ]
