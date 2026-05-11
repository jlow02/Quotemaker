"""
Purpose: User endpoints — GET /users/me returns the authenticated user's details.
Owner: [Claude]
"""
from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Purpose: Return the authenticated user's profile.
    Inputs: JWT Bearer token (via dependency)
    Outputs: UserRead
    Owner: [Claude]
    """
    return current_user
