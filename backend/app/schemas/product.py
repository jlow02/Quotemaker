"""
Purpose: Product request/response schemas. Products are soft-deleted; never hard-deleted.
Owner: [Claude]
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    """
    Purpose: Body for POST /products.
    Inputs: category, name, description, sub_specs, default_cost_price,
            default_currency, default_unit, default_markup_pct, default_contingency_pct
    Outputs: N/A
    Owner: [Claude]
    """
    category: str  # 'Hardware' | 'Software' | 'Professional Fees' | 'Maintenance'
    name: str
    description: Optional[str] = None
    sub_specs: Optional[list[str]] = None
    default_cost_price: Decimal = Decimal("0")
    default_currency: str = "SGD"
    default_unit: str = "unit"
    default_markup_pct: Decimal = Decimal("0")
    default_contingency_pct: Decimal = Decimal("0")


class ProductUpdate(BaseModel):
    """
    Purpose: Body for PUT /products/{product_id}.
    Inputs: all fields optional for partial update
    Outputs: N/A
    Owner: [Claude]
    """
    category: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    sub_specs: Optional[list[str]] = None
    default_cost_price: Optional[Decimal] = None
    default_currency: Optional[str] = None
    default_unit: Optional[str] = None
    default_markup_pct: Optional[Decimal] = None
    default_contingency_pct: Optional[Decimal] = None


class ProductRead(BaseModel):
    """
    Purpose: Product record in list/get responses.
    Inputs: N/A (response body)
    Outputs: all Product fields (excluding hashed_password, deleted_at)
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    name: str
    description: Optional[str] = None
    sub_specs: Optional[list[str]] = None
    default_cost_price: Decimal
    default_currency: str
    default_unit: str
    default_markup_pct: Decimal
    default_contingency_pct: Decimal
    created_at: datetime
    updated_at: datetime
