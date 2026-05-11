"""
One-shot script to create all database tables from ORM models.
Run once to initialise the schema. Safe to re-run (create_all is idempotent).
Owner: [Claude]
"""
import sys
from pathlib import Path

# Ensure app.* imports resolve from this directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from sqlalchemy import create_engine, text
from app.database import Base
from app.config import settings
import app.models  # noqa: F401 — registers all 15 models with Base.metadata

engine = create_engine(
    settings.database_url,
    connect_args={"options": "-c timezone=utc"},
)

print("Connecting to database...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    print(f"Connected: {result.scalar()}")

print("\nCreating tables...")
Base.metadata.create_all(bind=engine)
print("Done. Tables created:")
for table in Base.metadata.sorted_tables:
    print(f"  ✓ {table.name}")
