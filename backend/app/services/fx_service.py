"""
Purpose: FX rate resolution — override-first lookup with live rate fallback.
         Live rates fetched from open.er-api.com and cached in-memory for 1 hour.
         Uses asyncio.Lock for safe concurrent access in async FastAPI context.
Owner: [Claude]
"""
import asyncio
import time
from decimal import Decimal

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.constants import FX_BASE_CURRENCY, FX_CACHE_TTL_SECONDS, FX_LIVE_RATE_API_URL
from app.models.fx_rate_override import FXRateOverride

# ── In-memory cache ────────────────────────────────────────────────────────────
# Key: base_currency (e.g. 'USD')
# Value: {'rate': Decimal, 'fetched_at': float (unix timestamp)}
# Per-process cache — acceptable for single-dyno Railway v1 deployment.
# Migrate to Redis if multi-worker scaling is needed.
_rate_cache: dict[str, dict] = {}
_cache_lock = asyncio.Lock()


async def get_live_rate(base_currency: str) -> Decimal:
    """
    Purpose: Fetch the SGD rate for a given base currency from open.er-api.com.
             Results are cached in-memory for FX_CACHE_TTL_SECONDS (1 hour).
             Returns how many SGD 1 unit of base_currency buys.
    Inputs: base_currency (str) — ISO 4217 code, e.g. 'USD'
    Outputs: Decimal — exchange rate (1 base_currency = X SGD)
    Owner: [Claude]
    """
    if base_currency == FX_BASE_CURRENCY:
        return Decimal("1")

    async with _cache_lock:
        cached = _rate_cache.get(base_currency)
        now = time.time()
        if cached and (now - cached["fetched_at"]) < FX_CACHE_TTL_SECONDS:
            return cached["rate"]

        # Cache miss or expired — fetch live
        url = FX_LIVE_RATE_API_URL.format(base=base_currency)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Exchange rate service unavailable for {base_currency}. "
                    "Set a manual FX override to proceed."
                ),
            ) from exc

        rates = data.get("rates", {})
        sgd_rate = rates.get(FX_BASE_CURRENCY)
        if sgd_rate is None:
            raise HTTPException(
                status_code=503,
                detail=f"SGD rate not available for base currency {base_currency}.",
            )

        rate = Decimal(str(sgd_rate))
        _rate_cache[base_currency] = {"rate": rate, "fetched_at": now}
        return rate


async def get_all_live_rates() -> dict[str, Decimal]:
    """
    Purpose: Fetch all available rates with SGD as base from open.er-api.com.
             Used by GET /fx/live-rates endpoint.
    Inputs: none
    Outputs: dict[str, Decimal] — {currency_code: rate_in_sgd}
    Owner: [Claude]
    """
    url = FX_LIVE_RATE_API_URL.format(base=FX_BASE_CURRENCY)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Exchange rate service unavailable. Try again shortly.",
        ) from exc

    return {k: Decimal(str(v)) for k, v in data.get("rates", {}).items()}


def get_cached_status(base_currency: str) -> bool:
    """
    Purpose: Return True if a valid cached rate exists for base_currency.
    Inputs: base_currency (str)
    Outputs: bool
    Owner: [Claude]
    """
    cached = _rate_cache.get(base_currency)
    if not cached:
        return False
    return (time.time() - cached["fetched_at"]) < FX_CACHE_TTL_SECONDS


async def resolve_rate(sheet_id, base_currency: str, db: Session) -> Decimal:
    """
    Purpose: Resolve the effective SGD rate for a currency pair on a given sheet.
             Priority: FXRateOverride (sheet-specific) > live rate from open.er-api.com.
             NOTE: Makes one DB query per call. Use fetch_sheet_overrides + resolve_rate_batch
             instead when processing multiple line items to avoid N+1 queries.
    Inputs: sheet_id (UUID), base_currency (str), db (SQLAlchemy Session)
    Outputs: Decimal — effective rate (1 base_currency = X SGD)
    Owner: [Claude]
    """
    if base_currency == FX_BASE_CURRENCY:
        return Decimal("1")

    override = (
        db.query(FXRateOverride)
        .filter(
            FXRateOverride.costing_sheet_id == sheet_id,
            FXRateOverride.base_currency == base_currency,
            FXRateOverride.target_currency == FX_BASE_CURRENCY,
        )
        .first()
    )
    if override:
        return Decimal(str(override.override_rate))

    return await get_live_rate(base_currency)


def fetch_sheet_overrides(sheet_id, db) -> dict:
    """
    Purpose: Pre-fetch ALL FX overrides for a sheet in a single DB query.
             Returns a dict keyed by base_currency for O(1) lookup during item iteration.
             Use this before processing a list of line items to eliminate N+1 DB queries.
    Inputs: sheet_id (UUID or str), db (SQLAlchemy Session)
    Outputs: dict[str, Decimal] — {base_currency: override_rate_in_sgd}
    Owner: [Claude]
    """
    from decimal import Decimal
    from app.models.fx_rate_override import FXRateOverride
    rows = (
        db.query(FXRateOverride)
        .filter(
            FXRateOverride.costing_sheet_id == sheet_id,
            FXRateOverride.target_currency == FX_BASE_CURRENCY,
        )
        .all()
    )
    return {row.base_currency: Decimal(str(row.override_rate)) for row in rows}


async def resolve_rate_batch(overrides: dict, base_currency: str):
    """
    Purpose: Resolve the effective SGD rate using a pre-fetched overrides dict.
             Override-first; falls back to live rate (1hr cached). No DB query.
             Use after fetch_sheet_overrides to process many items without N+1 queries.
    Inputs: overrides (dict[str, Decimal] from fetch_sheet_overrides), base_currency (str)
    Outputs: Decimal — effective rate (1 base_currency = X SGD)
    Owner: [Claude]
    """
    from decimal import Decimal
    if base_currency == FX_BASE_CURRENCY:
        return Decimal("1")
    if base_currency in overrides:
        return overrides[base_currency]
    return await get_live_rate(base_currency)
