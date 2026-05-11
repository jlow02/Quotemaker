"""
Purpose: GlobalSetting ORM model. Key-value store for app-wide settings (logo URL, signature URL).
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GlobalSetting(Base):
    """
    Purpose: Stores application-wide settings as key-value pairs.
             Used for Supabase Storage URLs for logo and signature assets.
             Fixed NEXTAN warranty exclusion bullets are NOT here — they are hardcoded
             in app config (app/constants.py) to enforce the "cannot be deleted" rule.
    """
    __tablename__ = "global_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
