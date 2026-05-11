"""
Purpose: QuoteExport ORM model. Records each locked export with snapshot data.
Owner: [Claude]
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QuoteExport(Base):
    """
    Purpose: Immutable record of a quote export. Stores snapshot_data (full scenario state
             at export time) so the export can be regenerated if the Storage file is lost.
    Notes:
    - revision_number: 0 = original (NT_YYMM-ID-NNNN.docx), 1 = R1, 2 = R2, etc.
    - ON DELETE RESTRICT: sheet/scenario cannot be deleted while exports exist.
    - DELETE /api/v1/exports/{id} removes both the DB record and the Supabase Storage file.
    - POST /scenarios/{id}/exports must wrap snapshot write + Storage upload + DB insert
      in a single transaction. If Storage upload fails, transaction is rolled back.
    """
    __tablename__ = "quote_exports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    costing_sheet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("costing_sheets.id", ondelete="RESTRICT"), nullable=False)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_type: Mapped[str] = mapped_column(SAEnum("docx", "pdf", name="export_file_type_enum"), nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    exported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    costing_sheet: Mapped["CostingSheet"] = relationship("CostingSheet", back_populates="quote_exports")
    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="quote_exports")
    user: Mapped["User"] = relationship("User", back_populates="quote_exports")
