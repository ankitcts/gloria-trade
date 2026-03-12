from datetime import date, datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    DEACTIVATED = "deactivated"


class KYCStatus(str, Enum):
    NOT_STARTED = "not_started"
    DOCUMENTS_SUBMITTED = "documents_submitted"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Permission(str, Enum):
    TRADE_EXECUTE = "trade:execute"
    TRADE_VIEW = "trade:view"
    PORTFOLIO_MANAGE = "portfolio:manage"
    PORTFOLIO_VIEW = "portfolio:view"
    MARKET_DATA_REALTIME = "market_data:realtime"
    MARKET_DATA_HISTORICAL = "market_data:historical"
    SENTIMENT_VIEW = "sentiment:view"
    PREDICTIONS_VIEW = "predictions:view"
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"


ROLE_PERMISSIONS: dict[UserRole, list[Permission]] = {
    UserRole.ADMIN: list(Permission),
    UserRole.TRADER: [
        Permission.TRADE_EXECUTE,
        Permission.TRADE_VIEW,
        Permission.PORTFOLIO_MANAGE,
        Permission.PORTFOLIO_VIEW,
        Permission.MARKET_DATA_REALTIME,
        Permission.MARKET_DATA_HISTORICAL,
        Permission.SENTIMENT_VIEW,
        Permission.PREDICTIONS_VIEW,
    ],
    UserRole.ANALYST: [
        Permission.TRADE_VIEW,
        Permission.PORTFOLIO_VIEW,
        Permission.MARKET_DATA_REALTIME,
        Permission.MARKET_DATA_HISTORICAL,
        Permission.SENTIMENT_VIEW,
        Permission.PREDICTIONS_VIEW,
    ],
    UserRole.VIEWER: [
        Permission.TRADE_VIEW,
        Permission.PORTFOLIO_VIEW,
        Permission.MARKET_DATA_HISTORICAL,
    ],
}


class KYCDetail(BaseModel):
    status: KYCStatus = KYCStatus.NOT_STARTED
    document_type: Optional[str] = None
    document_number_hash: Optional[str] = None
    submitted_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    reviewer_id: Optional[str] = None


class Address(BaseModel):
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country_code: str


class RiskProfile(BaseModel):
    high_pct: float = 0.0
    medium_pct: float = 0.0
    low_pct: float = 0.0
    max_daily_trade_amount: Optional[float] = None
    preferred_currency: str = "USD"


class User(Document):
    # Identity
    email: Indexed(str, unique=True)
    phone: Optional[Indexed(str, unique=True)] = None
    password_hash: str

    # Profile
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[Address] = None
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    preferred_locale: str = "en-US"

    # Access Control
    role: UserRole = UserRole.VIEWER
    extra_permissions: list[Permission] = Field(default_factory=list)

    # Status
    account_status: Indexed(AccountStatus) = AccountStatus.PENDING_VERIFICATION
    kyc: KYCDetail = Field(default_factory=KYCDetail)
    email_verified: bool = False
    phone_verified: bool = False

    # Trading Preferences
    risk_profile: RiskProfile = Field(default_factory=RiskProfile)
    default_exchange_code: Optional[str] = None

    # Audit
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            [("first_name", "text"), ("last_name", "text"), ("email", "text")],
            [("account_status", 1), ("role", 1)],
            [("kyc.status", 1)],
        ]
