"""
Purpose: SQLAlchemy engine, session factory, and declarative base.
Owner: [Claude]
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"sslmode": "require"},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db():
    """
    Purpose: FastAPI dependency that yields a DB session and closes it after the request.
    Outputs: SQLAlchemy Session
    Owner: [Claude]
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
