"""
Purpose: Scenario ORM model. One CostingSheet has many independent Scenarios (Option A, B...).
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Boolean, Numeric, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Scenario(Base):
    """
    Purpose: An independent pricing scenario within a CostingSheet.
             Each scenario has its own line items, discount, GST toggle, and notes.
             show_gst is here (not on CostingSheet) because each scenario exports independently.
    """
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    costing_sheet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("costing_sheets.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False, default="Option A")
    discount_type: Mapped[Optional[str]] = mapped_column(SAEnum("percentage", "flat", name="discount_type_enum"), nullable=True)
    discount_value: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    show_gst: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes_exclusions: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    costing_sheet: Mapped["CostingSheet"] = relationship("CostingSheet", back_populates="scenarios")
    line_items: Mapped[list["LineItem"]] = relationship(
        "LineItem",
        back_populates="scenario",
        cascade="all, delete-orphan",
        primaryjoin="and_(LineItem.scenario_id == Scenario.id, LineItem.parent_line_item_id == None)",
        order_by="LineItem.section, LineItem.display_order",
    )
    quote_exports: Mapped[list["QuoteExport"]] = relationship("QuoteExport", back_populates="scenario")
