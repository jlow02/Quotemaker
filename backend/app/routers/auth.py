"""
Purpose: Auth endpoints — login and token refresh. No JWT dependency on these routes.
Owner: [Claude]
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenPair, TokenRefreshRequest, AccessToken
from app.services.auth_service import (
    verify_password, create_access_token, create_refresh_token, decode_token
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Purpose: Authenticate a user and return JWT access + refresh token pair.
    Inputs: LoginRequest (username, password)
    Outputs: TokenPair
    Owner: [Claude]
    """
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )
    subject = str(user.id)
    return TokenPair(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.post("/refresh", response_model=AccessToken)
def refresh_token(body: TokenRefreshRequest, db: Session = Depends(get_db)):
    """
    Purpose: Exchange a valid refresh token for a new access token.
    Inputs: TokenRefreshRequest (refresh_token)
    Outputs: AccessToken
    Owner: [Claude]
    """
    import uuid
    user_id_str = decode_token(body.refresh_token, expected_type="refresh")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token.")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return AccessToken(access_token=create_access_token(str(user.id)))
