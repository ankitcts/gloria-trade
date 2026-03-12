from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class SentimentSource(str, Enum):
    NEWS_ARTICLE = "news_article"
    TWITTER = "twitter"
    REDDIT = "reddit"
    STOCKTWITS = "stocktwits"
    ANALYST_REPORT = "analyst_report"
    EARNINGS_CALL = "earnings_call"
    RSS_FEED = "rss_feed"


class SentimentLabel(str, Enum):
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


class SentimentRecord(Document):
    security_id: Optional[Indexed(str)] = None
    symbol: Optional[str] = None

    source_type: Indexed(SentimentSource)
    source_name: Optional[str] = None
    source_url: Optional[str] = None

    title: Optional[str] = None
    content_snippet: Optional[str] = None

    sentiment_score: float
    sentiment_label: SentimentLabel
    confidence: float

    is_market_wide: bool = False
    exchange_code: Optional[str] = None
    sector: Optional[str] = None

    model_name: Optional[str] = None
    model_version: Optional[str] = None

    published_at: Indexed(datetime)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "sentiment_records"
        indexes = [
            [("security_id", 1), ("published_at", -1)],
            [("source_type", 1), ("published_at", -1)],
            [("is_market_wide", 1), ("published_at", -1)],
            [("security_id", 1), ("published_at", -1), ("source_type", 1)],
        ]
