"""
Purpose: Auth request/response schemas — login, token pair, refresh.
Owner: [Claude]
"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """
    Purpose: Credentials for POST /auth/login.
    Inputs: username (str), password (str)
    Outputs: N/A (request body)
    Owner: [Claude]
    """
    username: str
    password: str


class TokenPair(BaseModel):
    """
    Purpose: Access + refresh token pair returned on successful login.
    Inputs: N/A (response body)
    Outputs: access_token, refresh_token, token_type
    Owner: [Claude]
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    """
    Purpose: Request body for POST /auth/refresh.
    Inputs: refresh_token (str)
    Outputs: N/A (request body)
    Owner: [Claude]
    """
    refresh_token: str


class AccessToken(BaseModel):
    """
    Purpose: New access token returned by POST /auth/refresh.
    Inputs: N/A (response body)
    Outputs: access_token, token_type
    Owner: [Claude]
    """
    access_token: str
    token_type: str = "bearer"
