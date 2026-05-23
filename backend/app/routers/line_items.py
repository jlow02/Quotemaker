"""
Purpose: LineItem CRUD + bundle operations + reorder. Core of the costing sheet.
         Sub-component updates automatically clear parent bundle override (atomic).
         selectinload(depth=2) used to avoid N+1 on bundle parents with sub-components.
Owner: [Claude]
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.costing_sheet import CostingSheet
from app.models.line_item import LineItem
from app.models.scenario import Scenario
from app.models.user import User
from app.schemas.line_item import (
    BulkDeleteRequest, BundleOverridePatch, LineItemCreate, LineItemRead, LineItemUpdate, ReorderRequest
)
from app.services.fx_service import fetch_sheet_overrides, resolve_rate_batch
from app.services.pricing_service import compute_item_from_orm

router = APIRouter(tags=["Line Items"])


def _owned_scenario(scenario_id: str, user_id, db: Session) -> Scenario:
    """
    Purpose: Fetch a scenario accessible by the current user or raise 404.
    Inputs: scenario_id (str), user_id, db
    Outputs: Scenario
    Owner: [Claude]
    """
    s = (
        db.query(Scenario)
        .join(CostingSheet)
        .filter(Scenario.id == scenario_id, CostingSheet.user_id == user_id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    return s


def _owned_line_item(item_id: str, user_id, db: Session) -> LineItem:
    """
    Purpose: Fetch a line item accessible by the current user or raise 404.
    Inputs: item_id (str), user_id, db
    Outputs: LineItem
    Owner: [Claude]
    """
    item = (
        db.query(LineItem)
        .join(Scenario)
        .join(CostingSheet)
        .filter(LineItem.id == item_id, CostingSheet.user_id == user_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found.")
    return item


async def _inject_pricing(
    item: LineItem,
    overrides: dict[str, Decimal],
) -> LineItemRead:
    """
    Purpose: Convert a LineItem ORM object to LineItemRead with computed pricing injected.
             Recursively handles sub-components for bundle parents. Uses a pre-fetched
             overrides dict to avoid N+1 DB queries — fetch_sheet_overrides() must be
             called once per request before calling this function.
    Inputs: item (LineItem), overrides (dict[str, Decimal] from fetch_sheet_overrides)
    Outputs: LineItemRead with .computed populated
    Owner: [Claude]
    """
    sub_totals: list[Decimal] = []
    sub_reads: list[LineItemRead] = []

    for sub in item.sub_components:
        sub_read = await _inject_pricing(sub, overrides)
        sub_reads.append(sub_read)
        if sub.is_visible and sub_read.computed and sub_read.computed.line_total_sgd:
            sub_totals.append(sub_read.computed.line_total_sgd)

    fx_rate = await resolve_rate_batch(overrides, item.cost_currency)
    computed = compute_item_from_orm(item, fx_rate, sub_totals if sub_totals else None)

    read = LineItemRead.model_validate(item)
    read.computed = computed
    read.sub_components = sub_reads
    return read


@router.post("/scenarios/{scenario_id}/line-items", response_model=LineItemRead, status_code=status.HTTP_201_CREATED)
async def create_line_item(
    scenario_id: str,
    body: LineItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Create a top-level line item or bundle sub-component within a scenario.
    Inputs: scenario_id (str UUID), LineItemCreate
    Outputs: LineItemRead with computed pricing
    Owner: [Claude]
    """
    scenario = _owned_scenario(scenario_id, current_user.id, db)
    sheet = db.query(CostingSheet).filter(CostingSheet.id == scenario.costing_sheet_id).first()

    # If sub-component: validate parent exists and is a bundle parent
    if body.parent_line_item_id:
        parent = db.query(LineItem).filter(
            LineItem.id == body.parent_line_item_id,
            LineItem.scenario_id == scenario_id,
            LineItem.is_bundle_parent.is_(True),
        ).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent line item not found or is not a bundle parent.")

    item = LineItem(
        scenario_id=scenario_id,
        parent_line_item_id=body.parent_line_item_id,
        section=body.section,
        display_order=body.display_order,
        description=body.description,
        sub_specs=body.sub_specs,
        qty=body.qty,
        unit=body.unit,
        cost_rate=body.cost_rate,
        cost_currency=body.cost_currency,
        markup_pct=body.markup_pct,
        contingency_pct=body.contingency_pct,
        is_visible=body.is_visible,
        is_bundle_parent=body.is_bundle_parent,
    )
    db.add(item)

    # Adding a sub-component clears parent override
    if body.parent_line_item_id:
        db.query(LineItem).filter(LineItem.id == body.parent_line_item_id).update(
            {"is_bundle_override_active": False, "bundle_override_price": None}
        )

    db.commit()
    db.refresh(item)
    # Reload with sub_components
    item = db.query(LineItem).options(selectinload(LineItem.sub_components)).filter(LineItem.id == item.id).first()
    overrides = fetch_sheet_overrides(sheet.id, db)
    return await _inject_pricing(item, overrides)


