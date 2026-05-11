"""
Purpose: User ORM model. Stores credentials for JWT authentication.
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """
    Purpose: Represents an authenticated user. Two users configured directly in DB for v1.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numeric_user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    costing_sheets: Mapped[list["CostingSheet"]] = relationship("CostingSheet", back_populates="user")
    ref_number_sequences: Mapped[list["RefNumberSequence"]] = relationship("RefNumberSequence", back_populates="user")
    quote_exports: Mapped[list["QuoteExport"]] = relationship("QuoteExport", back_populates="user")
