"""
Purpose: CostingSheet ORM model. The core working document. Private per user.
Owner: [Claude]
"""
import uuid
from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import String, Integer, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CostingSheet(Base):
    """
    Purpose: Represents a user's internal costing document. Contains header, terms,
             and owns Scenarios. Private per user; never shared cross-user.
    Notes:
    - organisation_id/contact_id use ON DELETE SET NULL — if org/contact is soft-deleted,
      snapshot fields (client_name, contact_name, contact_email) preserve display data.
    - show_gst is per-Scenario (not here) — it is an export-time decision.
    """
    __tablename__ = "costing_sheets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ref_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    quote_title: Mapped[str] = mapped_column(String, nullable=False, default="")

    # Client linkage — FK nullable with SET NULL; snapshot fields always populated
    organisation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="SET NULL"), nullable=True)
    client_name: Mapped[str] = mapped_column(String, nullable=False, default="")
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Terms block
    payment_term: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    quotation_validity_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    lead_time: Mapped[str] = mapped_column(String, nullable=False, default="30 working days")
    local_tax: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    warranty: Mapped[str] = mapped_column(String, nullable=False, default="12 months standard")
    general_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="costing_sheets")
    organisation: Mapped[Optional["Organisation"]] = relationship("Organisation", back_populates="costing_sheets")
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="costing_sheets")
    scenarios: Mapped[list["Scenario"]] = relationship("Scenario", back_populates="costing_sheet", cascade="all, delete-orphan", order_by="Scenario.display_order")
    fx_overrides: Mapped[list["FXRateOverride"]] = relationship("FXRateOverride", back_populates="costing_sheet", cascade="all, delete-orphan")
    tnc_additions: Mapped[list["CostingSheetTncAddition"]] = relationship("CostingSheetTncAddition", back_populates="costing_sheet", cascade="all, delete-orphan", order_by="CostingSheetTncAddition.display_order")
    quote_exports: Mapped[list["QuoteExport"]] = relationship("QuoteExport", back_populates="costing_sheet")
