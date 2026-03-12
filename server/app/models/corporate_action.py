from datetime import date, datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class ActionType(str, Enum):
    DIVIDEND = "dividend"
    STOCK_SPLIT = "stock_split"
    BONUS = "bonus"
    RIGHTS_ISSUE = "rights_issue"
    BUYBACK = "buyback"
    MERGER = "merger"
    DELISTING = "delisting"
    NAME_CHANGE = "name_change"


class CorporateAction(Document):
    security_id: Indexed(str)
    action_type: ActionType

    announcement_date: Optional[date] = None
    ex_date: Optional[Indexed(date)] = None
    record_date: Optional[date] = None
    payment_date: Optional[date] = None

    dividend_amount: Optional[float] = None
    dividend_currency: Optional[str] = None
    dividend_type: Optional[str] = None

    ratio_from: Optional[int] = None
    ratio_to: Optional[int] = None

    description: Optional[str] = None
    adjustment_factor: Optional[float] = None
    source: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "corporate_actions"
        indexes = [
            [("security_id", 1), ("ex_date", -1)],
            [("action_type", 1), ("ex_date", -1)],
        ]
