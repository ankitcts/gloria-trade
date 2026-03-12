I now have a thorough understanding of the existing codebase. Let me compile the comprehensive schema design.

---

# Gloria-Trade: Comprehensive MongoDB Schema Design with Beanie ODM

## Analysis of Existing Codebase

The current system is a Flask + pymongo application with:
- **No structured models** -- all MongoDB access is done through a raw `DBCollection` wrapper around pymongo
- **Collections identified**: `securities_list`, `equity_risk_matrix`, `profit_matrix`, `ticker_notifications`, `user_trade_risk_assignment`, and dynamically-created per-security historical data collections (pattern: `{TYPE}_{CODE}_historical_data`)
- **Current data**: BSE stocks (CSV with `description`, `code`, `type`), NSE stocks (JSON with `type`, `code`, `name`, `description`), OHLCV price data from Quandl
- **ML pipeline**: LSTM model for price prediction, SMA-based buy/sell signals, risk analysis (simple/log returns)
- **User model**: Hardcoded stub with `guid`, `name`, `role`
- **Trade simulation**: Buy/sell signal generation with profit/loss percent thresholds, notifications via Socket.IO

The migration to FastAPI + Beanie requires replacing all of this with strongly-typed Pydantic Document models.

---

## Schema Architecture Overview

The design uses **15 primary collections** organized into 5 domains:

| Domain | Collections |
|--------|-------------|
| **Identity** | `users`, `user_sessions` |
| **Market Structure** | `countries`, `exchanges`, `securities`, `corporate_actions` |
| **Market Data** | `price_history_daily`, `price_ticks_intraday`, `quote_snapshots` |
| **Trading** | `portfolios`, `orders`, `trade_executions`, `watchlists` |
| **Intelligence** | `sentiment_records`, `ml_predictions`, `ml_models` |

---

## Collection 1: `users`

### Beanie Document Model

```python
# File: server/app/models/user.py

from datetime import datetime, date
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


class KYCDetail(BaseModel):
    status: KYCStatus = KYCStatus.NOT_STARTED
    document_type: Optional[str] = None          # "passport", "drivers_license", "aadhaar", "pan_card"
    document_number_hash: Optional[str] = None   # hashed, never store plaintext
    submitted_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    reviewer_id: Optional[str] = None            # admin user_id who reviewed


class Address(BaseModel):
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country_code: str                            # ISO 3166-1 alpha-2: "IN", "US"


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


# Role-to-permission mapping (application logic, not stored per-user)
ROLE_PERMISSIONS: dict[UserRole, list[Permission]] = {
    UserRole.ADMIN: list(Permission),
    UserRole.TRADER: [
        Permission.TRADE_EXECUTE, Permission.TRADE_VIEW,
        Permission.PORTFOLIO_MANAGE, Permission.PORTFOLIO_VIEW,
        Permission.MARKET_DATA_REALTIME, Permission.MARKET_DATA_HISTORICAL,
        Permission.SENTIMENT_VIEW, Permission.PREDICTIONS_VIEW,
    ],
    UserRole.ANALYST: [
        Permission.TRADE_VIEW, Permission.PORTFOLIO_VIEW,
        Permission.MARKET_DATA_REALTIME, Permission.MARKET_DATA_HISTORICAL,
        Permission.SENTIMENT_VIEW, Permission.PREDICTIONS_VIEW,
    ],
    UserRole.VIEWER: [
        Permission.TRADE_VIEW, Permission.PORTFOLIO_VIEW,
        Permission.MARKET_DATA_HISTORICAL,
    ],
}


class RiskProfile(BaseModel):
    """User's trading risk allocation preferences."""
    high_pct: float = 0.0     # 0-100
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
    default_exchange_code: Optional[str] = None    # e.g. "NSE"
    
    # Audit
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            # Text search on name fields
            [
                ("first_name", "text"),
                ("last_name", "text"),
                ("email", "text"),
            ],
            # Compound: status + role for admin queries
            [
                ("account_status", 1),
                ("role", 1),
            ],
            # KYC filtering
            [
                ("kyc.status", 1),
            ],
        ]
```

### Index Definitions
- **Unique** on `email`, `phone`
- **Compound** on `(account_status, role)` for admin dashboards filtering users by status and role
- **Text** on `(first_name, last_name, email)` for user search
- **Single** on `kyc.status` for KYC queue processing

### Example Document (JSON)
```json
{
  "_id": "665a1b2c3d4e5f6a7b8c9d0e",
  "email": "trader@gloriatrade.com",
  "phone": "+919876543210",
  "password_hash": "$2b$12$...",
  "first_name": "Ankit",
  "last_name": "Khandelwal",
  "display_name": "AnkitK",
  "date_of_birth": "1990-05-15",
  "address": {
    "line1": "123 Trading Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001",
    "country_code": "IN"
  },
  "timezone": "Asia/Kolkata",
  "preferred_locale": "en-IN",
  "role": "trader",
  "extra_permissions": [],
  "account_status": "active",
  "kyc": {
    "status": "verified",
    "document_type": "pan_card",
    "document_number_hash": "sha256:...",
    "submitted_at": "2024-01-10T09:00:00Z",
    "verified_at": "2024-01-12T14:30:00Z",
    "rejection_reason": null,
    "reviewer_id": "665a1b2c3d4e5f6a7b000001"
  },
  "email_verified": true,
  "phone_verified": true,
  "risk_profile": {
    "high_pct": 20.0,
    "medium_pct": 50.0,
    "low_pct": 30.0,
    "max_daily_trade_amount": 100000.0,
    "preferred_currency": "INR"
  },
  "default_exchange_code": "NSE",
  "last_login_at": "2024-06-01T08:15:00Z",
  "login_count": 247,
  "created_at": "2024-01-05T12:00:00Z",
  "updated_at": "2024-06-01T08:15:00Z"
}
```

### Relationships
- Referenced by `portfolios.user_id`, `orders.user_id`, `watchlists.user_id`, `user_sessions.user_id`

### Estimated Size & Growth
- ~2-4 KB per document
- Slow growth: depends on user signups (hundreds to low thousands initially)

### Special Considerations
- `password_hash` must never be returned in API responses; use Beanie's `response_model_exclude` or a separate projection
- `phone` unique index is sparse (optional field)
- `risk_profile` is embedded because it is 1:1 and always read with the user

---

## Collection 2: `user_sessions`

### Beanie Document Model

```python
# File: server/app/models/user_session.py

from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, Link
from pydantic import Field


class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class UserSession(Document):
    user_id: Indexed(str)
    session_token_hash: Indexed(str, unique=True)
    refresh_token_hash: Optional[str] = None
    
    status: SessionStatus = SessionStatus.ACTIVE
    
    # Device / context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None           # "web", "mobile_ios", "mobile_android"
    geo_location: Optional[str] = None          # "Mumbai, IN"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Indexed(datetime)               # TTL anchor
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None

    class Settings:
        name = "user_sessions"
        indexes = [
            # TTL index: auto-delete expired sessions after 30 days
            [("expires_at", 1)],   # TTL set via pymongo IndexModel with expireAfterSeconds=0
            # User's active sessions
            [("user_id", 1), ("status", 1)],
        ]
```

