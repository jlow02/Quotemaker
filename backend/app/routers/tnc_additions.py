"""
Purpose: T&C Addition endpoints — both sheet-specific and global additions.
Owner: [Claude]
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.costing_sheet import CostingSheet
from app.models.tnc_addition import CostingSheetTncAddition, GlobalTncAddition
from app.models.user import User
from app.schemas.tnc_addition import TncCreate, TncRead, TncUpdate

router = APIRouter(tags=["T&C Additions"])


def _owned_sheet(sheet_id: str, user_id, db: Session) -> CostingSheet:
    sheet = db.query(CostingSheet).filter(
        CostingSheet.id == sheet_id, CostingSheet.user_id == user_id
    ).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Costing sheet not found.")
    return sheet


# ── Sheet-level T&C ──────────────────────────────────────────────────────────

@router.get("/costing-sheets/{sheet_id}/tnc-additions", response_model=list[TncRead])
def list_sheet_tnc(
    sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: List sheet-specific T&C bullet points.
    Inputs: sheet_id (str UUID)
    Outputs: list[TncRead]
    Owner: [Claude]
    """
    _owned_sheet(sheet_id, current_user.id, db)
    items = (
        db.query(CostingSheetTncAddition)
        .filter(CostingSheetTncAddition.costing_sheet_id == sheet_id)
        .order_by(CostingSheetTncAddition.display_order)
        .all()
    )
    return [TncRead(
        id=item.id, bullet_point=item.bullet_point, display_order=item.display_order,
        costing_sheet_id=item.costing_sheet_id, created_at=item.created_at, updated_at=item.updated_at
    ) for item in items]


@router.post("/costing-sheets/{sheet_id}/tnc-additions", response_model=TncRead, status_code=status.HTTP_201_CREATED)
def create_sheet_tnc(
    sheet_id: str,
    body: TncCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Add a T&C bullet to a costing sheet.
    Inputs: sheet_id (str UUID), TncCreate
    Outputs: TncRead
    Owner: [Claude]
    """
    _owned_sheet(sheet_id, current_user.id, db)
    item = CostingSheetTncAddition(
        costing_sheet_id=sheet_id,
        bullet_point=body.bullet_point,
        display_order=body.display_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return TncRead(
        id=item.id, bullet_point=item.bullet_point, display_order=item.display_order,
        costing_sheet_id=item.costing_sheet_id, created_at=item.created_at, updated_at=item.updated_at
    )


@router.put("/tnc-additions/{tnc_id}", response_model=TncRead)
def update_tnc(
    tnc_id: str,
    body: TncUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Update a sheet-level T&C bullet (bullet_point or display_order).
    Inputs: tnc_id (str UUID), TncUpdate
    Outputs: TncRead
    Owner: [Claude]
    """
    item = (
        db.query(CostingSheetTncAddition)
        .join(CostingSheet)
        .filter(CostingSheetTncAddition.id == tnc_id, CostingSheet.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="T&C addition not found.")
    if body.bullet_point is not None:
        item.bullet_point = body.bullet_point
    if body.display_order is not None:
        item.display_order = body.display_order
    db.commit()
    db.refresh(item)
    return TncRead(
        id=item.id, bullet_point=item.bullet_point, display_order=item.display_order,
        costing_sheet_id=item.costing_sheet_id, created_at=item.created_at, updated_at=item.updated_at
    )


@router.delete("/tnc-additions/{tnc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tnc(
    tnc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Delete a sheet-level T&C bullet.
    Inputs: tnc_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    item = (
        db.query(CostingSheetTncAddition)
        .join(CostingSheet)
        .filter(CostingSheetTncAddition.id == tnc_id, CostingSheet.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="T&C addition not found.")
    db.delete(item)
    db.commit()


# ── Global T&C ───────────────────────────────────────────────────────────────

@router.get("/settings/tnc-additions", response_model=list[TncRead])
def list_global_tnc(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: List global T&C additions (shared across all costing sheets on export).
    Inputs: none
    Outputs: list[TncRead]
    Owner: [Claude]
    """
    items = db.query(GlobalTncAddition).order_by(GlobalTncAddition.display_order).all()
    return [TncRead(
        id=item.id, bullet_point=item.bullet_point, display_order=item.display_order,
        costing_sheet_id=None, created_at=item.created_at, updated_at=item.updated_at
    ) for item in items]


@router.post("/settings/tnc-additions", response_model=TncRead, status_code=status.HTTP_201_CREATED)
def create_global_tnc(
    body: TncCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Create a new global T&C addition.
    Inputs: TncCreate
    Outputs: TncRead
    Owner: [Claude]
    """
    item = GlobalTncAddition(bullet_point=body.bullet_point, display_order=body.display_order)
    db.add(item)
    db.commit()
    db.refresh(item)
    return TncRead(
        id=item.id, bullet_point=item.bullet_point, display_order=item.display_order,
        costing_sheet_id=None, created_at=item.created_at, updated_at=item.updated_at
    )


@router.put("/settings/tnc-additions/{tnc_id}", response_model=TncRead)
def update_global_tnc(
    tnc_id: str,
    body: TncUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Update a global T&C addition.
    Inputs: tnc_id (str UUID), TncUpdate
    Outputs: TncRead
    Owner: [Claude]
    """
    item = db.query(GlobalTncAddition).filter(GlobalTncAddition.id == tnc_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Global T&C addition not found.")
    if body.bullet_point is not None:
        item.bullet_point = body.bullet_point
    if body.display_order is not None:
        item.display_order = body.display_order
    db.commit()
    db.refresh(item)
    return TncRead(
        id=item.id, bullet_point=item.bullet_point, display_order=item.display_order,
        costing_sheet_id=None, created_at=item.created_at, updated_at=item.updated_at
    )


@router.delete("/settings/tnc-additions/{tnc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_global_tnc(
    tnc_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Delete a global T&C addition.
    Inputs: tnc_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    item = db.query(GlobalTncAddition).filter(GlobalTncAddition.id == tnc_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Global T&C addition not found.")
    db.delete(item)
    db.commit()
