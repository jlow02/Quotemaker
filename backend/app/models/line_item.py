"""
Purpose: LineItem ORM model. Supports regular items and bundle parents with sub-components.
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Boolean, Numeric, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LineItem(Base):
    """
    Purpose: A single line in a Scenario. Can be a regular item, a bundle parent,
             or a bundle sub-component (parent_line_item_id set).
    Notes:
    - Derived fields NOT stored: cost_sgd, selling_rate_sgd, line_total_sgd — computed at query time.
    - When any sub-component is updated, service layer MUST clear is_bundle_override_active
      and bundle_override_price on the parent within the same transaction.
    - Use selectinload(depth=2) when loading scenarios to avoid N+1 on bundle sub-components.
    """
    __tablename__ = "line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    parent_line_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("line_items.id", ondelete="CASCADE"), nullable=True)

    section: Mapped[str] = mapped_column(
        SAEnum("Hardware", "Software", "Professional Fees", "Maintenance", name="section_enum"),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    sub_specs: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    qty: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=1)
    unit: Mapped[str] = mapped_column(String, nullable=False, default="unit")
    cost_rate: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    cost_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="SGD")
    markup_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False, default=0.0)
    contingency_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False, default=0.0)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_bundle_parent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bundle_override_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    is_bundle_override_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="line_items", foreign_keys=[scenario_id])
    sub_components: Mapped[list["LineItem"]] = relationship(
        "LineItem",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys="LineItem.parent_line_item_id",
        order_by="LineItem.display_order",
    )
    parent: Mapped[Optional["LineItem"]] = relationship(
        "LineItem",
        back_populates="sub_components",
        remote_side="LineItem.id",
        foreign_keys="LineItem.parent_line_item_id",
    )