### Index Definitions
- **TTL** on `expires_at` with `expireAfterSeconds=0` -- MongoDB auto-deletes documents once `expires_at` passes
- **Compound** on `(user_id, status)` for listing a user's active sessions
- **Unique** on `session_token_hash`

### Example Document
```json
{
  "_id": "665b...",
  "user_id": "665a1b2c3d4e5f6a7b8c9d0e",
  "session_token_hash": "sha256:abc123...",
  "refresh_token_hash": "sha256:def456...",
  "status": "active",
  "ip_address": "203.0.113.42",
  "user_agent": "Mozilla/5.0 ...",
  "device_type": "web",
  "geo_location": "Mumbai, IN",
  "created_at": "2024-06-01T08:15:00Z",
  "expires_at": "2024-06-08T08:15:00Z",
  "last_activity_at": "2024-06-01T10:30:00Z",
  "revoked_at": null
}
```

### Relationships
- `user_id` references `users._id`

### Estimated Size & Growth
- ~0.5-1 KB per document
- High churn: sessions created on every login, TTL auto-cleans
- Peak: (active_users * avg_devices) active documents at any time

### Special Considerations
- **TTL index** is critical -- do not skip this; it prevents unbounded collection growth
- Store only hashes of tokens, never raw tokens

---

## Collection 3: `countries`

### Beanie Document Model

```python
# File: server/app/models/market.py

from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class Country(Document):
    code: Indexed(str, unique=True)              # ISO 3166-1 alpha-2: "IN", "US"
    name: str                                     # "India", "United States"
    default_currency: str                         # ISO 4217: "INR", "USD"
    flag_emoji: Optional[str] = None              # "🇮🇳"
    regulatory_body: Optional[str] = None         # "SEBI", "SEC"
    market_timezone: str                          # "Asia/Kolkata", "America/New_York"
    is_active: bool = True
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "countries"
```

### Index Definitions
- **Unique** on `code`
- Small collection, no additional indexes needed

### Example Document
```json
{
  "_id": "...",
  "code": "IN",
  "name": "India",
  "default_currency": "INR",
  "flag_emoji": null,
  "regulatory_body": "SEBI",
  "market_timezone": "Asia/Kolkata",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Relationships
- Referenced by `exchanges.country_code`

### Estimated Size & Growth
- ~0.3 KB per document, 2-5 documents total (static/seed data)

---

## Collection 4: `exchanges`

### Beanie Document Model

```python
# File: server/app/models/market.py (continued)

from enum import Enum


