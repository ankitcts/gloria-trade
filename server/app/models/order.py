from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderValidity(str, Enum):
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    GTD = "gtd"


class FillRecord(BaseModel):
    fill_id: str
    quantity: int
    price: float
    fees: float = 0.0
    filled_at: datetime


class Order(Document):
    user_id: Indexed(str)
    portfolio_id: str
    security_id: Indexed(str)

    symbol: str
    exchange_code: str
    security_name: Optional[str] = None

    order_type: OrderType
    side: OrderSide
    quantity: int
    filled_quantity: int = 0

    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    avg_fill_price: Optional[float] = None

    validity: OrderValidity = OrderValidity.DAY
    valid_until: Optional[datetime] = None

    status: OrderStatus = OrderStatus.PENDING

    fills: list[FillRecord] = Field(default_factory=list)

    total_amount: Optional[float] = None
    total_fees: float = 0.0
    total_taxes: float = 0.0
    currency: str

    realized_pnl: Optional[float] = None

    is_simulated: bool = False
    trigger_source: Optional[str] = None
    trigger_details: Optional[dict] = None

    placed_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    notification_sent: bool = False
    notification_sent_at: Optional[datetime] = None

    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "orders"
        indexes = [
            [("user_id", 1), ("placed_at", -1)],
            [("user_id", 1), ("status", 1)],
            [("security_id", 1), ("placed_at", -1)],
            [("portfolio_id", 1), ("placed_at", -1)],
            [("status", 1), ("validity", 1), ("valid_until", 1)],
            [("notification_sent", 1), ("status", 1)],
        ]
