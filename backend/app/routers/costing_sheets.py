"""
Purpose: CostingSheet CRUD + duplicate endpoints. Private per user.
         Ref numbers auto-generated atomically on create. Duplicate creates a new sheet.
Owner: [Claude]
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.costing_sheet import CostingSheet
from app.models.quote_export import QuoteExport
from app.models.scenario import Scenario
from app.models.line_item import LineItem
from app.models.user import User
from app.schemas.costing_sheet import (
    CostingSheetCreate, CostingSheetList, CostingSheetRead, CostingSheetUpdate
)
from app.services.ref_number_service import generate_ref_number

router = APIRouter(prefix="/costing-sheets", tags=["Costing Sheets"])


def _owned_sheet(sheet_id: str, user_id, db: Session) -> CostingSheet:
    """
    Purpose: Fetch a costing sheet owned by the current user or raise 404.
    Inputs: sheet_id (str), user_id (UUID), db (Session)
    Outputs: CostingSheet
    Owner: [Claude]
    """
    sheet = db.query(CostingSheet).filter(
        CostingSheet.id == sheet_id,
        CostingSheet.user_id == user_id,
    ).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Costing sheet not found.")
    return sheet


@router.post("", response_model=CostingSheetRead, status_code=status.HTTP_201_CREATED)
def create_costing_sheet(
    body: CostingSheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Create a new costing sheet. Atomically reserves the next ref number
             for this user in the current month via INSERT...ON CONFLICT DO UPDATE.
    Inputs: CostingSheetCreate
    Outputs: CostingSheetRead
    Owner: [Claude]
    """
    ref_number = generate_ref_number(
        str(current_user.id), current_user.numeric_user_id, db
    )
    sheet = CostingSheet(
        user_id=current_user.id,
        ref_number=ref_number,
        date=body.date or date.today(),
        quote_title=body.quote_title,
        client_name=body.client_name,
        organisation_id=body.organisation_id,
        contact_id=body.contact_id,
        contact_name=body.contact_name,
        contact_email=body.contact_email,
        payment_term=body.payment_term,
        quotation_validity_days=body.quotation_validity_days,
        lead_time=body.lead_time,
        local_tax=body.local_tax,
        warranty=body.warranty,
        general_notes=body.general_notes,
    )
    db.add(sheet)
    db.commit()
    db.refresh(sheet)
    return sheet