class DayOfWeek(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class TradingSession(BaseModel):
    """A single trading session window."""
    name: str                    # "Regular", "Pre-Market", "After-Hours"
    open_time: str               # "09:15" (local exchange time)
    close_time: str              # "15:30"


class MarketHoliday(BaseModel):
    date: str                    # "2024-08-15" (ISO date string)
    name: str                    # "Independence Day"
    is_half_day: bool = False
    half_day_close_time: Optional[str] = None


class Exchange(Document):
    code: Indexed(str, unique=True)              # "NSE", "BSE", "NASDAQ", "NYSE", "AMEX"
    name: str                                     # "National Stock Exchange of India"
    mic_code: Optional[str] = None               # ISO 10383 MIC: "XNSE", "XBOM", "XNAS", "XNYS"
    country_code: Indexed(str)                   # "IN", "US"
    currency: str                                 # "INR", "USD"
    timezone: str                                 # "Asia/Kolkata", "America/New_York"
    
    # Trading schedule
    trading_days: list[DayOfWeek] = Field(
        default_factory=lambda: [
            DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
            DayOfWeek.THURSDAY, DayOfWeek.FRIDAY,
        ]
    )
    sessions: list[TradingSession] = Field(default_factory=list)
    holidays: list[MarketHoliday] = Field(default_factory=list)  # current year; refresh annually
    
    # Market rules
    lot_size: int = 1
    tick_size: float = 0.01
    circuit_breaker_pct: Optional[float] = None  # e.g. 20.0 for 20%
    
    is_active: bool = True
    data_source: Optional[str] = None            # "quandl", "alpha_vantage", "yahoo_finance"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "exchanges"
```

### Index Definitions
- **Unique** on `code`
- **Single** on `country_code` for listing exchanges by country

### Example Document
```json
{
  "_id": "...",
  "code": "NSE",
  "name": "National Stock Exchange of India",
  "mic_code": "XNSE",
  "country_code": "IN",
  "currency": "INR",
  "timezone": "Asia/Kolkata",
  "trading_days": [0, 1, 2, 3, 4],
  "sessions": [
    {"name": "Pre-Open", "open_time": "09:00", "close_time": "09:15"},
    {"name": "Regular", "open_time": "09:15", "close_time": "15:30"},
    {"name": "Post-Close", "open_time": "15:40", "close_time": "16:00"}
  ],
  "holidays": [
    {"date": "2024-08-15", "name": "Independence Day", "is_half_day": false},
    {"date": "2024-10-02", "name": "Gandhi Jayanti", "is_half_day": false}
  ],
  "lot_size": 1,
  "tick_size": 0.05,
  "circuit_breaker_pct": 20.0,
  "is_active": true,
  "data_source": "quandl",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-06-01T00:00:00Z"
}
```

### Relationships
- `country_code` references `countries.code`
- Referenced by `securities.listings[].exchange_code`

### Estimated Size & Growth
- ~2-5 KB per document (holidays array grows, but refreshed annually)
- 5 documents (BSE, NSE, NASDAQ, NYSE, AMEX)

### Special Considerations
- `holidays` is embedded because it is bounded (~20-25 per year) and always accessed with the exchange
- Holidays should be refreshed at start of each year; old years can be pruned or archived

---

## Collection 5: `securities`

This is the **Security Master** -- the canonical record for every tradable instrument. It replaces the current `securities_list` and `equity_risk_matrix` collections.

### Beanie Document Model

```python
# File: server/app/models/security.py

from datetime import datetime, date
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class SecurityType(str, Enum):
    EQUITY = "equity"
    ETF = "etf"
    INDEX = "index"
    MUTUAL_FUND = "mutual_fund"
    BOND = "bond"
    COMMODITY = "commodity"
    DERIVATIVE = "derivative"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Sector(str, Enum):
    TECHNOLOGY = "technology"
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    CONSUMER_CYCLICAL = "consumer_cyclical"
    CONSUMER_DEFENSIVE = "consumer_defensive"
    INDUSTRIALS = "industrials"
    ENERGY = "energy"
    UTILITIES = "utilities"
    REAL_ESTATE = "real_estate"
    COMMUNICATION_SERVICES = "communication_services"
    BASIC_MATERIALS = "basic_materials"
    OTHER = "other"


class ExchangeListing(BaseModel):
    """One listing of this security on a specific exchange."""
    exchange_code: str                         # "NSE", "BSE", "NASDAQ"
    ticker: str                                # "SBIN", "BOM500112", "AAPL"
    is_primary: bool = False
    listing_date: Optional[date] = None
    delisting_date: Optional[date] = None
    lot_size: int = 1
    is_active: bool = True


class Fundamentals(BaseModel):
    """Fundamental financial metrics; updated periodically."""
    market_cap: Optional[float] = None          # in security's currency
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield_pct: Optional[float] = None
    book_value: Optional[float] = None
    face_value: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    avg_volume_30d: Optional[int] = None
    beta: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe_pct: Optional[float] = None
    updated_at: Optional[datetime] = None


class QuoteSnapshot(BaseModel):
    """Latest price snapshot; updated by data ingestion pipeline."""
    last_price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    prev_close: Optional[float] = None
    volume: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    timestamp: Optional[datetime] = None


class Security(Document):
    # Identifiers
    symbol: Indexed(str)                         # Primary ticker: "SBIN", "AAPL"
    name: str                                     # "State Bank of India", "Apple Inc."
    isin: Optional[Indexed(str, unique=True)] = None  # "INE062A01020" (globally unique)
    security_type: SecurityType = SecurityType.EQUITY
    
    # Classification
    sector: Optional[Sector] = None
    industry: Optional[str] = None               # Free-text: "Private Banks", "Consumer Electronics"
    description: Optional[str] = None
    
    # Exchange listings (embedded, max ~5 per security)
    listings: list[ExchangeListing] = Field(default_factory=list)
    primary_exchange_code: str                    # "NSE"
    currency: str                                 # "INR"
    country_code: str                             # "IN"
    
    # Fundamentals
    fundamentals: Fundamentals = Field(default_factory=Fundamentals)
    
    # Real-time quote
    quote: QuoteSnapshot = Field(default_factory=QuoteSnapshot)
    
    # Risk assessment (from the existing equity_risk_matrix)
    computed_risk: Optional[RiskLevel] = None
    risk_updated_at: Optional[datetime] = None
    
    # Data availability
    data_source: Optional[str] = None            # "quandl", "alpha_vantage"
    data_source_id: Optional[str] = None         # "BSE/BOM500112", "WIKI/AAPL"
    has_historical_data: bool = False
    historical_data_from: Optional[date] = None
    historical_data_to: Optional[date] = None
    
    # Lifecycle
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "securities"
        indexes = [
            # Primary lookup: symbol + exchange
            [("symbol", 1), ("primary_exchange_code", 1)],
            # Filter by sector, type
            [("sector", 1), ("security_type", 1)],
            # Listings subdocument: find by exchange ticker
            [("listings.exchange_code", 1), ("listings.ticker", 1)],
            # Country + active
            [("country_code", 1), ("is_active", 1)],
            # Text search
            [("name", "text"), ("symbol", "text")],
            # Risk filtering
            [("computed_risk", 1)],
        ]
```

### Index Definitions
- **Compound** on `(symbol, primary_exchange_code)` -- the primary lookup pattern
- **Compound** on `(sector, security_type)` for filtered browsing
- **Compound** on `(listings.exchange_code, listings.ticker)` for cross-exchange lookups
- **Compound** on `(country_code, is_active)` for country-scoped active security lists
- **Text** on `(name, symbol)` for search-as-you-type
- **Unique sparse** on `isin`

### Example Document
```json
{
  "_id": "665c...",
  "symbol": "SBIN",
  "name": "State Bank of India",
  "isin": "INE062A01020",
  "security_type": "equity",
  "sector": "financial_services",
  "industry": "Public Banks",
  "description": "State Bank of India is an Indian multinational...",
  "listings": [
    {
      "exchange_code": "NSE",
      "ticker": "SBIN",
      "is_primary": true,
      "listing_date": "1995-03-01",
      "lot_size": 1,
      "is_active": true
    },
    {
      "exchange_code": "BSE",
      "ticker": "BOM500112",
      "is_primary": false,
      "listing_date": "1993-01-01",
      "lot_size": 1,
      "is_active": true
    }
  ],
  "primary_exchange_code": "NSE",
  "currency": "INR",
  "country_code": "IN",
  "fundamentals": {
    "market_cap": 5420000000000,
    "pe_ratio": 10.5,
    "eps": 62.34,
    "dividend_yield_pct": 1.8,
    "week_52_high": 690.0,
    "week_52_low": 430.0,
    "avg_volume_30d": 15000000,
    "beta": 1.12,
    "updated_at": "2024-06-01T00:00:00Z"
  },
  "quote": {
    "last_price": 655.50,
    "change": 12.30,
    "change_pct": 1.91,
    "open": 645.00,
    "high": 658.00,
    "low": 642.00,
    "close": 655.50,
    "prev_close": 643.20,
    "volume": 18234567,
    "timestamp": "2024-06-01T15:30:00Z"
  },
  "computed_risk": "medium",
  "risk_updated_at": "2024-05-28T12:00:00Z",
  "data_source": "quandl",
  "data_source_id": "BSE/BOM500112",
  "has_historical_data": true,
  "historical_data_from": "2015-01-01",
  "historical_data_to": "2024-06-01",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-06-01T15:30:00Z"
}
```

### Relationships
- `primary_exchange_code` and `listings[].exchange_code` reference `exchanges.code`
- `country_code` references `countries.code`
- Referenced by `price_history_daily.security_id`, `orders.security_id`, `portfolios.holdings[].security_id`, `sentiment_records.security_id`, `ml_predictions.security_id`

### Estimated Size & Growth
- ~2-5 KB per document
- ~10,000 - 50,000 documents (all BSE + NSE + US exchange listings)
- Growth: slow (new IPOs)

### Special Considerations
- `listings` is embedded because a security lists on at most ~5 exchanges
- `quote` is embedded and updated frequently by a data pipeline; consider using `$set` on just the `quote` sub-document for efficiency
- `fundamentals` updates daily/weekly, not real-time
- This replaces the current anti-pattern of creating a separate collection per security (`BSE_BOM500112_historical_data`)

---

## Collection 6: `corporate_actions`

### Beanie Document Model

```python
# File: server/app/models/corporate_action.py

from datetime import datetime, date
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
    action_type: Indexed(ActionType)
    
    # Dates
    announcement_date: Optional[date] = None
    ex_date: Optional[Indexed(date)] = None       # the key date for price adjustment
    record_date: Optional[date] = None
    payment_date: Optional[date] = None
    
    # Dividend-specific
    dividend_amount: Optional[float] = None
    dividend_currency: Optional[str] = None
    dividend_type: Optional[str] = None          # "interim", "final", "special"
    
    # Split/bonus-specific
    ratio_from: Optional[int] = None             # split: old face value or share count
    ratio_to: Optional[int] = None               # split: new face value or share count
    
    # General
    description: Optional[str] = None
    adjustment_factor: Optional[float] = None    # price adjustment multiplier
    source: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "corporate_actions"
        indexes = [
            [("security_id", 1), ("ex_date", -1)],
            [("action_type", 1), ("ex_date", -1)],
        ]
```

### Index Definitions
- **Compound** on `(security_id, ex_date desc)` -- primary lookup: all actions for a security ordered by date
- **Compound** on `(action_type, ex_date desc)` -- find all dividends/splits in a date range

### Example Document
```json
{
  "_id": "...",
  "security_id": "665c...",
  "action_type": "stock_split",
  "announcement_date": "2024-09-01",
  "ex_date": "2024-09-15",
  "record_date": "2024-09-16",
  "ratio_from": 1,
  "ratio_to": 5,
  "description": "Stock split 1:5, face value reduced from Rs 10 to Rs 2",
  "adjustment_factor": 0.2,
  "created_at": "2024-09-02T00:00:00Z",
  "updated_at": "2024-09-02T00:00:00Z"
}
```

### Relationships
- `security_id` references `securities._id`

### Estimated Size & Growth
- ~0.5-1 KB per document
- ~2-5 actions per security per year; ~50,000-250,000 total over time
- Moderate growth

---

## Collection 7: `price_history_daily`

This is the **highest-volume collection** in the system. It replaces all the dynamically-created `{TYPE}_{CODE}_historical_data` collections.

### Beanie Document Model

```python
# File: server/app/models/price_history.py

from datetime import datetime, date
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class PriceHistoryDaily(Document):
    """
    One document per security per trading day.
    This is the core time-series collection for OHLCV data.
    """
    security_id: Indexed(str)
    date: Indexed(date)
    
    # OHLCV
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    # Adjusted prices (post-split/dividend adjustments)
    adj_open: Optional[float] = None
    adj_high: Optional[float] = None
    adj_low: Optional[float] = None
    adj_close: Optional[float] = None
    adj_volume: Optional[int] = None
    
    # Derived metrics (populated by data pipeline)
    change: Optional[float] = None               # close - prev_close
    change_pct: Optional[float] = None
    vwap: Optional[float] = None                 # Volume Weighted Average Price
    
    # BSE-specific fields from existing data
    no_of_shares: Optional[int] = None
    no_of_trades: Optional[int] = None
    total_turnover: Optional[float] = None
    deliverable_qty: Optional[int] = None
    pct_delivery_to_trade: Optional[float] = None
    spread_h_l: Optional[float] = None
    spread_c_o: Optional[float] = None
    
    # Source tracking
    exchange_code: Optional[str] = None          # which exchange this data came from
    data_source: Optional[str] = None            # "quandl", "yahoo_finance"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "price_history_daily"
        indexes = [
            # PRIMARY query pattern: get price history for a security
            # Compound unique ensures no duplicate data points
            {
                "keys": [("security_id", 1), ("date", -1)],
                "unique": True,
            },
            # Range scans for charting: security + date range
            [("security_id", 1), ("date", 1)],
            # Cross-security queries by date (market-wide analysis)
            [("date", -1)],
            # Filter by exchange for exchange-specific analysis
            [("exchange_code", 1), ("date", -1)],
        ]
```

### Index Definitions
- **Compound unique** on `(security_id, date)` -- prevents duplicates, primary query pattern
- **Compound** on `(security_id, date ASC)` -- forward scans for charting
- **Single** on `(date DESC)` -- cross-security market analysis
- **Compound** on `(exchange_code, date DESC)` -- exchange-specific bulk queries

### Example Document
```json
{
  "_id": "...",
  "security_id": "665c...",
  "date": "2024-05-31",
  "open": 643.00,
  "high": 658.00,
  "low": 640.50,
  "close": 655.50,
  "volume": 18234567,
  "adj_open": 643.00,
  "adj_high": 658.00,
  "adj_low": 640.50,
  "adj_close": 655.50,
  "adj_volume": 18234567,
  "change": 12.30,
  "change_pct": 1.91,
  "vwap": 649.75,
  "no_of_shares": 18234567,
  "no_of_trades": 432156,
  "total_turnover": 11856234500.0,
  "spread_h_l": 17.50,
  "spread_c_o": 12.50,
  "exchange_code": "NSE",
  "data_source": "quandl",
  "created_at": "2024-06-01T01:00:00Z"
}
```

### Relationships
- `security_id` references `securities._id`
- `exchange_code` references `exchanges.code`

### Estimated Size & Growth
- ~0.5-1 KB per document
- **Volume**: ~250 trading days/year * 10,000 securities = **2.5 million documents/year**
- After 5 years: ~12.5 million documents
- This is the largest collection and requires careful indexing

### Special Considerations
- **MongoDB Time-Series Collection**: Consider using MongoDB's native time-series collection feature (`timeseries` option in `createCollection`) with `timeField="date"` and `metaField="security_id"`. This provides automatic bucketing, compression, and optimized range queries. In Beanie, this requires creating the collection manually before the ODM initializes it.
- **Weekly/monthly aggregation**: Do NOT store separate weekly/monthly collections. Use MongoDB's aggregation pipeline with `$group` by `$isoWeek` or `$month` to compute on the fly, or use materialized views/caching for frequently accessed aggregations.
- `no_updated_at` intentionally: price history is immutable once written (append-only)

---

## Collection 8: `price_ticks_intraday`

### Beanie Document Model

```python
# File: server/app/models/price_history.py (continued)

from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class PriceTickIntraday(Document):
    """
    Intraday tick data for trading simulation.
    High volume -- use time-series collection or TTL to manage size.
    """
    security_id: Indexed(str)
    timestamp: Indexed(datetime)
    
    price: float
    volume: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    
    # Simulation metadata (from existing create_data_set.py)
    is_simulated: bool = False
    
    exchange_code: Optional[str] = None

    class Settings:
        name = "price_ticks_intraday"
        indexes = [
            # Primary query: ticks for a security in a time range
            {
                "keys": [("security_id", 1), ("timestamp", -1)],
            },
            # TTL: auto-delete ticks older than 90 days
            {
                "keys": [("timestamp", 1)],
                # expireAfterSeconds=7776000 (90 days)
            },
        ]
```

### Index Definitions
- **Compound** on `(security_id, timestamp DESC)` -- primary query pattern
- **TTL** on `timestamp` with `expireAfterSeconds=7776000` (90 days) to keep collection manageable

### Example Document
```json
{
  "_id": "...",
  "security_id": "665c...",
  "timestamp": "2024-06-01T09:15:01.234Z",
  "price": 645.25,
  "volume": 1523,
  "bid": 645.20,
  "ask": 645.30,
  "is_simulated": false,
  "exchange_code": "NSE"
}
```

### Relationships
- `security_id` references `securities._id`

### Estimated Size & Growth
- ~0.2-0.3 KB per document
- Potentially millions of documents per day if ingesting real tick data
- **TTL index** is mandatory to prevent unbounded growth

### Special Considerations
- **Time-series collection**: This is an ideal candidate for MongoDB's `timeseries` collection type with `timeField="timestamp"`, `metaField="security_id"`, `granularity="seconds"`
- For the current simulation use case (existing `create_data_set.py` generates ~400 ticks per simulation), volume is manageable
- For production real-time data feeds, consider a dedicated time-series database (InfluxDB, TimescaleDB) or MongoDB Atlas time-series with auto-bucketing

---

## Collection 9: `portfolios`

### Beanie Document Model

```python
# File: server/app/models/portfolio.py

from datetime import datetime, date
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
    """Current position in a security within a portfolio."""
    security_id: str
    symbol: str                                   # denormalized for display
    exchange_code: str
    
    quantity: int
    avg_buy_price: float                          # weighted average
    current_price: Optional[float] = None         # updated by quote pipeline
    
    # P&L
    invested_value: float                         # quantity * avg_buy_price
    current_value: Optional[float] = None         # quantity * current_price
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    
    first_buy_date: Optional[date] = None
    last_transaction_date: Optional[date] = None


class Transaction(BaseModel):
    """A single buy/sell/dividend event within a portfolio."""
    transaction_id: str                           # UUID
    transaction_type: TransactionType
    security_id: str
    symbol: str                                   # denormalized
    exchange_code: str
    
    quantity: int
    price: float                                  # per unit
    total_amount: float                           # quantity * price
    fees: float = 0.0
    taxes: float = 0.0
    net_amount: float                             # total_amount +/- fees/taxes
    
    currency: str
    order_id: Optional[str] = None                # link to the order that created this
    notes: Optional[str] = None
    
    executed_at: datetime


class PortfolioSnapshot(BaseModel):
    """Point-in-time snapshot for historical NAV tracking."""
    date: date
    total_invested: float
    total_current_value: float
    total_realized_pnl: float
    total_unrealized_pnl: float
    holding_count: int
    cash_balance: float


class Portfolio(Document):
    user_id: Indexed(str)
    name: str                                     # "My Growth Portfolio", "Retirement Fund"
    description: Optional[str] = None
    currency: str = "INR"
    is_default: bool = False
    is_active: bool = True
    
    # Current holdings (embedded, typically 10-100 per portfolio)
    holdings: list[Holding] = Field(default_factory=list)
    
    # Aggregate metrics
    total_invested: float = 0.0
    total_current_value: float = 0.0
    total_realized_pnl: float = 0.0
    cash_balance: float = 0.0
    
    # Transaction history
    # IMPORTANT: Transactions are stored in a separate sub-list but
    # for portfolios with many transactions (>500), we cap this and
    # rely on the 'orders' / 'trade_executions' collections for full history.
    recent_transactions: list[Transaction] = Field(default_factory=list)
    transaction_count: int = 0
    
    # Snapshots for charting portfolio value over time (last 365 days)
    # For longer history, use a dedicated aggregation pipeline.
    snapshots: list[PortfolioSnapshot] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "portfolios"
        indexes = [
            # User's portfolios
            [("user_id", 1), ("is_active", 1)],
            # Lookup holding by security across all portfolios (admin/analytics)
            [("holdings.security_id", 1)],
        ]
```

### Index Definitions
- **Compound** on `(user_id, is_active)` -- primary lookup: a user's active portfolios
- **Single** on `holdings.security_id` for cross-portfolio security queries

### Example Document
```json
{
  "_id": "665d...",
  "user_id": "665a1b2c3d4e5f6a7b8c9d0e",
  "name": "India Long-Term",
  "description": "Blue-chip Indian equities for long-term growth",
  "currency": "INR",
  "is_default": true,
  "is_active": true,
  "holdings": [
    {
      "security_id": "665c...",
      "symbol": "SBIN",
      "exchange_code": "NSE",
      "quantity": 200,
      "avg_buy_price": 520.0,
      "current_price": 655.50,
      "invested_value": 104000.0,
      "current_value": 131100.0,
      "unrealized_pnl": 27100.0,
      "unrealized_pnl_pct": 26.06,
      "first_buy_date": "2023-06-15",
      "last_transaction_date": "2024-03-10"
    }
  ],
  "total_invested": 104000.0,
  "total_current_value": 131100.0,
  "total_realized_pnl": 8500.0,
  "cash_balance": 25000.0,
  "recent_transactions": [
    {
      "transaction_id": "txn-uuid-001",
      "transaction_type": "buy",
      "security_id": "665c...",
      "symbol": "SBIN",
      "exchange_code": "NSE",
      "quantity": 100,
      "price": 520.0,
      "total_amount": 52000.0,
      "fees": 15.0,
      "taxes": 52.0,
      "net_amount": 52067.0,
      "currency": "INR",
      "order_id": "665e...",
      "executed_at": "2024-03-10T10:15:00Z"
    }
  ],
  "transaction_count": 15,
  "snapshots": [
    {
      "date": "2024-05-31",
      "total_invested": 104000.0,
      "total_current_value": 128000.0,
      "total_realized_pnl": 8500.0,
      "total_unrealized_pnl": 24000.0,
      "holding_count": 5,
      "cash_balance": 25000.0
    }
  ],
  "created_at": "2023-06-01T00:00:00Z",
  "updated_at": "2024-06-01T15:30:00Z"
}
```

### Relationships
- `user_id` references `users._id`
- `holdings[].security_id` references `securities._id`
- `recent_transactions[].order_id` references `orders._id`

### Estimated Size & Growth
- ~5-20 KB per document (depends on holding count and transaction history)
- Typically 1-5 portfolios per user
- **16 MB limit mitigation**: `recent_transactions` is capped at ~500 entries. Older transactions are queryable from `orders` collection. `snapshots` is capped at 365 entries (1 year). Older snapshots are accessible via aggregation on `price_history_daily`.

---

## Collection 10: `watchlists`

### Beanie Document Model

```python
# File: server/app/models/watchlist.py

from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class WatchlistItem(BaseModel):
    security_id: str
    symbol: str                                   # denormalized
    exchange_code: str
    added_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    alert_above: Optional[float] = None           # price alert: notify if price > X
    alert_below: Optional[float] = None           # price alert: notify if price < X


class Watchlist(Document):
    user_id: Indexed(str)
    name: str                                     # "Tech Stocks", "Breakout Candidates"
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
```

### Estimated Size & Growth
- ~1-5 KB per document
- 1-10 watchlists per user, 10-50 items each
- Well within 16 MB limit

---

## Collection 11: `orders`

### Beanie Document Model

```python
# File: server/app/models/order.py

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
    DAY = "day"                     # valid for the trading day
    GTC = "gtc"                     # good till cancelled
    IOC = "ioc"                     # immediate or cancel
    GTD = "gtd"                     # good till date


class FillRecord(BaseModel):
    """A partial or full fill against this order."""
    fill_id: str                    # UUID
    quantity: int
    price: float
    fees: float = 0.0
    filled_at: datetime


class Order(Document):
    # References
    user_id: Indexed(str)
    portfolio_id: str
    security_id: Indexed(str)
    
    # Denormalized for display / notification
    symbol: str
    exchange_code: str
    security_name: Optional[str] = None
    
    # Order specification
    order_type: OrderType
    side: OrderSide
    quantity: int
    filled_quantity: int = 0
    
    # Pricing
    limit_price: Optional[float] = None          # for LIMIT, STOP_LIMIT
    stop_price: Optional[float] = None           # for STOP_LOSS, STOP_LIMIT
    avg_fill_price: Optional[float] = None
    
    # Validity
    validity: OrderValidity = OrderValidity.DAY
    valid_until: Optional[datetime] = None       # for GTD
    
    # Status
    status: Indexed(OrderStatus) = OrderStatus.PENDING
    
    # Fills
    fills: list[FillRecord] = Field(default_factory=list)
    
    # Amounts
    total_amount: Optional[float] = None
    total_fees: float = 0.0
    total_taxes: float = 0.0
    currency: str
    
    # P&L (for sell orders)
    realized_pnl: Optional[float] = None
    
    # Simulation flag (from existing day-trade simulation)
    is_simulated: bool = False
    
    # Trigger metadata (what triggered this order)
    trigger_source: Optional[str] = None         # "manual", "sma_crossover", "ai_signal", "stop_loss"
    trigger_details: Optional[dict] = None
    
    # Timestamps
    placed_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Notification tracking
    notification_sent: bool = False
    notification_sent_at: Optional[datetime] = None
    
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "orders"
        indexes = [
            # User's orders sorted by time
            [("user_id", 1), ("placed_at", -1)],
            # User's orders by status
            [("user_id", 1), ("status", 1)],
            # Security orders (admin/analytics)
            [("security_id", 1), ("placed_at", -1)],
            # Portfolio's orders
            [("portfolio_id", 1), ("placed_at", -1)],
            # Open orders that need processing
            [("status", 1), ("validity", 1), ("valid_until", 1)],
            # Notification queue
            [("notification_sent", 1), ("status", 1)],
        ]
```

### Index Definitions
- **Compound** on `(user_id, placed_at DESC)` -- user's order history
- **Compound** on `(user_id, status)` -- user's open/pending orders
- **Compound** on `(security_id, placed_at DESC)` -- all orders for a security
- **Compound** on `(portfolio_id, placed_at DESC)` -- portfolio transaction log
- **Compound** on `(status, validity, valid_until)` -- order processing engine finds open orders to check/expire
- **Compound** on `(notification_sent, status)` -- notification queue

### Example Document
```json
{
  "_id": "665e...",
  "user_id": "665a...",
  "portfolio_id": "665d...",
  "security_id": "665c...",
  "symbol": "SBIN",
  "exchange_code": "NSE",
  "security_name": "State Bank of India",
  "order_type": "limit",
  "side": "buy",
  "quantity": 100,
  "filled_quantity": 100,
  "limit_price": 520.00,
  "avg_fill_price": 519.50,
  "validity": "day",
  "status": "filled",
  "fills": [
    {
      "fill_id": "fill-uuid-001",
      "quantity": 60,
      "price": 519.00,
      "fees": 8.50,
      "filled_at": "2024-03-10T10:15:00Z"
    },
    {
      "fill_id": "fill-uuid-002",
      "quantity": 40,
      "price": 520.25,
      "fees": 5.75,
      "filled_at": "2024-03-10T10:15:03Z"
    }
  ],
  "total_amount": 51950.00,
  "total_fees": 14.25,
  "total_taxes": 51.95,
  "currency": "INR",
  "is_simulated": false,
  "trigger_source": "manual",
  "placed_at": "2024-03-10T10:14:55Z",
  "executed_at": "2024-03-10T10:15:03Z",
  "notification_sent": true,
  "notification_sent_at": "2024-03-10T10:15:05Z",
  "created_at": "2024-03-10T10:14:55Z",
  "updated_at": "2024-03-10T10:15:05Z"
}
```

### Relationships
- `user_id` references `users._id`
- `portfolio_id` references `portfolios._id`
- `security_id` references `securities._id`

### Estimated Size & Growth
- ~1-3 KB per document
- Heavy users: 10-50 orders/day; casual: 1-5/week
- Growth: moderate to high depending on user activity

### Special Considerations
- `fills` is embedded because an order rarely has more than ~10 fills
- This replaces the current `ticker_notifications` collection, merging notification tracking into the order itself
- `trigger_source` + `trigger_details` preserve the existing buy/sell signal context (SMA crossover, profit/loss percent thresholds)

---

## Collection 12: `sentiment_records`

### Beanie Document Model

```python
# File: server/app/models/sentiment.py

from datetime import datetime, date
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


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
    """
    Individual sentiment data point from a specific source.
    """
    security_id: Optional[Indexed(str)] = None   # null for market-wide sentiment
    symbol: Optional[str] = None                  # denormalized
    
    # Source
    source_type: Indexed(SentimentSource)
    source_name: Optional[str] = None            # "Reuters", "MoneyControl", "@elonmusk"
    source_url: Optional[str] = None
    
    # Content
    title: Optional[str] = None
    content_snippet: Optional[str] = None        # first 500 chars
    
    # Sentiment scoring
    sentiment_score: float                        # -1.0 (very bearish) to +1.0 (very bullish)
    sentiment_label: SentimentLabel
    confidence: float                             # 0.0 to 1.0
    
    # Scope
    is_market_wide: bool = False                  # True for general market sentiment
    exchange_code: Optional[str] = None
    sector: Optional[str] = None
    
    # ML metadata
    model_name: Optional[str] = None             # "finbert-v2", "vader"
    model_version: Optional[str] = None
    
    published_at: Indexed(datetime)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "sentiment_records"
        indexes = [
            # Primary query: sentiment for a security over time
            [("security_id", 1), ("published_at", -1)],
            # Source-specific queries
            [("source_type", 1), ("published_at", -1)],
            # Market-wide sentiment
            [("is_market_wide", 1), ("published_at", -1)],
            # Daily aggregation lookup
            [("security_id", 1), ("published_at", -1), ("source_type", 1)],
            # TTL: auto-delete raw records older than 1 year (keep aggregates)
            {
                "keys": [("created_at", 1)],
                # expireAfterSeconds=31536000  (365 days)
            },
        ]
```

### Index Definitions
- **Compound** on `(security_id, published_at DESC)` -- get sentiment history for a stock
- **Compound** on `(source_type, published_at DESC)` -- filter by source
- **Compound** on `(is_market_wide, published_at DESC)` -- market sentiment overview
- **TTL** on `created_at` with `expireAfterSeconds=31536000` (365 days) -- raw sentiment records are ephemeral; aggregations should be computed and cached separately

### Example Document
```json
{
  "_id": "...",
  "security_id": "665c...",
  "symbol": "SBIN",
  "source_type": "news_article",
  "source_name": "MoneyControl",
  "source_url": "https://moneycontrol.com/news/...",
  "title": "SBI reports record quarterly profit, beats estimates",
  "content_snippet": "State Bank of India reported a net profit of...",
  "sentiment_score": 0.82,
  "sentiment_label": "very_bullish",
  "confidence": 0.91,
  "is_market_wide": false,
  "exchange_code": "NSE",
  "sector": "financial_services",
  "model_name": "finbert-v2",
  "model_version": "2.1.0",
  "published_at": "2024-05-31T14:30:00Z",
  "analyzed_at": "2024-05-31T14:35:00Z",
  "created_at": "2024-05-31T14:35:00Z"
}
```

### Relationships
- `security_id` references `securities._id`

### Estimated Size & Growth
- ~0.5-1.5 KB per document
- Could be 100-1000 records/day depending on news volume and number of monitored securities
- TTL keeps it bounded at ~365 days of data

### Special Considerations
- Daily/weekly sentiment aggregations should be computed via an aggregation pipeline (`$group` by `security_id` + date bucket, `$avg` on `sentiment_score`) and cached in the application layer or a materialized view
- Raw sentiment is TTL-deleted; if long-term sentiment history is needed, a nightly job should compute and store daily aggregates in a separate small collection or as embedded summaries on the security document

---

## Collection 13: `ml_models`

### Beanie Document Model

```python
# File: server/app/models/ml.py

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class ModelType(str, Enum):
    LSTM_PRICE = "lstm_price"
    LINEAR_REGRESSION = "linear_regression"
    SVM_CLASSIFIER = "svm_classifier"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    TRANSFORMER = "transformer"
    ENSEMBLE = "ensemble"


class ModelStatus(str, Enum):
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class MLModel(Document):
    """
    Metadata about a trained ML model.
    The actual model weights are stored in object storage (S3/GCS);
    this document tracks lineage, metrics, and deployment status.
    """
    name: Indexed(str)                            # "lstm-sbin-v3", "lr-aapl-v1"
    model_type: ModelType
    version: str                                   # "3.0.1"
    status: Indexed(ModelStatus)
    
    # What this model predicts
    target_security_id: Optional[str] = None      # null for multi-security models
    target_description: str                        # "SBIN next-day close price"
    prediction_horizon: str                        # "1d", "5d", "30d"
    
    # Training details
    training_data_from: Optional[datetime] = None
    training_data_to: Optional[datetime] = None
    training_samples: Optional[int] = None
    training_duration_seconds: Optional[float] = None
    
    # Hyperparameters (mirrors existing LSTM config in api_stocks.py)
    hyperparameters: dict = Field(default_factory=dict)
    # Example: {"epochs": 1, "batch_size": 1, "lstm_units": [50, 50],
    #           "dense_units": [25, 1], "optimizer": "adam",
    #           "loss": "mean_squared_error", "lookback_window": 60}
    
    # Performance metrics
    metrics: dict = Field(default_factory=dict)
    # Example: {"rmse": 4.23, "mae": 3.11, "r2": 0.87, "accuracy": 91.2}
    
    # Feature columns
    feature_columns: list[str] = Field(default_factory=list)
    # Example: ["Adj. Close", "HL_PCT", "PCT_change", "Adj. Volume"]
    
    # Storage
    model_artifact_path: Optional[str] = None     # "s3://gloria-models/lstm-sbin-v3.h5"
    scaler_artifact_path: Optional[str] = None    # "s3://gloria-models/scaler-sbin-v3.pkl"
    
    trained_by: Optional[str] = None              # user_id or "system"
    deployed_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "ml_models"
        indexes = [
            [("target_security_id", 1), ("model_type", 1), ("status", 1)],
            [("status", 1)],
        ]
```

### Example Document
```json
{
  "_id": "665f...",
  "name": "lstm-sbin-v3",
  "model_type": "lstm_price",
  "version": "3.0.1",
  "status": "deployed",
  "target_security_id": "665c...",
  "target_description": "SBIN next-day close price prediction",
  "prediction_horizon": "1d",
  "training_data_from": "2015-01-01T00:00:00Z",
  "training_data_to": "2024-05-01T00:00:00Z",
  "training_samples": 2350,
  "training_duration_seconds": 180.5,
  "hyperparameters": {
    "epochs": 10,
    "batch_size": 32,
    "lstm_units": [50, 50],
    "dense_units": [25, 1],
    "optimizer": "adam",
    "loss": "mean_squared_error",
    "lookback_window": 60,
    "train_test_split": 0.8
  },
  "metrics": {
    "rmse": 4.23,
    "mae": 3.11,
    "r2": 0.87
  },
  "feature_columns": ["Adj. Close", "HL_PCT", "PCT_change", "Adj. Volume"],
  "model_artifact_path": "s3://gloria-models/lstm-sbin-v3.h5",
  "scaler_artifact_path": "s3://gloria-models/scaler-sbin-v3.pkl",
  "trained_by": "system",
  "deployed_at": "2024-05-15T00:00:00Z",
  "created_at": "2024-05-15T00:00:00Z",
  "updated_at": "2024-05-15T00:00:00Z"
}
```

### Relationships
- `target_security_id` references `securities._id`
- Referenced by `ml_predictions.model_id`

### Estimated Size & Growth
- ~1-3 KB per document
- Tens to low hundreds of models total
- Minimal growth

---

## Collection 14: `ml_predictions`

### Beanie Document Model

```python
# File: server/app/models/ml.py (continued)


class PredictionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EVALUATED = "evaluated"       # actual outcome compared


class MLPrediction(Document):
    """
    Cached prediction output from an ML model.
    """
    model_id: Indexed(str)
    security_id: Indexed(str)
    symbol: Optional[str] = None
    
    # Prediction
    prediction_date: Indexed(datetime)           # when the prediction was generated
    target_date: datetime                         # the date the prediction is FOR
    
    predicted_value: float                        # e.g. predicted close price
    prediction_low: Optional[float] = None       # confidence interval lower bound
    prediction_high: Optional[float] = None      # confidence interval upper bound
    confidence: Optional[float] = None           # 0-1
    
    # Signal
    signal: Optional[str] = None                 # "buy", "sell", "hold"
    signal_strength: Optional[float] = None      # 0-1
    
    # Risk analysis (from existing security_analysis.py)
    risk_assessment: Optional[dict] = None
    # Example: {
    #   "simple_avg_daily": "0.05%",
    #   "simple_avg_yearly": "12.5%",
    #   "log_avg_daily": "0.04%",
    #   "log_avg_yearly": "10.2%",
    #   "risk_level": "medium",
    #   "volatility_30d": 0.023,
    #   "sharpe_ratio": 1.45
    # }
    
    # Evaluation (filled after target_date passes)
    actual_value: Optional[float] = None
    prediction_error: Optional[float] = None
    status: PredictionStatus = PredictionStatus.ACTIVE
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "ml_predictions"
        indexes = [
            # Primary: latest prediction for a security
            [("security_id", 1), ("prediction_date", -1)],
            # Model performance tracking
            [("model_id", 1), ("prediction_date", -1)],
            # Active predictions
            [("status", 1), ("target_date", 1)],
            # TTL: expire evaluated predictions after 180 days
            {
                "keys": [("created_at", 1)],
                # expireAfterSeconds=15552000  (180 days)
            },
        ]
```

### Example Document
```json
{
  "_id": "...",
  "model_id": "665f...",
  "security_id": "665c...",
  "symbol": "SBIN",
  "prediction_date": "2024-05-31T16:00:00Z",
  "target_date": "2024-06-03T00:00:00Z",
  "predicted_value": 662.00,
  "prediction_low": 648.00,
  "prediction_high": 676.00,
  "confidence": 0.78,
  "signal": "buy",
  "signal_strength": 0.65,
  "risk_assessment": {
    "simple_avg_daily": "0.05%",
    "simple_avg_yearly": "12.5%",
    "log_avg_daily": "0.04%",
    "log_avg_yearly": "10.2%",
    "risk_level": "medium",
    "volatility_30d": 0.023,
    "sharpe_ratio": 1.45
  },
  "actual_value": null,
  "prediction_error": null,
  "status": "active",
  "created_at": "2024-05-31T16:00:00Z"
}
```

### Relationships
- `model_id` references `ml_models._id`
- `security_id` references `securities._id`

### Estimated Size & Growth
- ~0.5-1.5 KB per document
- 1 prediction per security per model per day
- ~10,000 securities * 1-3 models = ~10,000-30,000 predictions/day
- TTL at 180 days keeps total manageable (~1.8-5.4 million)

### Special Considerations
- **TTL of 180 days** ensures the prediction cache doesn't grow unboundedly
- `risk_assessment` preserves the exact structure currently computed in `security_analysis.py`

---

## Collection 15: `system_config`

### Beanie Document Model

```python
# File: server/app/models/config.py

from datetime import datetime
from typing import Any, Optional

from beanie import Document, Indexed
from pydantic import Field


class SystemConfig(Document):
    """
    Key-value style configuration for platform-wide settings.
    Small collection, infrequently updated.
    """
    key: Indexed(str, unique=True)
    value: Any
    description: Optional[str] = None
    category: Optional[str] = None               # "trading", "data_pipeline", "notifications"
    is_secret: bool = False                       # if True, mask in API responses
    
    updated_by: Optional[str] = None             # user_id of admin who changed it
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "system_config"
```

### Example Documents
```json
[
  {
    "key": "data_pipeline.quandl_api_key",
    "value": "encrypted:...",
    "description": "Quandl API key for market data",
    "category": "data_pipeline",
    "is_secret": true
  },
  {
    "key": "trading.default_profit_pct",
    "value": 2.0,
    "description": "Default profit percentage threshold for auto-sell signals",
    "category": "trading"
  },
  {
    "key": "trading.default_loss_pct",
    "value": 2.0,
    "description": "Default loss percentage threshold for stop-loss signals",
    "category": "trading"
  },
  {
    "key": "trading.default_simulation_ticks",
    "value": 400,
    "description": "Number of ticks to generate in day-trade simulation",
    "category": "trading"
  }
]
```

---

## Beanie Initialization

The following shows how all models are registered with Beanie at FastAPI startup:

```python
# File: server/app/database.py

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

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

async def init_db(mongo_uri: str, db_name: str = "gloria_trade"):
    client = AsyncIOMotorClient(mongo_uri)
    await init_beanie(
        database=client[db_name],
        document_models=ALL_DOCUMENT_MODELS,
    )
```

---

## Data Migration Plan from Existing Collections

| Existing Collection | Target Collection | Migration Notes |
|---|---|---|
| `securities_list` | `securities` | Map `description` to `name`, `code` to `data_source_id`, `type` to `primary_exchange_code`; create `listings[]` entry |
| `equity_risk_matrix` | `securities` | Merge `risk` into `computed_risk` field on the matching security document |
| `{TYPE}_{CODE}_historical_data` | `price_history_daily` | Flatten all per-security collections into one; map fields (`Close` -> `close`, `Open` -> `open`, etc.); add `security_id` |
| `ticker_notifications` | `orders` | Map `buyValue`/`sellValue` to order fields; `isNotified` to `notification_sent` |
| `profit_matrix` | `portfolios` + `orders` | Map `investedAmount`/`profitEarned` to portfolio metrics and order P&L |
| `user_trade_risk_assignment` | `users.risk_profile` | Map `high_risk`/`medium_risk`/`low_risk` to embedded `RiskProfile` |

---

## Entity-Relationship Summary

```
users (1) ──────┬──< user_sessions (N)
                ├──< portfolios (N) ─────── holdings[] ──> securities
                │       └── recent_transactions[] ──> orders
                ├──< watchlists (N) ─────── items[] ──> securities
                └──< orders (N) ──────────> securities

countries (1) ──< exchanges (N)

securities (1) ──┬──< price_history_daily (N)  [highest volume]
                 ├──< price_ticks_intraday (N) [TTL-managed]
                 ├──< corporate_actions (N)
                 ├──< sentiment_records (N)    [TTL-managed]
                 ├──< ml_predictions (N)       [TTL-managed]
                 └──< ml_models (N)

system_config (standalone key-value store)
```

---

## Indexing Strategy Summary

| Collection | Index Count | Key Patterns |
|---|---|---|
| `users` | 5 | unique email/phone, compound status+role, text search, KYC status |
| `user_sessions` | 3 | TTL on expires_at, compound user+status, unique token |
| `countries` | 1 | unique code |
| `exchanges` | 2 | unique code, country_code |
| `securities` | 6 | compound symbol+exchange, sector+type, listings subdoc, text search, isin unique sparse |
| `corporate_actions` | 2 | compound security+date, type+date |
| `price_history_daily` | 4 | **compound unique** security+date (critical), date, exchange+date |
| `price_ticks_intraday` | 2 | compound security+timestamp, TTL on timestamp |
| `portfolios` | 2 | compound user+active, holdings subdoc |
| `watchlists` | 2 | user_id, items subdoc |
| `orders` | 6 | user+time, user+status, security+time, portfolio+time, status+validity, notification queue |
| `sentiment_records` | 5 | security+time, source+time, market_wide+time, TTL |
| `ml_models` | 2 | compound security+type+status, status |
| `ml_predictions` | 4 | security+date, model+date, status+target, TTL |
| `system_config` | 1 | unique key |

**Total indexes: ~42** across 15 collections.

---

## Volume Estimates

| Collection | Initial Documents | After 1 Year | After 5 Years | Avg Doc Size |
|---|---|---|---|---|
| `users` | 100 | 5,000 | 25,000 | 3 KB |
| `user_sessions` | 200 | TTL-bounded ~10K | TTL-bounded ~50K | 0.7 KB |
| `countries` | 2-5 | 5-10 | 10-15 | 0.3 KB |
| `exchanges` | 5 | 5-8 | 8-12 | 3 KB |
| `securities` | 10,000 | 15,000 | 30,000 | 4 KB |
| `corporate_actions` | 0 | 25,000 | 150,000 | 0.7 KB |
| `price_history_daily` | 5M (backfill) | 7.5M | 17.5M | 0.7 KB |
| `price_ticks_intraday` | 0 | TTL-bounded ~50M | TTL-bounded ~50M | 0.2 KB |
| `portfolios` | 100 | 5,000 | 25,000 | 10 KB |
| `watchlists` | 50 | 2,500 | 12,500 | 2 KB |
| `orders` | 0 | 500,000 | 5M | 2 KB |
| `sentiment_records` | 0 | TTL-bounded ~200K | TTL-bounded ~200K | 1 KB |
| `ml_models` | 10 | 100 | 500 |
