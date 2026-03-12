from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.models.user import User
from app.models.user_session import UserSession
from app.models.market import Country, Exchange
from app.models.security import Security
from app.models.corporate_action import CorporateAction
from app.models.price_history import PriceHistoryDaily, PriceTickIntraday
from app.models.portfolio import Portfolio
from app.models.watchlist import Watchlist
from app.models.order import Order
from app.models.sentiment import SentimentRecord
from app.models.ml import MLModel, MLPrediction
from app.models.config import SystemConfig

ALL_DOCUMENT_MODELS = [
    User,
    UserSession,
    Country,
    Exchange,
    Security,
    CorporateAction,
    PriceHistoryDaily,
    PriceTickIntraday,
    Portfolio,
    Watchlist,
    Order,
    SentimentRecord,
    MLModel,
    MLPrediction,
    SystemConfig,
]

_client: AsyncIOMotorClient | None = None


async def init_db():
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    await init_beanie(
        database=_client[settings.mongodb_db_name],
        document_models=ALL_DOCUMENT_MODELS,
    )


async def close_db():
    global _client
    if _client:
        _client.close()
