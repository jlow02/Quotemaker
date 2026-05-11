"""
Purpose: Scenario CRUD endpoints. Scenarios belong to a CostingSheet.
Owner: [Claude]
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.costing_sheet import CostingSheet
from app.models.quote_export import QuoteExport
from app.models.scenario import Scenario
from app.models.user import User
from app.schemas.scenario import ScenarioCreate, ScenarioRead, ScenarioUpdate

router = APIRouter(tags=["Scenarios"])


def _owned_sheet(sheet_id: str, user_id, db: Session) -> CostingSheet:
    """
    Purpose: Fetch a costing sheet owned by the current user or raise 404.
    Inputs: sheet_id (str), user_id, db (Session)
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


def _owned_scenario(scenario_id: str, user_id, db: Session) -> Scenario:
    """
    Purpose: Fetch a scenario belonging to a sheet owned by current user or raise 404.
    Inputs: scenario_id (str), user_id, db (Session)
    Outputs: Scenario
    Owner: [Claude]
    """
    scenario = (
        db.query(Scenario)
        .join(CostingSheet, Scenario.costing_sheet_id == CostingSheet.id)
        .filter(Scenario.id == scenario_id, CostingSheet.user_id == user_id)
        .first()
    )
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    return scenario


@router.post("/costing-sheets/{sheet_id}/scenarios", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
def create_scenario(
    sheet_id: str,
    body: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Create a new scenario within a costing sheet.
    Inputs: sheet_id (str UUID), ScenarioCreate
    Outputs: ScenarioRead
    Owner: [Claude]
    """
    _owned_sheet(sheet_id, current_user.id, db)
    scenario = Scenario(
        costing_sheet_id=sheet_id,
        name=body.name,
        discount_type=body.discount_type,
        discount_value=body.discount_value,
        show_gst=body.show_gst,
        notes_exclusions=body.notes_exclusions,
        display_order=body.display_order,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/costing-sheets/{sheet_id}/scenarios", response_model=list[ScenarioRead])
def list_scenarios(
    sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: List all scenarios for a costing sheet.
    Inputs: sheet_id (str UUID)
    Outputs: list[ScenarioRead]
    Owner: [Claude]
    """
    _owned_sheet(sheet_id, current_user.id, db)
    return (
        db.query(Scenario)
        .filter(Scenario.costing_sheet_id == sheet_id)
        .order_by(Scenario.display_order)
        .all()
    )


@router.get("/scenarios/{scenario_id}", response_model=ScenarioRead)
def get_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Get a single scenario (line items loaded via separate endpoint).
    Inputs: scenario_id (str UUID)
    Outputs: ScenarioRead
    Owner: [Claude]
    """
    return _owned_scenario(scenario_id, current_user.id, db)


@router.put("/scenarios/{scenario_id}", response_model=ScenarioRead)
def update_scenario(
    scenario_id: str,
    body: ScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Update scenario name, discount, show_gst, or notes_exclusions.
    Inputs: scenario_id (str UUID), ScenarioUpdate
    Outputs: ScenarioRead
    Owner: [Claude]
    """
    scenario = _owned_scenario(scenario_id, current_user.id, db)
    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(scenario, field, value)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Delete a scenario. Blocked with 409 if any QuoteExport records exist for it.
    Inputs: scenario_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    scenario = _owned_scenario(scenario_id, current_user.id, db)
    export_count = db.query(QuoteExport).filter(
        QuoteExport.scenario_id == scenario.id
    ).count()
    if export_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete: {export_count} export(s) exist. Delete all exports first.",
        )
    db.delete(scenario)
    db.commit()
