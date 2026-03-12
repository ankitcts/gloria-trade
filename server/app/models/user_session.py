from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
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

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None
    geo_location: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Indexed(datetime)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None

    class Settings:
        name = "user_sessions"
        indexes = [
            [("user_id", 1), ("status", 1)],
        ]
