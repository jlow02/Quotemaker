"""
Purpose: T&C addition models — per-sheet additions and global defaults.
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CostingSheetTncAddition(Base):
    """
    Purpose: User-configurable T&C bullet points specific to one CostingSheet.
             Appended after fixed warranty exclusions (hardcoded in app config) on export.
    """
    __tablename__ = "costing_sheet_tnc_additions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    costing_sheet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("costing_sheets.id", ondelete="CASCADE"), nullable=False)
    bullet_point: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    costing_sheet: Mapped["CostingSheet"] = relationship("CostingSheet", back_populates="tnc_additions")


class GlobalTncAddition(Base):
    """
    Purpose: Global default T&C additions editable via Settings.
             These are copied to new sheets as defaults; they are NOT the fixed NEXTAN
             warranty exclusion bullets (those are hardcoded in app config and not deletable).
    """
    __tablename__ = "global_tnc_additions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bullet_point: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
