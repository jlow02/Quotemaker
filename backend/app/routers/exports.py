"""
Purpose: Quote export endpoints — create DOCX/PDF, list, download (signed URL), delete.
         Export flow: snapshot → render → upload (outside DB txn) → INSERT record.
Owner: [Claude]
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.constants import NEXTAN_WARRANTY_EXCLUSIONS
from app.database import get_db
from app.dependencies import get_current_user
from app.models.costing_sheet import CostingSheet
from app.models.global_setting import GlobalSetting
from app.models.line_item import LineItem
from app.models.quote_export import QuoteExport
from app.models.scenario import Scenario
from app.models.tnc_addition import CostingSheetTncAddition, GlobalTncAddition
from app.models.user import User
from app.schemas.quote_export import ExportCreate, ExportDownloadResponse, ExportRead
from app.services.export_service import (
    build_file_path, build_snapshot, delete_from_storage,
    generate_signed_url, render_docx, render_pdf, upload_to_storage,
)
from app.services.fx_service import fetch_sheet_overrides, resolve_rate_batch
from app.services.pricing_service import compute_item_from_orm, compute_scenario_totals

router = APIRouter(tags=["Exports"])


def _owned_scenario(scenario_id: str, user_id, db: Session) -> Scenario:
    s = (
        db.query(Scenario)
        .join(CostingSheet)
        .filter(Scenario.id == scenario_id, CostingSheet.user_id == user_id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    return s


async def _build_export_context(scenario: Scenario, sheet: CostingSheet, db: Session) -> dict:
    """
    Purpose: Build the full rendering context for a quote export/preview.
             Computes all pricing, resolves FX rates, and gathers T&C/settings.
    Inputs: scenario (Scenario), sheet (CostingSheet), db (Session)
    Outputs: dict — rendering context for preview_service and export_service
    Owner: [Claude]
    """
    # Load line items with sub-components
    items = (
        db.query(LineItem)
        .options(selectinload(LineItem.sub_components).selectinload(LineItem.sub_components))
        .filter(LineItem.scenario_id == scenario.id, LineItem.parent_line_item_id.is_(None))
        .order_by(LineItem.section, LineItem.display_order)
        .all()
    )

    # Pre-fetch all FX overrides for this sheet in a single query —
    # eliminates N+1 DB queries when iterating over line items below.
    overrides = fetch_sheet_overrides(sheet.id, db)

    fx_rates_used: dict[str, Decimal] = {}
    line_items_rendered = []
    visible_totals: list[Decimal] = []

    async def _process_item(item: LineItem, is_sub: bool = False) -> dict:
        """
        Purpose: Recursively build the rendering context dict for one line item.
                 Uses pre-fetched overrides (no DB query per item) and the shared
                 compute_item_from_orm kernel (same pricing logic as the API layer).
        Inputs: item (LineItem), is_sub (bool)
        Outputs: dict — rendering context for Jinja2 / python-docx
        Owner: [Claude]
        """
        # resolve_rate_batch: O(1) dict lookup, falls back to cached live rate — no DB query
        fx_rate = await resolve_rate_batch(overrides, item.cost_currency)
        fx_rates_used[item.cost_currency] = fx_rate

        sub_rendered = [await _process_item(sub, is_sub=True) for sub in item.sub_components]
        sub_totals = [
            Decimal(s["computed"]["line_total_sgd"])
            for s in sub_rendered
            if s.get("is_visible") and s.get("computed", {}).get("line_total_sgd")
        ]

        # compute_item_from_orm: shared kernel — same logic as _inject_pricing in line_items.py
        computed = compute_item_from_orm(item, fx_rate, sub_totals if sub_totals else None)

        return {
            "id": str(item.id),
            "section": item.section,
            "display_order": item.display_order,
            "description": item.description,
            "sub_specs": item.sub_specs,
            "qty": str(item.qty),
            "unit": item.unit,
            "cost_rate": str(item.cost_rate),
            "cost_currency": item.cost_currency,
            "markup_pct": str(item.markup_pct),
            "contingency_pct": str(item.contingency_pct),
            "is_visible": item.is_visible,
            "is_bundle_parent": item.is_bundle_parent,
            "is_bundle_override_active": item.is_bundle_override_active,
            "bundle_override_price": str(item.bundle_override_price) if item.bundle_override_price else None,
            "sub_components": sub_rendered,
            "computed": {
                "cost_sgd": str(computed.cost_sgd),
                "selling_rate_sgd": str(computed.selling_rate_sgd),
                "line_total_sgd": str(computed.line_total_sgd),
            },
        }

    for item in items:
        rendered = await _process_item(item)
        line_items_rendered.append(rendered)
        if item.is_visible and rendered["computed"].get("line_total_sgd"):
            visible_totals.append(Decimal(rendered["computed"]["line_total_sgd"]))

    totals = compute_scenario_totals(
        line_totals=visible_totals,
        discount_type=scenario.discount_type,
        discount_value=Decimal(str(scenario.discount_value)) if scenario.discount_value else None,
        show_gst=scenario.show_gst,
    )

    # Global settings (logo, signature, company contact for sign-off)
    settings_rows = db.query(GlobalSetting).all()
    settings_map = {row.key: row.value for row in settings_rows}
    logo_url = settings_map.get("nextan_logo_url")
    signature_url = settings_map.get("signature_url")
    company_name = settings_map.get("company_name", "NEXTAN Pte Ltd")
    company_contact_name = settings_map.get("company_contact_name", "")
    company_contact_email = settings_map.get("company_contact_email", "")
    company_contact_phone = settings_map.get("company_contact_phone", "")

    # T&C
    global_tnc = [
        t.bullet_point for t in
        db.query(GlobalTncAddition).order_by(GlobalTncAddition.display_order).all()
    ]
    sheet_tnc = [
        t.bullet_point for t in
        db.query(CostingSheetTncAddition)
        .filter(CostingSheetTncAddition.costing_sheet_id == sheet.id)
        .order_by(CostingSheetTncAddition.display_order)
        .all()
    ]

    # Build sheet dict for template
    sheet_dict = {
        "id": str(sheet.id),
        "ref_number": sheet.ref_number,
        "date": str(sheet.date),
        "quote_title": sheet.quote_title,
        "client_name": sheet.client_name,
        "contact_name": sheet.contact_name,
        "contact_email": sheet.contact_email,
        "payment_term": sheet.payment_term,
        "quotation_validity_days": sheet.quotation_validity_days,
        "lead_time": sheet.lead_time,
        "local_tax": sheet.local_tax,
        "warranty": sheet.warranty,
        "general_notes": sheet.general_notes,
    }

    totals_dict = {
        "subtotal_sgd": str(totals.subtotal_sgd),
        "discount_amount_sgd": str(totals.discount_amount_sgd),
        "total_before_gst_sgd": str(totals.total_before_gst_sgd),
        "gst_amount_sgd": str(totals.gst_amount_sgd),
        "grand_total_sgd": str(totals.grand_total_sgd),
    }

    return {
        "sheet": sheet_dict,
        "line_items": line_items_rendered,
        "totals": totals_dict,
        "show_gst": scenario.show_gst,
        "notes_exclusions": scenario.notes_exclusions or [],
        "logo_url": logo_url,
        "signature_url": signature_url,
        "company_name": company_name,
        "company_contact_name": company_contact_name,
        "company_contact_email": company_contact_email,
        "company_contact_phone": company_contact_phone,
        "global_tnc": global_tnc,
        "sheet_tnc": sheet_tnc,
        "fx_rates_used": fx_rates_used,
        "warranty_exclusions": NEXTAN_WARRANTY_EXCLUSIONS,
    }


@router.post("/scenarios/{scenario_id}/exports", response_model=ExportRead, status_code=status.HTTP_201_CREATED)
async def create_export(
    scenario_id: str,
    body: ExportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Generate a quote export (DOCX or PDF). Steps:
             1. Compute snapshot_data and render file (outside DB transaction)
             2. Upload to Supabase Storage (outside DB transaction)
             3. INSERT QuoteExport record inside DB transaction (revision_number computed inside txn)
    Inputs: scenario_id (str UUID), ExportCreate (file_type)
    Outputs: ExportRead
    Owner: [Claude]
    """
    if body.file_type not in ("docx", "pdf"):
        raise HTTPException(status_code=400, detail="file_type must be 'docx' or 'pdf'.")

    scenario = _owned_scenario(scenario_id, current_user.id, db)
    sheet = db.query(CostingSheet).filter(CostingSheet.id == scenario.costing_sheet_id).first()

    # Step 1: Build context and snapshot (outside transaction)
    context = await _build_export_context(scenario, sheet, db)
    snapshot = build_snapshot(
        sheet=type("S", (), context["sheet"])() if False else _dict_to_obj(context["sheet"]),
        scenario=scenario,
        line_items_with_pricing=context["line_items"],
        totals=_dict_to_obj(context["totals"]),
        fx_rates_used=context["fx_rates_used"],
        logo_url=context["logo_url"],
        signature_url=context["signature_url"],
        global_tnc=context["global_tnc"],
        sheet_tnc=context["sheet_tnc"],
    )

    # Step 2: Render file (outside transaction)
    if body.file_type == "pdf":
        file_bytes = render_pdf(context)
    else:
        file_bytes = render_docx(context)

    # Step 3: Upload to Supabase (outside transaction — see sketch for rationale)
    # revision_number computed inside transaction below to prevent race conditions
    temp_path = f"exports/{current_user.id}/tmp_{scenario_id}.{body.file_type}"
    await upload_to_storage(file_bytes, temp_path, body.file_type)

    # Step 4-7: Open DB transaction, compute revision_number, insert record, rename path
    max_rev = db.query(func.max(QuoteExport.revision_number)).filter(
        QuoteExport.costing_sheet_id == sheet.id,
        QuoteExport.scenario_id == scenario.id,
        QuoteExport.file_type == body.file_type,
    ).scalar()
    revision_number = 0 if max_rev is None else max_rev + 1

    file_path = build_file_path(str(current_user.id), sheet.ref_number, body.file_type, revision_number)

    # Move temp file to final path in Supabase (upload final path, delete temp)
    await upload_to_storage(file_bytes, file_path, body.file_type)
    # Clean up temp (non-fatal)
    try:
        from app.services.export_service import delete_from_storage as _del
        _del(temp_path)
    except Exception:
        pass

    export_record = QuoteExport(
        costing_sheet_id=sheet.id,
        scenario_id=scenario.id,
        user_id=current_user.id,
        revision_number=revision_number,
        file_type=body.file_type,
        file_path=file_path,
        snapshot_data=snapshot,
    )
    db.add(export_record)
    db.commit()
    db.refresh(export_record)
    return export_record


