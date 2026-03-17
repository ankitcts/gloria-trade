from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field

from app.models.user import Permission


class UserGroup(Document):
    name: Indexed(str, unique=True)
    description: Optional[str] = None

    permissions: list[Permission] = Field(default_factory=list)
    member_ids: list[str] = Field(default_factory=list)

    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "user_groups"
        indexes = [
            [("member_ids", 1)],
        ]
