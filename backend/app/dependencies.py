"""
Purpose: FastAPI dependencies — get_current_user JWT auth dependency.
         Injected via Depends() in all protected routes.
Owner: [Claude]
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import decode_token

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Purpose: FastAPI dependency that validates the Bearer JWT and returns the User ORM object.
             Raises 401 if the token is missing, invalid, expired, or the user is not found.
    Inputs: credentials (HTTPAuthorizationCredentials), db (Session)
    Outputs: User ORM instance
    Owner: [Claude]
    """
    token = credentials.credentials
    user_id_str = decode_token(token, expected_type="access")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
