"""
Purpose: One-shot script to create the initial admin user in Supabase.
         Run once: python create_user.py
         Username = email address (matches the Login page's email field).
Owner: [Claude]
"""
import sys
import os

# Ensure app config is importable
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.user import User
from app.services.auth_service import hash_password
from app.database import Base

# ── Config ──────────────────────────────────────────────────────────────────
USERNAME = "jlow02@gmail.com"   # Must match what you type in the Login page
PASSWORD = "nextan2026"          # Change this to whatever you prefer
NUMERIC_ID = 1
# ────────────────────────────────────────────────────────────────────────────

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)

with SessionLocal() as db:
    existing = db.query(User).filter(User.username == USERNAME).first()
    if existing:
        print(f"User '{USERNAME}' already exists — skipping.")
    else:
        user = User(
            numeric_user_id=NUMERIC_ID,
            username=USERNAME,
            hashed_password=hash_password(PASSWORD),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created user: {USERNAME} (id={user.id})")
        print(f"Login with: email={USERNAME}  password={PASSWORD}")
