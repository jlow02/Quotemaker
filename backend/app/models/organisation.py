"""
Purpose: Organisation ORM model. Shared client database across all users. Soft-delete only.
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organisation(Base):
    """
    Purpose: Represents a client organisation. Shared across users; soft-deleted only
             to preserve CostingSheet snapshot history.
    """
    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="organisation")
    costing_sheets: Mapped[list["CostingSheet"]] = relationship("CostingSheet", back_populates="organisation")
