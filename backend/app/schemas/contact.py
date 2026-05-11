"""
Purpose: Contact request/response schemas. Scoped to an Organisation.
Owner: [Claude]
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ContactCreate(BaseModel):
    """
    Purpose: Body for POST /organisations/{org_id}/contacts.
    Inputs: name, email, phone
    Outputs: N/A
    Owner: [Claude]
    """
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class ContactUpdate(BaseModel):
    """
    Purpose: Body for PUT /contacts/{contact_id}.
    Inputs: name, email, phone (all optional)
    Outputs: N/A
    Owner: [Claude]
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ContactRead(BaseModel):
    """
    Purpose: Contact details in list and get responses.
    Inputs: N/A (response body)
    Outputs: id, organisation_id, name, email, phone, created_by_user_id, timestamps
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organisation_id: uuid.UUID
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ContactAutocomplete(BaseModel):
    """
    Purpose: Lightweight item for contact autocomplete dropdown.
    Inputs: N/A (response body)
    Outputs: id, name, email
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: Optional[str] = None
