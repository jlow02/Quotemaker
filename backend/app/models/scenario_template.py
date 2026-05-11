"""
Purpose: ScenarioTemplate and TemplateLineItem ORM models. Global templates seeded at deploy.
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Boolean, Numeric, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScenarioTemplate(Base):
    """
    Purpose: A reusable template for pre-populating a new Scenario.
             Global (not user-specific) for v1. Items are COPIED on apply — not linked.
             Three pre-built starters seeded at deploy: Tracking System, CCTV, IoT Sensor.
    """
    __tablename__ = "scenario_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    notes_exclusions: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    template_line_items: Mapped[list["TemplateLineItem"]] = relationship(
        "TemplateLineItem",
        back_populates="scenario_template",
        cascade="all, delete-orphan",
        primaryjoin="and_(TemplateLineItem.scenario_template_id == ScenarioTemplate.id, TemplateLineItem.parent_template_line_item_id == None)",
        order_by="TemplateLineItem.section, TemplateLineItem.display_order",
    )


class TemplateLineItem(Base):
    """
    Purpose: A line item definition within a ScenarioTemplate.
             Mirrors LineItem structure for copy-on-apply to a Scenario.
    """
    __tablename__ = "template_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenario_templates.id", ondelete="CASCADE"), nullable=False)
    parent_template_line_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("template_line_items.id", ondelete="CASCADE"), nullable=True)
    section: Mapped[str] = mapped_column(
        SAEnum("Hardware", "Software", "Professional Fees", "Maintenance", name="template_section_enum"),
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
    is_bundle_parent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    scenario_template: Mapped["ScenarioTemplate"] = relationship("ScenarioTemplate", back_populates="template_line_items", foreign_keys=[scenario_template_id])
    sub_components: Mapped[list["TemplateLineItem"]] = relationship(
        "TemplateLineItem",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys="TemplateLineItem.parent_template_line_item_id",
        order_by="TemplateLineItem.display_order",
    )
    parent: Mapped[Optional["TemplateLineItem"]] = relationship(
        "TemplateLineItem",
        back_populates="sub_components",
        remote_side="TemplateLineItem.id",
        foreign_keys="TemplateLineItem.parent_template_line_item_id",
    )
