"""
Purpose: Application configuration loaded from environment variables.
Owner: [Claude]
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Purpose: Centralised settings sourced from .env file. No hardcoded secrets.
    """
    database_url: str
    supabase_url: str
    supabase_service_key: str
    supabase_storage_bucket_exports: str = "exports"
    supabase_storage_bucket_assets: str = "assets"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    app_env: str = "development"
    cors_origins: str = "*"  # Comma-separated list; set to Vercel domain in Railway production

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
