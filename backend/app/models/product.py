"""
Purpose: Product ORM model. Product library used to pre-fill line items.
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Numeric, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Product(Base):
    """
    Purpose: A product in the library. Values are copied into LineItem on add;
             products are NOT linked to line items after insertion.
             Soft-deleted only to preserve historical costing sheet data.
    """
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(
        SAEnum("Hardware", "Software", "Professional Fees", "Maintenance", name="product_category_enum"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sub_specs: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    default_cost_price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="SGD")
    default_unit: Mapped[str] = mapped_column(String, nullable=False, default="unit")
    default_markup_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False, default=0.0)
    default_contingency_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False, default=0.0)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
