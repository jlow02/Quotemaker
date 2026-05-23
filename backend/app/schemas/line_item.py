"""
Purpose: LineItem request/response schemas including computed pricing fields.
Owner: [Claude]
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.pricing import ComputedLineItemPricing


class LineItemCreate(BaseModel):
    """
    Purpose: Body for POST /scenarios/{scenario_id}/line-items.
    Inputs: section, description, qty, unit, cost_rate, cost_currency,
            markup_pct, contingency_pct, display_order, sub_specs,
            is_bundle_parent, parent_line_item_id (for sub-components)
    Outputs: N/A
    Owner: [Claude]
    """
    section: str  # 'Hardware' | 'Software' | 'Professional Fees' | 'Maintenance'
    description: str
    sub_specs: Optional[list[str]] = None
    qty: Decimal = Decimal("1")
    unit: str = "unit"
    cost_rate: Decimal = Decimal("0")
    cost_currency: str = "SGD"
    markup_pct: Decimal = Decimal("0")
    contingency_pct: Decimal = Decimal("0")
    is_visible: bool = True
    is_bundle_parent: bool = False
    parent_line_item_id: Optional[uuid.UUID] = None
    display_order: int = 0


class LineItemUpdate(BaseModel):
    """
    Purpose: Body for PUT /line-items/{line_item_id}.
             Sub-component updates automatically clear parent bundle override.
    Inputs: all LineItem fields (all optional for partial update)
    Outputs: N/A
    Owner: [Claude]
    """
    description: Optional[str] = None
    sub_specs: Optional[list[str]] = None
    qty: Optional[Decimal] = None
    unit: Optional[str] = None
    cost_rate: Optional[Decimal] = None
    cost_currency: Optional[str] = None
    markup_pct: Optional[Decimal] = None
    contingency_pct: Optional[Decimal] = None
    is_visible: Optional[bool] = None
    section: Optional[str] = None
    display_order: Optional[int] = None


class BundleOverridePatch(BaseModel):
    """
    Purpose: Body for PATCH /line-items/{line_item_id}/bundle-override.
             Set bundle_override_price to activate override; send null to clear it.
    Inputs: bundle_override_price (Decimal or None)
    Outputs: N/A
    Owner: [Claude]
    """
    bundle_override_price: Optional[Decimal] = None


class ReorderItem(BaseModel):
    """
    Purpose: Single item in a reorder request — id + new display_order.
    Owner: [Claude]
    """
    id: uuid.UUID
    display_order: int


class ReorderRequest(BaseModel):
    """
    Purpose: Body for PUT /scenarios/{scenario_id}/line-items/reorder.
             Bulk update of display_order for all top-level items in a scenario.
    Inputs: items (list of {id, display_order})
    Outputs: N/A
    Owner: [Claude]
    """
    items: list[ReorderItem]


class BulkDeleteRequest(BaseModel):
    """
    Purpose: Body for DELETE /scenarios/{scenario_id}/line-items/bulk.
             Delete multiple line items by ID in a single request.
             Silently skips IDs that don't belong to the scenario.
    Inputs: ids (list of str UUIDs)
    Outputs: N/A
    Owner: [Claude]
    """
    ids: list[uuid.UUID]


class LineItemRead(BaseModel):
    """
    Purpose: Full line item response including computed pricing fields.
             Computed fields (cost_sgd etc.) are injected at the router layer, not from DB.
    Inputs: N/A (response body)
    Outputs: all stored fields + ComputedLineItemPricing + sub_components (recursive for bundles)
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scenario_id: uuid.UUID
    parent_line_item_id: Optional[uuid.UUID] = None
    section: str
    display_order: int
    description: str
    sub_specs: Optional[list[str]] = None
    qty: Decimal
    unit: str
    cost_rate: Decimal
    cost_currency: str
    markup_pct: Decimal
    contingency_pct: Decimal
    is_visible: bool
    is_bundle_parent: bool
    bundle_override_price: Optional[Decimal] = None
    is_b