@router.get("/scenarios/{scenario_id}/line-items", response_model=list[LineItemRead])
async def list_line_items(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: List all top-level line items for a scenario, with bundle sub-components nested.
             Uses selectinload(depth=2) to avoid N+1 on bundles.
    Inputs: scenario_id (str UUID)
    Outputs: list[LineItemRead] with computed pricing
    Owner: [Claude]
    """
    scenario = _owned_scenario(scenario_id, current_user.id, db)
    sheet = db.query(CostingSheet).filter(CostingSheet.id == scenario.costing_sheet_id).first()

    items = (
        db.query(LineItem)
        .options(selectinload(LineItem.sub_components).selectinload(LineItem.sub_components))
        .filter(
            LineItem.scenario_id == scenario_id,
            LineItem.parent_line_item_id.is_(None),
        )
        .order_by(LineItem.section, LineItem.display_order)
        .all()
    )
    overrides = fetch_sheet_overrides(sheet.id, db)
    return [await _inject_pricing(item, overrides) for item in items]


@router.get("/line-items/{line_item_id}", response_model=LineItemRead)
async def get_line_item(
    line_item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Get a single line item with computed pricing and sub-components.
    Inputs: line_item_id (str UUID)
    Outputs: LineItemRead
    Owner: [Claude]
    """
    item = _owned_line_item(line_item_id, current_user.id, db)
    item = db.query(LineItem).options(
        selectinload(LineItem.sub_components).selectinload(LineItem.sub_components)
    ).filter(LineItem.id == item.id).first()
    scenario = db.query(Scenario).filter(Scenario.id == item.scenario_id).first()
    sheet = db.query(CostingSheet).filter(CostingSheet.id == scenario.costing_sheet_id).first()
    overrides = fetch_sheet_overrides(sheet.id, db)
    return await _inject_pricing(item, overrides)


@router.put("/line-items/{line_item_id}", response_model=LineItemRead)
async def update_line_item(
    line_item_id: str,
    body: LineItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Update a line item. If the item is a sub-component, clears the parent bundle override
             atomically in the same transaction.
    Inputs: line_item_id (str UUID), LineItemUpdate
    Outputs: LineItemRead with computed pricing
    Owner: [Claude]
    """
    item = _owned_line_item(line_item_id, current_user.id, db)

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    # Clear parent override atomically when sub-component is updated
    if item.parent_line_item_id:
        db.query(LineItem).filter(LineItem.id == item.parent_line_item_id).update(
            {"is_bundle_override_active": False, "bundle_override_price": None}
        )

    db.commit()
    db.refresh(item)
    item = db.query(LineItem).options(
        selectinload(LineItem.sub_components).selectinload(LineItem.sub_components)
    ).filter(LineItem.id == item.id).first()
    scenario = db.query(Scenario).filter(Scenario.id == item.scenario_id).first()
    sheet = db.query(CostingSheet).filter(CostingSheet.id == scenario.costing_sheet_id).first()
    overrides = fetch_sheet_overrides(sheet.id, db)
    return await _inject_pricing(item, overrides)


@router.delete("/line-items/{line_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line_item(
    line_item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Delete a line item. Cascades to sub-components (via DB ON DELETE CASCADE).
    Inputs: line_item_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    item = _owned_line_item(line_item_id, current_user.id, db)
    db.delete(item)
    db.commit()


@router.delete("/scenarios/{scenario_id}/line-items/bulk", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_line_items(
    scenario_id: str,
    body: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Delete multiple line items in a single request. Only deletes items that
             belong to the scenario and are accessible by the current user.
             Silently skips IDs that don't match (idempotent for already-deleted items).
             Sub-components cascade via DB ON DELETE CASCADE.
    Inputs: scenario_id (str UUID), BulkDeleteRequest (ids: list[UUID])
    Outputs: 204 No Content
    Owner: [Claude]
    """
    _owned_scenario(scenario_id, current_user.id, db)
    if not body.ids:
        return
    db.query(LineItem).filter(
        LineItem.id.in_(body.ids),
        LineItem.scenario_id == scenario_id,
    ).delete(synchronize_session=False)
    db.commit()


@router.post("/line-items/{line_item_id}/bundle-components", response_model=LineItemRead, status_code=status.HTTP_201_CREATED)
async def add_bundle_component(
    line_item_id: str,
    body: LineItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Add a sub-component to a bundle parent. Clears parent bundle override.
    Inputs: line_item_id (str UUID, bundle parent), LineItemCreate
    Outputs: LineItemRead (the new sub-component)
    Owner: [Claude]
    """
    parent = _owned_line_item(line_item_id, current_user.id, db)
    if not parent.is_bundle_parent:
        raise HTTPException(status_code=400, detail="Line item is not a bundle parent.")

    sub = LineItem(
        scenario_id=parent.scenario_id,
        parent_line_item_id=parent.id,
        section=parent.section,  # Sub-components inherit section from parent
        display_order=body.display_order,
        description=body.description,
        sub_specs=body.sub_specs,
        qty=body.qty,
        unit=body.unit,
        cost_rate=body.cost_rate,
        cost_currency=body.cost_currency,
        markup_pct=body.markup_pct,
        contingency_pct=body.contingency_pct,
        is_visible=body.is_visible,
        is_bundle_parent=False,
    )
    db.add(sub)

    # Clear parent override
    parent.is_bundle_override_active = False
    parent.bundle_override_price = None

    db.commit()
    db.refresh(sub)
    scenario = db.query(Scenario).filter(Scenario.id == sub.scenario_id).first()
    sheet = db.query(CostingSheet).filter(CostingSheet.id == scenario.costing_sheet_id).first()
    sub = db.query(LineItem).options(selectinload(LineItem.sub_components)).filter(LineItem.id == sub.id).first()
    overrides = fetch_sheet_overrides(sheet.id, db)
    return await _inject_pricing(sub, overrides)


@router.patch("/line-items/{line_item_id}/bundle-override", response_model=LineItemRead)
async def set_bundle_override(
    line_item_id: str,
    body: BundleOverridePatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Set or clear the bundle manual override price.
             Send bundle_override_price=null to clear the override.
    Inputs: line_item_id (str UUID, must be bundle parent), BundleOverridePatch
    Outputs: LineItemRead
    Owner: [Claude]
    """
    item = _owned_line_item(line_item_id, current_user.id, db)
    if not item.is_bundle_parent:
        raise HTTPException(status_code=400, detail="Line item is not a bundle parent.")

    if body.bundle_override_price is not None:
        item.bundle_override_price = body.bundle_override_price
        item.is_bundle_override_active = True
    else:
        item.bundle_override_price = None
        item.is_bundle_override_active = False

    db.commit()
    db.refresh(item)
    item = db.query(LineItem).options(
        selectinload(LineItem.sub_components).selectinload(LineItem.sub_components)
    ).filter(LineItem.id == item.id).first()
    scenario = db.query(Scenario).filter(Scenario.id == item.scenario_id).first()
    sheet = db.query