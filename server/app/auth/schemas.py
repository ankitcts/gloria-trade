from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import AccountStatus, UserRole


# ── Request schemas ──────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Response schemas ─────────────────────────────────────────────────────────


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    avatar_url: Optional[str] = None
    timezone: str
    preferred_locale: str
    role: UserRole
    account_status: AccountStatus
    email_verified: bool
    phone_verified: bool
    last_login_at: Optional[datetime] = None
    login_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_user(cls, user) -> "UserResponse":
        return cls(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            display_name=user.display_name,
            phone=user.phone,
            date_of_birth=user.date_of_birth,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            preferred_locale=user.preferred_locale,
            role=user.role,
            account_status=user.account_status,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            last_login_at=user.last_login_at,
            login_count=user.login_count,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
