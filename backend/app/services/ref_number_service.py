"""
Purpose: Atomic ref number generation using PostgreSQL INSERT...ON CONFLICT DO UPDATE.
         Produces YYMM-USERID-NNNN formatted strings, unique per user per month.
Owner: [Claude]
"""
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.constants import REF_NUMBER_SEQUENCE_PADDING, REF_NUMBER_USER_ID_PADDING


def generate_ref_number(user_id: str, numeric_user_id: int, db: Session) -> str:
    """
    Purpose: Atomically reserve the next sequence number for this user in the current year
             and return a formatted ref number string.
             Uses INSERT...ON CONFLICT DO UPDATE RETURNING for true atomicity —
             avoids phantom read vulnerability of SELECT...FOR UPDATE on non-existent rows.
    Inputs: user_id (str UUID), numeric_user_id (int), db (SQLAlchemy Session)
    Outputs: str — e.g. '2605-0001-0003' for May 2026, user #1, sequence #3
    Owner: [Claude]
    """
    now = datetime.now(timezone.utc)
    yymm = now.strftime("%y%m")    # e.g. '2605' for May 2026
    year = now.year

    # Atomic upsert: inserts first sequence for (user_id, year), or increments existing.
    result = db.execute(
        text("""
            INSERT INTO ref_number_sequences (id, user_id, year, last_sequence, updated_at)
            VALUES (gen_random_uuid(), :user_id, :year, 1, now())
            ON CONFLICT (user_id, year)
            DO UPDATE SET
                last_sequence = ref_number_sequences.last_sequence + 1,
                updated_at = now()
            RETURNING last_sequence
        """),
        {"user_id": user_id, "year": year},
    )
    last_sequence = result.scalar_one()

    uid_str = str(numeric_user_id).zfill(REF_NUMBER_USER_ID_PADDING)
    seq_str = str(last_sequence).zfill(REF_NUMBER_SEQUENCE_PADDING)
    return f"{yymm}-{uid_str}-{seq_str}"
