"""
Purpose: Quote HTML preview endpoint. Returns raw HTML (text/html).
         Frontend fetches with auth header and injects via iframe srcdoc.
Owner: [Claude]
"""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.costing_sheet import CostingSheet
from app.models.user import User
from app.routers.exports import _build_export_context, _owned_scenario
from app.services.preview_service import render_html_preview

router = APIRouter(tags=["Preview"])


@router.get("/scenarios/{scenario_id}/preview", response_class=HTMLResponse)
async def preview_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Return a rendered HTML preview of the quote for on-screen display.
             Same data and template as PDF export. Raw text/html response.
             Frontend must fetch() with Authorization header and inject via iframe srcdoc.
    Inputs: scenario_id (str UUID)
    Outputs: HTML string (text/html)
    Owner: [Claude]
    """
    scenario = _owned_scenario(scenario_id, current_user.id, db)
    sheet = db.query(CostingSheet).filter(CostingSheet.id == scenario.costing_sheet_id).first()
    context = await _build_export_context(scenario, sheet, db)
    html = render_html_preview(context)
    return HTMLResponse(content=html)
