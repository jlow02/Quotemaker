"""
Purpose: FX rate endpoints — live rates and per-sheet overrides.
Owner: [Claude]
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.costing_sheet import CostingSheet
from app.models.fx_rate_override import FXRateOverride
from app.models.user import User
from app.schemas.fx_rate_override import (
    FXRateOverrideCreate, FXRateOverrideRead, FXRateOverrideUpdate, LiveRatesResponse
)
from app.services.fx_service import get_all_live_rates, get_cached_status
from app.constants import FX_BASE_CURRENCY

router = APIRouter(tags=["FX Rates"])


def _owned_sheet(sheet_id: str, user_id, db: Session) -> CostingSheet:
    """
    Purpose: Fetch a costing sheet owned by the current user or raise 404.
    Inputs: sheet_id (str), user_id, db
    Outputs: CostingSheet
    Owner: [Claude]
    """
    sheet = db.query(CostingSheet).filter(
        CostingSheet.id == sheet_id, CostingSheet.user_id == user_id
    ).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Costing sheet not found.")
    return sheet


@router.get("/fx/live-rates", response_model=LiveRatesResponse)
async def get_live_rates(_: User = Depends(get_current_user)):
    """
    Purpose: Return current exchange rates from open.er-api.com (1hr cached).
             Base currency is always SGD.
    Inputs: none
    Outputs: LiveRatesResponse
    Owner: [Claude]
    """
    rates = await get_all_live_rates()
    cached = get_cached_status(FX_BASE_CURRENCY)
    return LiveRatesResponse(base=FX_BASE_CURRENCY, rates=rates, cached=cached)


@router.get("/costing-sheets/{sheet_id}/fx-overrides", response_model=list[FXRateOverrideRead])
def list_fx_overrides(
    sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: List all FX rate overrides for a costing sheet.
    Inputs: sheet_id (str UUID)
    Outputs: list[FXRateOverrideRead]
    Owner: [Claude]
    """
    _owned_sheet(sheet_id, current_user.id, db)
    return db.query(FXRateOverride).filter(FXRateOverride.costing_sheet_id == sheet_id).all()


@router.post("/costing-sheets/{sheet_id}/fx-overrides", response_model=FXRateOverrideRead, status_code=status.HTTP_201_CREATED)
def create_fx_override(
    sheet_id: str,
    body: FXRateOverrideCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Create or replace an FX override for a currency pair on a sheet.
             Atomic upsert on (costing_sheet_id, base_currency, target_currency).
             Uses INSERT ... ON CONFLICT DO UPDATE to prevent race conditions —
             two concurrent requests for the same currency pair are serialised
             by the database rather than risking a UniqueViolation 500 error.
    Inputs: sheet_id (str UUID), FXRateOverrideCreate
    Outputs: FXRateOverrideRead (HTTP 201)
    Owner: [Claude]
    """
    _owned_sheet(sheet_id, current_user.id, db)

    stmt = (
        pg_insert(FXRateOverride)
        .values(
            costing_sheet_id=sheet_id,
            base_currency=body.base_currency,
            target_currency=body.target_currency,
            override_rate=body.override_rate,
        )
        .on_conflict_do_update(
            constraint="uq_fx_override",
            set_={
                "override_rate": body.override_rate,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        .returning(FXRateOverride.id)
    )
    override_id = db.execute(stmt).scalar_one()
    db.commit()
    override = db.query(FXRateOverride).filter(FXRateOverride.id == override_id).first()
    return override


@router.put("/fx-overrides/{override_id}", response_model=FXRateOverrideRead)
def update_fx_override(
    override_id: str,
    body: FXRateOverrideUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Update the override rate for an FX override record.
    Inputs: override_id (str UUID), FXRateOverrideUpdate
    Outputs: FXRateOverrideRead
    Owner: [Claude]
    """
    override = (
        db.query(FXRateOverride)
        .join(CostingSheet)
        .filter(FXRateOverride.id == override_id, CostingSheet.user_id == current_user.id)
        .first()
    )
    if not override:
        raise HTTPException(status_code=404, detail="FX override not found.")
    override.override_rate = body.override_rate
    db.commit()
    db.refresh(override)
    return override


@router.delete("/fx-overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fx_override(
    override_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Delete an FX override. Reverts to live rate for that currency pair.
    Inputs: override_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    override = (
        db.query(FXRateOverride)
        .join(CostingSheet)
        .filter(FXRateOverride.id == override_id, CostingSheet.user_id == current_user.id)
        .first()
    )
    if not override:
        raise HTTPException(status_code=404, detail="FX override not found.")
    db.delete(override)
    db.commit()
