"""
Purpose: FXRateOverride request/response schemas.
Owner: [Claude]
"""
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class FXRateOverrideCreate(BaseModel):
    """
    Purpose: Body for POST /costing-sheets/{sheet_id}/fx-overrides.
             Upserts: if a record already exists for (sheet_id, base_currency, target_currency),
             it is replaced.
    Inputs: base_currency, override_rate, target_currency (always SGD)
    Outputs: N/A
    Owner: [Claude]
    """
    base_currency: str          # e.g. 'USD', 'CNY'
    target_currency: str = "SGD"
    override_rate: Decimal      # e.g. 1.35 means 1 USD = 1.35 SGD


class FXRateOverrideUpdate(BaseModel):
    """
    Purpose: Body for PUT /fx-overrides/{override_id}.
    Inputs: override_rate
    Outputs: N/A
    Owner: [Claude]
    """
    override_rate: Decimal


class FXRateOverrideRead(BaseModel):
    """
    Purpose: FX override record in list/get responses.
    Inputs: N/A (response body)
    Outputs: id, costing_sheet_id, base_currency, target_currency, override_rate, timestamps
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    costing_sheet_id: uuid.UUID
    base_currency: str
    target_currency: str
    override_rate: Decimal
    created_at: datetime
    updated_at: datetime


class LiveRatesResponse(BaseModel):
    """
    Purpose: Response for GET /fx/live-rates.
             Returns current exchange rates from open.er-api.com (1hr cached).
    Inputs: N/A (response body)
    Outputs: base, rates dict
    Owner: [Claude]
    """
    base: str                   # Always 'SGD'
    rates: dict[str, Decimal]   # e.g. {'USD': 0.74, 'CNY': 5.35}
    cached: bool                # True if served from in-memory cache
