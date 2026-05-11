"""
Purpose: Tracks the last-assigned NNNN sequence per user per year for ref number generation.
         Incremented atomically via SELECT ... FOR UPDATE within the same transaction as CostingSheet INSERT.
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RefNumberSequence(Base):
    """
    Purpose: Atomic per-user, per-year counter for generating NNNN in ref numbers.
             Replaces application-side MAX()+1 which is race-prone.
    """
    __tablename__ = "ref_number_sequences"
    __table_args__ = (UniqueConstraint("user_id", "year", name="uq_ref_seq_user_year"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    last_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="ref_number_sequences")
