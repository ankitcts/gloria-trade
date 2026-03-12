from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ── Request schemas ──────────────────────────────────────────────────────────


class CreatePortfolioRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    currency: str = Field("INR", min_length=3, max_length=3)
    initial_cash_balance: float = Field(0.0, ge=0)


class UpdatePortfolioRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class RiskSettingsRequest(BaseModel):
    high_pct: float = Field(ge=0, le=100)
    medium_pct: float = Field(ge=0, le=100)
    low_pct: float = Field(ge=0, le=100)
    max_daily_trade_amount: Optional[float] = Field(None, ge=0)

    @model_validator(mode="after")
    def pcts_must_sum_to_100(self) -> "RiskSettingsRequest":
        total = self.high_pct + self.medium_pct + self.low_pct
        if abs(total - 100.0) > 0.01:
            raise ValueError(
                f"Risk percentages must sum to 100 (got {total})."
            )
        return self


class AddHoldingRequest(BaseModel):
    security_id: str
    quantity: int = Field(gt=0)
    buy_price: float = Field(gt=0)
    fees: float = Field(0.0, ge=0)
    taxes: float = Field(0.0, ge=0)


class SellHoldingRequest(BaseModel):
    security_id: str
    quantity: int = Field(gt=0)
    sell_price: float = Field(gt=0)
    fees: float = Field(0.0, ge=0)
    taxes: float = Field(0.0, ge=0)


class CreateWatchlistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class AddWatchlistItemRequest(BaseModel):
    security_id: str
    notes: Optional[str] = Field(None, max_length=500)
    alert_above: Optional[float] = Field(None, ge=0)
    alert_below: Optional[float] = Field(None, ge=0)


# ── Response schemas ─────────────────────────────────────────────────────────


class RiskSettingsResponse(BaseModel):
    high_pct: float
    medium_pct: float
    low_pct: float
    max_daily_trade_amount: Optional[float] = None
    preferred_currency: str


class HoldingResponse(BaseModel):
    security_id: str
    symbol: str
    exchange_code: str
    quantity: int
    avg_buy_price: float
    current_price: Optional[float] = None
    invested: float
    current_value: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    first_buy_date: Optional[date] = None
    last_transaction_date: Optional[date] = None


class TransactionResponse(BaseModel):
    transaction_id: str
    type: str
    symbol: str
    exchange_code: str
    quantity: int
    price: float
    total: float
    fees: float
    taxes: float
    net_amount: float
    currency: str
    executed_at: datetime


class PortfolioSummary(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    currency: str
    total_invested: float
    current_value: float
    total_pnl: float
    total_pnl_pct: Optional[float] = None
    holding_count: int
    cash_balance: float
    created_at: datetime


class PortfolioDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    currency: str
    is_default: bool
    total_invested: float
    current_value: float
    total_realized_pnl: float
    cash_balance: float
    holding_count: int
    transaction_count: int
    holdings: list[HoldingResponse]
    recent_transactions: list[TransactionResponse]
    created_at: datetime
    updated_at: datetime


class PortfolioSnapshotResponse(BaseModel):
    date: date
    total_invested: float
    current_value: float
    realized_pnl: float
    unrealized_pnl: float
    holding_count: int
    cash_balance: float


class WatchlistItemResponse(BaseModel):
    security_id: str
    symbol: str
    exchange_code: str
    added_at: datetime
    notes: Optional[str] = None
    alert_above: Optional[float] = None
    alert_below: Optional[float] = None


class WatchlistResponse(BaseModel):
    id: str
    name: str
    is_default: bool
    items: list[WatchlistItemResponse]
    item_count: int
    created_at: datetime
    updated_at: datetime
