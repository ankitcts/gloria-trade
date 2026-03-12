from datetime import date, datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class PriceHistoryDaily(Document):
    security_id: Indexed(str)
    date: Indexed(date)

    open: float
    high: float
    low: float
    close: float
    volume: int

    adj_open: Optional[float] = None
    adj_high: Optional[float] = None
    adj_low: Optional[float] = None
    adj_close: Optional[float] = None
    adj_volume: Optional[int] = None

    change: Optional[float] = None
    change_pct: Optional[float] = None
    vwap: Optional[float] = None

    no_of_shares: Optional[int] = None
    no_of_trades: Optional[int] = None
    total_turnover: Optional[float] = None
    deliverable_qty: Optional[int] = None
    pct_delivery_to_trade: Optional[float] = None
    spread_h_l: Optional[float] = None
    spread_c_o: Optional[float] = None

    exchange_code: Optional[str] = None
    data_source: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "price_history_daily"
        indexes = [
            [("security_id", 1), ("date", -1)],
            [("security_id", 1), ("date", 1)],
            [("date", -1)],
            [("exchange_code", 1), ("date", -1)],
        ]


class PriceTickIntraday(Document):
    security_id: Indexed(str)
    timestamp: Indexed(datetime)

    price: float
    volume: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None

    is_simulated: bool = False
    exchange_code: Optional[str] = None

    class Settings:
        name = "price_ticks_intraday"
        indexes = [
            [("security_id", 1), ("timestamp", -1)],
        ]
