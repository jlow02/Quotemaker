"""
Purpose: ScenarioTemplate CRUD + apply endpoints.
         Templates are global (no user_id). Apply copies line items into a new Scenario.
Owner: [Claude]
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.costing_sheet import CostingSheet
from app.models.line_item import LineItem
from app.models.scenario import Scenario
from app.models.scenario_template import ScenarioTemplate, TemplateLineItem
from app.models.user import User
from app.schemas.scenario_template import (
    TemplateCreate, TemplateRead, TemplateUpdate
)

router = APIRouter(prefix="/scenario-templates", tags=["Scenario Templates"])


@router.get("", response_model=list[TemplateRead])
def list_templates(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: List all scenario templates.
    Inputs: none
    Outputs: list[TemplateRead]
    Owner: [Claude]
    """
    return (
        db.query(ScenarioTemplate)
        .options(selectinload(ScenarioTemplate.template_line_items))
        .order_by(ScenarioTemplate.name)
        .all()
    )


@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(
    body: TemplateCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Create a new scenario template.
    Inputs: TemplateCreate
    Outputs: TemplateRead
    Owner: [Claude]
    """
    template = ScenarioTemplate(name=body.name, notes_exclusions=body.notes_exclusions)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateRead)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Get a template with all its line items.
    Inputs: template_id (str UUID)
    Outputs: TemplateRead
    Owner: [Claude]
    """
    template = (
        db.query(ScenarioTemplate)
        .options(
            selectinload(ScenarioTemplate.template_line_items)
            .selectinload(TemplateLineItem.sub_components)
        )
        .filter(ScenarioTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")
    return template


@router.put("/{template_id}", response_model=TemplateRead)
def update_template(
    template_id: str,
    body: TemplateUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Update a template's name or notes_exclusions.
    Inputs: template_id (str UUID), TemplateUpdate
    Outputs: TemplateRead
    Owner: [Claude]
    """
    template = db.query(ScenarioTemplate).filter(ScenarioTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")
    if body.name is not None:
        template.name = body.name
    if body.notes_exclusions is not None:
        template.notes_exclusions = body.notes_exclusions
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Delete a scenario template and all its line items (cascades).
    Inputs: template_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    template = db.query(ScenarioTemplate).filter(ScenarioTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")
    db.delete(template)
    db.commit()


@router.post("/{template_id}/apply/{sheet_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
def apply_template(
    template_id: str,
    sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Apply a template to a costing sheet — copy all template line items and notes
             into a new Scenario. No FK link to template; changes to template don't affect this sheet.
    Inputs: template_id (str UUID), sheet_id (str UUID)
    Outputs: dict with new scenario_id
    Owner: [Claude]
    """
    # Verify ownership of sheet
    sheet = db.query(CostingSheet).filter(
        CostingSheet.id == sheet_id, CostingSheet.user_id == current_user.id
    ).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Costing sheet not found.")

    template = (
        db.query(ScenarioTemplate)
        .options(
            selectinload(ScenarioTemplate.template_line_items)
            .selectinload(TemplateLineItem.sub_components)
        )
        .filter(ScenarioTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")

    # Determine display_order for new scenario
    max_order = db.query(Scenario).filter(
        Scenario.costing_sheet_id == sheet_id
    ).count()

    new_scenario = Scenario(
        costing_sheet_id=sheet_id,
        name=template.name,
        notes_exclusions=template.notes_exclusions,
        display_order=max_order,
    )
    db.add(new_scenario)
    db.flush()

    # Copy top-level items first, tracking id mapping for sub-components
    id_map: dict = {}
    top_level = [t for t in template.template_line_items if t.parent_template_line_item_id is None]
    for tli in sorted(top_level, key=lambda x: x.display_order):
        new_item = LineItem(
            scenario_id=new_scenario.id,
            section=tli.section,
            display_order=tli.display_order,
            description=tli.description,
            sub_specs=tli.sub_specs,
            qty=tli.qty,
            unit=tli.unit,
            cost_rate=tli.cost_rate,
            cost_currency=tli.cost_currency,
            markup_pct=tli.markup_pct,
            contingency_pct=tli.contingency_pct,
            is_bundle_parent=tli.is_bundle_parent,
        )
        db.add(new_item)
        db.flush()
        id_map[tli.id] = new_item.id

        for sub in sorted(tli.sub_components, key=lambda x: x.display_order):
            new_sub = LineItem(
                scenario_id=new_scenario.id,
                parent_line_item_id=new_item.id,
                section=tli.section,
                display_order=sub.display_order,
                description=sub.description,
                sub_specs=sub.sub_specs,
                qty=sub.qty,
                unit=sub.unit,
                cost_rate=sub.cost_rate,
                cost_currency=sub.cost_currency,
                markup_pct=sub.markup_pct,
                contingency_pct=sub.contingency_pct,
                is_bundle_parent=False,
            )
            db.add(new_sub)

    db.commit()
    return {"scenario_id": str(new_scenario.id), "message": f"Template '{template.name}' applied successfully."}