@router.get("", response_model=list[CostingSheetList])
def list_costing_sheets(
    client_name: Optional[str] = Query(None),
    ref_number: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: List the authenticated user's costing sheets with optional filters.
    Inputs: client_name, ref_number, date_from, date_to (all optional query params)
    Outputs: list[CostingSheetList]
    Owner: [Claude]
    """
    q = db.query(CostingSheet).filter(CostingSheet.user_id == current_user.id)
    if client_name:
        q = q.filter(CostingSheet.client_name.ilike(f"%{client_name}%"))
    if ref_number:
        q = q.filter(CostingSheet.ref_number.ilike(f"%{ref_number}%"))
    if date_from:
        q = q.filter(CostingSheet.date >= date_from)
    if date_to:
        q = q.filter(CostingSheet.date <= date_to)
    return q.order_by(CostingSheet.created_at.desc()).all()


@router.get("/{sheet_id}", response_model=CostingSheetRead)
def get_costing_sheet(
    sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Get a single costing sheet with its scenarios (line items loaded separately).
    Inputs: sheet_id (str UUID)
    Outputs: CostingSheetRead
    Owner: [Claude]
    """
    sheet = (
        db.query(CostingSheet)
        .options(selectinload(CostingSheet.scenarios))
        .filter(CostingSheet.id == sheet_id, CostingSheet.user_id == current_user.id)
        .first()
    )
    if not sheet:
        raise HTTPException(status_code=404, detail="Costing sheet not found.")
    return sheet


@router.put("/{sheet_id}", response_model=CostingSheetRead)
def update_costing_sheet(
    sheet_id: str,
    body: CostingSheetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Update costing sheet header and terms fields.
    Inputs: sheet_id (str UUID), CostingSheetUpdate
    Outputs: CostingSheetRead
    Owner: [Claude]
    """
    sheet = _owned_sheet(sheet_id, current_user.id, db)
    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(sheet, field, value)
    db.commit()
    db.refresh(sheet)
    return sheet


@router.post("/{sheet_id}/duplicate", response_model=CostingSheetRead, status_code=status.HTTP_201_CREATED)
def duplicate_costing_sheet(
    sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Duplicate a costing sheet — new ref number, today's date, all scenarios copied.
    Inputs: sheet_id (str UUID)
    Outputs: CostingSheetRead — the new duplicate sheet
    Owner: [Claude]
    """
    original = (
        db.query(CostingSheet)
        .options(
            selectinload(CostingSheet.scenarios).selectinload(Scenario.line_items)
        )
        .filter(CostingSheet.id == sheet_id, CostingSheet.user_id == current_user.id)
        .first()
    )
    if not original:
        raise HTTPException(status_code=404, detail="Costing sheet not found.")

    new_ref = generate_ref_number(str(current_user.id), current_user.numeric_user_id, db)
    new_sheet = CostingSheet(
        user_id=current_user.id,
        ref_number=new_ref,
        date=date.today(),
        quote_title=f"{original.quote_title} (Copy)",
        client_name=original.client_name,
        organisation_id=original.organisation_id,
        contact_id=original.contact_id,
        contact_name=original.contact_name,
        contact_email=original.contact_email,
        payment_term=original.payment_term,
        quotation_validity_days=original.quotation_validity_days,
        lead_time=original.lead_time,
        local_tax=original.local_tax,
        warranty=original.warranty,
        general_notes=original.general_notes,
    )
    db.add(new_sheet)
    db.flush()  # Get new_sheet.id before adding scenarios

    # Copy scenarios and their line items
    for scenario in original.scenarios:
        new_scenario = Scenario(
            costing_sheet_id=new_sheet.id,
            name=scenario.name,
            discount_type=scenario.discount_type,
            discount_value=scenario.discount_value,
            show_gst=scenario.show_gst,
            notes_exclusions=scenario.notes_exclusions,
            display_order=scenario.display_order,
        )
        db.add(new_scenario)
        db.flush()

        # Map old line item ids to new ones for parent reference
        id_map: dict = {}
        for item in sorted(scenario.line_items, key=lambda x: (x.display_order, str(x.id))):
            new_item = LineItem(
                scenario_id=new_scenario.id,
                section=item.section,
                display_order=item.display_order,
                description=item.description,
                sub_specs=item.sub_specs,
                qty=item.qty,
                unit=item.unit,
                cost_rate=item.cost_rate,
                cost_currency=item.cost_currency,
                markup_pct=item.markup_pct,
                contingency_pct=item.contingency_pct,
                is_visible=item.is_visible,
                is_bundle_parent=item.is_bundle_parent,
                bundle_override_price=item.bundle_override_price,
                is_bundle_override_active=item.is_bundle_override_active,
            )
            db.add(new_item)
            db.flush()
            id_map[item.id] = new_item.id

        # Relink parent references
        for item in scenario.line_items:
            if item.parent_line_item_id:
                new_child_id = id_map.get(item.id)
                new_parent_id = id_map.get(item.parent_line_item_id)
                if new_child_id and new_parent_id:
                    db.query(LineItem).filter(LineItem.id == new_child_id).update(
                        {"parent_line_item_id": new_parent_id}
                    )

    db.commit()
    db.refresh(new_sheet)
    return new_sheet


@router.delete("/{sheet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_costing_sheet(
    sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Delete a costing sheet. Blocked with 409 if any QuoteExport records exist.
    Inputs: sheet_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    sheet = _owned_sheet(sheet_id, current_user.id, db)
    export_count = db.query(QuoteExport).filter(
        QuoteExport.costing_sheet_id == sheet.id
    ).count()
    if export_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete: {export_count} export(s) exist. Delete all exports first.",
        )
    db.delete(sheet)
    db.commit()
