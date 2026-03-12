from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class Country(Document):
    code: Indexed(str, unique=True)
    name: str
    default_currency: str
    regulatory_body: Optional[str] = None
    market_timezone: str
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "countries"


class DayOfWeek(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class TradingSession(BaseModel):
    name: str
    open_time: str
    close_time: str


class MarketHoliday(BaseModel):
    date: str
    name: str
    is_half_day: bool = False
    half_day_close_time: Optional[str] = None


class Exchange(Document):
    code: Indexed(str, unique=True)
    name: str
    mic_code: Optional[str] = None
    country_code: Indexed(str)
    currency: str
    timezone: str

    trading_days: list[DayOfWeek] = Field(
        default_factory=lambda: [
            DayOfWeek.MONDAY,
            DayOfWeek.TUESDAY,
            DayOfWeek.WEDNESDAY,
            DayOfWeek.THURSDAY,
            DayOfWeek.FRIDAY,
        ]
    )
    sessions: list[TradingSession] = Field(default_factory=list)
    holidays: list[MarketHoliday] = Field(default_factory=list)

    lot_size: int = 1
    tick_size: float = 0.01
    circuit_breaker_pct: Optional[float] = None

    is_active: bool = True
    data_source: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "exchanges"
