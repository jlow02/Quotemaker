"""
Purpose: QuoteExport request/response schemas.
Owner: [Claude]
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ExportCreate(BaseModel):
    """
    Purpose: Body for POST /scenarios/{scenario_id}/exports.
    Inputs: file_type ('docx' | 'pdf')
    Outputs: N/A
    Owner: [Claude]
    """
    file_type: str  # 'docx' | 'pdf'


class ExportRead(BaseModel):
    """
    Purpose: QuoteExport record in list responses.
             Does not include snapshot_data to keep payload small.
    Inputs: N/A (response body)
    Outputs: id, costing_sheet_id, scenario_id, user_id, revision_number, file_type, file_path, exported_at
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    costing_sheet_id: uuid.UUID
    scenario_id: uuid.UUID
    user_id: uuid.UUID
    revision_number: int
    file_type: str
    file_path: str
    exported_at: datetime


class ExportDownloadResponse(BaseModel):
    """
    Purpose: Response for GET /exports/{export_id}/download.
             Returns a signed Supabase Storage URL valid for a short TTL.
    Inputs: N/A (response body)
    Outputs: signed_url, expires_in_seconds, export metadata
    Owner: [Claude]
    """
    export_id: uuid.UUID
    signed_url: str
    expires_in_seconds: int
    file_type: str
    revision_number: int
