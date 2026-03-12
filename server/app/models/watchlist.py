from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class WatchlistItem(BaseModel):
    security_id: str
    symbol: str
    exchange_code: str
    added_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    alert_above: Optional[float] = None
    alert_below: Optional[float] = None


class Watchlist(Document):
    user_id: Indexed(str)
    name: str
    items: list[WatchlistItem] = Field(default_factory=list)
    is_default: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "watchlists"
        indexes = [
            [("user_id", 1)],
            [("items.security_id", 1)],
        ]
