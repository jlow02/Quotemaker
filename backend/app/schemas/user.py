"""
Purpose: User response schema. No write schemas — users are provisioned directly in DB for v1.
Owner: [Claude]
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    """
    Purpose: Authenticated user details returned by GET /users/me.
    Inputs: N/A (response body)
    Outputs: id, numeric_user_id, username, created_at
    Owner: [Claude]
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    numeric_user_id: int
    username: str
    created_at: datetime
