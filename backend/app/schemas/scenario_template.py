"""
Purpose: ScenarioTemplate and TemplateLineItem schemas. Templates are global (no user_id).
Owner: [Claude]
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TemplateLineItemCreate(BaseModel):
    """
    Purpose: Line item definition within a template.
    Inputs: section, description, qty, unit, cost_rate, cost_currency,
            markup_pct, contingency_pct, is_bundle_parent, display_order, sub_specs
    Outputs: N/A
    Owner: [Claude]
    """
    section: str
    description: str
    sub_specs: Optional[list[str]] = None
    qty: Decimal = Decimal("1")
    unit: str = "unit"
    cost_rate: Decimal = Decimal("0")
    cost_currency: str = "SGD"
    markup_pct: Decimal = Decimal("0")
    contingency_pct: Decimal = Decimal("0")
    is_bundle_parent: bool = False
    parent_template_line_item_id: Optional[uuid.UUID] = None
    display_order: int = 0


class TemplateLineItemRead(BaseModel):
    """
    Purpose: TemplateLineItem in template get response.
    Inputs: N/A (response body)
    Outputs: all TemplateLineItem fields + sub_components (recursive for bundles)
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scenario_template_id: uuid.UUID
    parent_template_line_item_id: Optional[uuid.UUID] = None
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
    is_bundle_parent: bool
    created_at: datetime
    updated_at: datetime

    sub_components: list["TemplateLineItemRead"] = []


TemplateLineItemRead.model_rebuild()


class TemplateCreate(BaseModel):
    """
    Purpose: Body for POST /scenario-templates.
    Inputs: name, notes_exclusions, template_line_items
    Outputs: N/A
    Owner: [Claude]
    """
    name: str
    notes_exclusions: Optional[list[str]] = None


class TemplateUpdate(BaseModel):
    """
    Purpose: Body for PUT /scenario-templates/{template_id}.
    Inputs: name, notes_exclusions (both optional)
    Outputs: N/A
    Owner: [Claude]
    """
    name: Optional[str] = None
    notes_exclusions: Optional[list[str]] = None


class TemplateRead(BaseModel):
    """
    Purpose: Full ScenarioTemplate with top-level line items.
    Inputs: N/A (response body)
    Outputs: id, name, notes_exclusions, template_line_items, timestamps
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    notes_exclusions: Optional[list[str]] = None
    template_line_items: list[TemplateLineItemRead] = []
    created_at: datetime
    updated_at: datetime
