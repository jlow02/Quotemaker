"""
Purpose: T&C Addition schemas — shared shape for both sheet-level and global additions.
Owner: [Claude]
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TncCreate(BaseModel):
    """
    Purpose: Body for POST /.../tnc-additions. Creates a new T&C bullet.
    Inputs: bullet_point, display_order
    Outputs: N/A
    Owner: [Claude]
    """
    bullet_point: str
    display_order: int = 0


class TncUpdate(BaseModel):
    """
    Purpose: Body for PUT .../tnc-additions/{id}. Updates a T&C bullet.
    Inputs: bullet_point, display_order (both optional)
    Outputs: N/A
    Owner: [Claude]
    """
    bullet_point: Optional[str] = None
    display_order: Optional[int] = None


class TncRead(BaseModel):
    """
    Purpose: T&C Addition record in list/get responses. Used for both sheet-level
             (CostingSheetTncAddition) and global (GlobalTncAddition).
    Inputs: N/A (response body)
    Outputs: id, bullet_point, display_order, costing_sheet_id (None for global), timestamps
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bullet_point: str
    display_order: int
    costing_sheet_id: Optional[uuid.UUID] = None  # None for GlobalTncAddition
    created_at: datetime
    updated_at: datetime
