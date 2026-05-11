"""
Purpose: Application-wide constants. Hardcoded values that must not be configurable or deletable.
Owner: [Claude]
"""

# ---------------------------------------------------------------------------
# NEXTAN Warranty Exclusion Bullets
# These items appear on every quote export's T&C section and CANNOT be removed
# by any user action (they are not in the database by design).
# To change these, a code deployment is required — that is intentional.
# ---------------------------------------------------------------------------

NEXTAN_WARRANTY_EXCLUSIONS: list[str] = [
    "Damage caused by misuse, negligence, or accidents",
    "Damage caused by unauthorized modifications or repairs",
    "Consumable parts (batteries, fuses, cables) unless defective at delivery",
    "Software defects caused by user-installed third-party applications",
    "Environmental damage including water ingress, lightning, or power surges",
    "Normal wear and tear",
]

# ---------------------------------------------------------------------------
# FX
# ---------------------------------------------------------------------------

FX_CACHE_TTL_SECONDS: int = 3600  # 1 hour
FX_BASE_CURRENCY: str = "SGD"     # System always prices in SGD
FX_LIVE_RATE_API_URL: str = "https://open.er-api.com/v6/latest/{base}"

# ---------------------------------------------------------------------------
# Ref Number
# ---------------------------------------------------------------------------

REF_NUMBER_SEQUENCE_PADDING: int = 4   # Zero-pad NNNN to 4 digits
REF_NUMBER_USER_ID_PADDING: int = 4    # Zero-pad numeric_user_id to 4 digits

# ---------------------------------------------------------------------------
# Export file path templates (Supabase Storage)
# ---------------------------------------------------------------------------

EXPORT_PATH_ORIGINAL: str = "exports/{user_id}/{ref}.{ext}"
EXPORT_PATH_REVISION: str = "exports/{user_id}/{ref}-R{revision}.{ext}"

# ---------------------------------------------------------------------------
# GST
# ---------------------------------------------------------------------------

GST_RATE: float = 0.09  # 9% Singapore GST

# ---------------------------------------------------------------------------
# Quote defaults
# ---------------------------------------------------------------------------

DEFAULT_QUOTATION_VALIDITY_DAYS: int = 90
DEFAULT_LEAD_TIME: str = "30 working days"
DEFAULT_WARRANTY: str = "12 months standard"
