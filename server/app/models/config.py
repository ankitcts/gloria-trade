from datetime import datetime
from typing import Any, Optional

from beanie import Document, Indexed
from pydantic import Field


class SystemConfig(Document):
    key: Indexed(str, unique=True)
    value: Any
    description: Optional[str] = None
    category: Optional[str] = None
    is_secret: bool = False

    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "system_config"
