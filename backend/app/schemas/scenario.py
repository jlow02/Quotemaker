"""
Purpose: Scenario request/response schemas.
Owner: [Claude]
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.pricing import ScenarioTotals


class ScenarioCreate(BaseModel):
    """
    Purpose: Body for POST /costing-sheets/{sheet_id}/scenarios.
    Inputs: name, discount_type, discount_value, show_gst, notes_exclusions, display_order
    Outputs: N/A
    Owner: [Claude]
    """
    name: str
    discount_type: Optional[str] = None   # 'percentage' | 'flat'
    discount_value: Optional[Decimal] = None
    show_gst: bool = False
    notes_exclusions: Optional[list[str]] = None
    display_order: int = 0


class ScenarioUpdate(BaseModel):
    """
    Purpose: Body for PUT /scenarios/{scenario_id}.
    Inputs: all fields optional
    Outputs: N/A
    Owner: [Claude]
    """
    name: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    show_gst: Optional[bool] = None
    notes_exclusions: Optional[list[str]] = None
    display_order: Optional[int] = None


class ScenarioRead(BaseModel):
    """
    Purpose: Scenario response (without line items — loaded separately for performance).
    Inputs: N/A (response body)
    Outputs: all Scenario fields + optional totals
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    costing_sheet_id: uuid.UUID
    name: str
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    show_gst: bool
    notes_exclusions: Optional[list[str]] = None
    display_order: int
    created_at: datetime
    updated_at: datetime

    # Injected by router layer when line items are loaded
    totals: Optional[ScenarioTotals] = None
