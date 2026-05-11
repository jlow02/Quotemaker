"""
Purpose: Organisation request/response schemas. Shared client database entity.
Owner: [Claude]
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class OrganisationCreate(BaseModel):
    """
    Purpose: Body for POST /organisations.
    Inputs: name (str), address (Optional[str])
    Outputs: N/A
    Owner: [Claude]
    """
    name: str
    address: Optional[str] = None


class OrganisationUpdate(BaseModel):
    """
    Purpose: Body for PUT /organisations/{org_id}.
    Inputs: name (Optional[str]), address (Optional[str])
    Outputs: N/A
    Owner: [Claude]
    """
    name: Optional[str] = None
    address: Optional[str] = None


class OrganisationRead(BaseModel):
    """
    Purpose: Organisation details in list and get responses.
    Inputs: N/A (response body)
    Outputs: id, name, address, created_by_user_id, created_at, updated_at
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    address: Optional[str] = None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class OrganisationAutocomplete(BaseModel):
    """
    Purpose: Lightweight item for autocomplete dropdown.
    Inputs: N/A (response body)
    Outputs: id, name
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
