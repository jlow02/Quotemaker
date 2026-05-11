"""
Purpose: CostingSheet request/response schemas.
Owner: [Claude]
"""
import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.scenario import ScenarioRead


class CostingSheetCreate(BaseModel):
    """
    Purpose: Body for POST /costing-sheets.
             ref_number is auto-generated; date defaults to today.
    Inputs: quote_title, client_name, organisation_id, contact_id, contact_name,
            contact_email, payment_term, quotation_validity_days, lead_time,
            local_tax, warranty, general_notes
    Outputs: N/A
    Owner: [Claude]
    """
    quote_title: str
    date: Optional[date] = None                    # Defaults to today if not provided
    client_name: str
    organisation_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    payment_term: Optional[str] = None
    quotation_validity_days: int = 90
    lead_time: str = "30 working days"
    local_tax: Optional[str] = None
    warranty: str = "12 months standard"
    general_notes: Optional[str] = None


class CostingSheetUpdate(BaseModel):
    """
    Purpose: Body for PUT /costing-sheets/{sheet_id}.
             All fields optional for partial update.
    Inputs: any subset of CostingSheet header/terms fields
    Outputs: N/A
    Owner: [Claude]
    """
    quote_title: Optional[str] = None
    date: Optional[date] = None
    client_name: Optional[str] = None
    organisation_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    payment_term: Optional[str] = None
    quotation_validity_days: Optional[int] = None
    lead_time: Optional[str] = None
    local_tax: Optional[str] = None
    warranty: Optional[str] = None
    general_notes: Optional[str] = None
    ref_number: Optional[str] = None              # Editable per domain model


class CostingSheetList(BaseModel):
    """
    Purpose: Lightweight item for GET /costing-sheets list response.
             Does not include scenarios or line items.
    Inputs: N/A (response body)
    Outputs: id, ref_number, quote_title, date, client_name, contact_name, timestamps
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ref_number: str
    quote_title: str
    date: date
    client_name: str
    contact_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CostingSheetRead(BaseModel):
    """
    Purpose: Full CostingSheet response including nested scenarios.
             Line items are NOT embedded here — loaded per-scenario via separate endpoint.
    Inputs: N/A (response body)
    Outputs: all header/terms fields + scenarios list
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    ref_number: str
    date: date
    quote_title: str
    organisation_id: Optional[uuid.UUID] = None
    client_name: str
    contact_id: Optional[uuid.UUID] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    payment_term: Optional[str] = None
    quotation_validity_days: int
    lead_time: str
    local_tax: Optional[str] = None
    warranty: str
    general_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    scenarios: list[ScenarioRead] = []
