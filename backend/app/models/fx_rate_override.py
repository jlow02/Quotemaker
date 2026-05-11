"""
Purpose: FXRateOverride ORM model. Per currency pair per costing sheet override.
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FXRateOverride(Base):
    """
    Purpose: Stores a manual FX rate override for a specific currency pair on a CostingSheet.
             If no override exists for a pair, the live rate from open.er-api.com is used.
    """
    __tablename__ = "fx_rate_overrides"
    __table_args__ = (UniqueConstraint("costing_sheet_id", "base_currency", "target_currency", name="uq_fx_override"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    costing_sheet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("costing_sheets.id", ondelete="CASCADE"), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="SGD")
    override_rate: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    costing_sheet: Mapped["CostingSheet"] = relationship("CostingSheet", back_populates="fx_overrides")
