from datetime import date, datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT_ADJUSTMENT = "split_adjustment"
    BONUS_CREDIT = "bonus_credit"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"


class Holding(BaseModel):
    security_id: str
    symbol: str
    exchange_code: str

    quantity: int
    avg_buy_price: float
    current_price: Optional[float] = None

    invested_value: float
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None

    first_buy_date: Optional[date] = None
    last_transaction_date: Optional[date] = None


class Transaction(BaseModel):
    transaction_id: str
    transaction_type: TransactionType
    security_id: str
    symbol: str
    exchange_code: str

    quantity: int
    price: float
    total_amount: float
    fees: float = 0.0
    taxes: float = 0.0
    net_amount: float

    currency: str
    order_id: Optional[str] = None
    notes: Optional[str] = None

    executed_at: datetime


class PortfolioSnapshot(BaseModel):
    date: date
    total_invested: float
    total_current_value: float
    total_realized_pnl: float
    total_unrealized_pnl: float
    holding_count: int
    cash_balance: float


class Portfolio(Document):
    user_id: Indexed(str)
    name: str
    description: Optional[str] = None
    currency: str = "INR"
    is_default: bool = False
    is_active: bool = True

    holdings: list[Holding] = Field(default_factory=list)

    total_invested: float = 0.0
    total_current_value: float = 0.0
    total_realized_pnl: float = 0.0
    cash_balance: float = 0.0

    recent_transactions: list[Transaction] = Field(default_factory=list)
    transaction_count: int = 0

    snapshots: list[PortfolioSnapshot] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "portfolios"
        indexes = [
            [("user_id", 1), ("is_active", 1)],
            [("holdings.security_id", 1)],
        ]