def _dict_to_obj(d: dict):
    """Purpose: Convert a dict to a simple namespace object for attribute access. Owner: [Claude]"""
    class Obj:
        pass
    obj = Obj()
    for k, v in d.items():
        setattr(obj, k, v)
    return obj


@router.get("/costing-sheets/{sheet_id}/exports", response_model=list[ExportRead])
def list_sheet_exports(
    sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: List all exports for a costing sheet across all scenarios and file types.
    Inputs: sheet_id (str UUID)
    Outputs: list[ExportRead]
    Owner: [Claude]
    """
    sheet = db.query(CostingSheet).filter(
        CostingSheet.id == sheet_id, CostingSheet.user_id == current_user.id
    ).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Costing sheet not found.")
    return (
        db.query(QuoteExport)
        .filter(QuoteExport.costing_sheet_id == sheet_id)
        .order_by(QuoteExport.exported_at.desc())
        .all()
    )


@router.get("/scenarios/{scenario_id}/exports", response_model=list[ExportRead])
def list_scenario_exports(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: List exports for a specific scenario.
    Inputs: scenario_id (str UUID)
    Outputs: list[ExportRead]
    Owner: [Claude]
    """
    _owned_scenario(scenario_id, current_user.id, db)
    return (
        db.query(QuoteExport)
        .filter(QuoteExport.scenario_id == scenario_id)
        .order_by(QuoteExport.exported_at.desc())
        .all()
    )


@router.get("/exports/{export_id}/download", response_model=ExportDownloadResponse)
def download_export(
    export_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Return a signed Supabase Storage URL for downloading an export file.
    Inputs: export_id (str UUID)
    Outputs: ExportDownloadResponse (signed_url, expires_in_seconds, metadata)
    Owner: [Claude]
    """
    export = (
        db.query(QuoteExport)
        .filter(QuoteExport.id == export_id, QuoteExport.user_id == current_user.id)
        .first()
    )
    if not export:
        raise HTTPException(status_code=404, detail="Export not found.")
    signed_url = generate_signed_url(export.file_path, expires_in=3600)
    return ExportDownloadResponse(
        export_id=export.id,
        signed_url=signed_url,
        expires_in_seconds=3600,
        file_type=export.file_type,
        revision_number=export.revision_number,
    )


@router.delete("/exports/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_export(
    export_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Delete an export record and its Supabase Storage file.
             After deletion, sheet/scenario may become deletable if no exports remain.
    Inputs: export_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    export = (
        db.query(QuoteExport)
        .filter(QuoteExport.id == export_id, QuoteExport.user_id == current_user.id)
        .first()
    )
    if not export:
        raise HTTPException(status_code=404, detail="Export not found.")
    file_path = export.file_path
    db.delete(export)
    db.commit()
    delete_from_storage(file_path)
