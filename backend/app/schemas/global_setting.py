"""
Purpose: GlobalSetting schemas. Key-value store for logo URL, signature URL.
Owner: [Claude]
"""
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class SettingRead(BaseModel):
    """
    Purpose: GlobalSetting record in list/get responses.
    Inputs: N/A (response body)
    Outputs: id, key, value, timestamps
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    value: Any  # JSONB — can be any JSON-serialisable type
    created_at: datetime
    updated_at: datetime


class SettingUpdate(BaseModel):
    """
    Purpose: Body for PUT /settings/{key}. Updates a global setting value.
    Inputs: value (any JSON-serialisable value)
    Outputs: N/A
    Owner: [Claude]
    """
    value: Any
