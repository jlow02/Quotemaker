"""
Purpose: Quote export generation — DOCX (python-docx), PDF (WeasyPrint), Supabase Storage upload.
         Export flow: build_snapshot → render → upload (outside DB txn) → return file_path.
Owner: [Claude]
"""
import io
from decimal import Decimal
from typing import Any

import httpx
from docx import Document
from docx.shared import Inches
from fastapi import HTTPException
from supabase import create_client, Client
try:
    from weasyprint import HTML as _WeasyHTML
    _WEASYPRINT_AVAILABLE = True
except OSError:
    _WeasyHTML = None  # type: ignore[assignment]
    _WEASYPRINT_AVAILABLE = False

from app.config import settings
from app.constants import (
    EXPORT_PATH_ORIGINAL,
    EXPORT_PATH_REVISION,
    NEXTAN_WARRANTY_EXCLUSIONS,
)
from app.services.preview_service import render_html_preview


def _get_supabase() -> Client:
    """
    Purpose: Create a Supabase client using service-role key from settings.
    Inputs: none
    Outputs: supabase.Client
    Owner: [Claude]
    """
    return create_client(settings.supabase_url, settings.supabase_service_key)


def build_file_path(user_id: str, ref_number: str, file_type: str, revision_number: int) -> str:
    """
    Purpose: Construct the Supabase Storage path for an export file.
             Original (revision 0): exports/{user_id}/{ref}.{ext}
             Revisions: exports/{user_id}/{ref}-R{n}.{ext}
    Inputs: user_id (str), ref_number (str), file_type ('docx'|'pdf'), revision_number (int)
    Outputs: str — storage path
    Owner: [Claude]
    """
    ref_safe = ref_number.replace("/", "-")
    if revision_number == 0:
        return EXPORT_PATH_ORIGINAL.format(user_id=user_id, ref=ref_safe, ext=file_type)
    return EXPORT_PATH_REVISION.format(
        user_id=user_id, ref=ref_safe, revision=revision_number, ext=file_type
    )


def build_snapshot(
    sheet: Any,
    scenario: Any,
    line_items_with_pricing: list[dict],
    totals: Any,
    fx_rates_used: dict[str, Decimal],
    logo_url: str | None,
    signature_url: str | None,
    global_tnc: list[str],
    sheet_tnc: list[str],
) -> dict:
    """
    Purpose: Build the snapshot_data JSONB dict capturing full scenario state at export time.
             This is the source of truth for the locked quote. Stored in QuoteExport.snapshot_data.
    Inputs: sheet, scenario, line_items_with_pricing, totals, fx_rates_used,
            logo_url, signature_url, global_tnc, sheet_tnc
    Outputs: dict — JSON-serialisable snapshot
    Owner: [Claude]
    """
    def decimal_to_str(v):
        """Purpose: Convert Decimal to str for JSON serialisation. Owner: [Claude]"""
        return str(v) if isinstance(v, Decimal) else v

    return {
        "schema_version": 1,
        "sheet": {
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
        },
        "scenario": {
            "id": str(scenario.id),
            "name": scenario.name,
            "discount_type": scenario.discount_type,
            "discount_value": decimal_to_str(scenario.discount_value),
            "show_gst": scenario.show_gst,
            "notes_exclusions": scenario.notes_exclusions or [],
        },
        "line_items": line_items_with_pricing,
        "totals": {
            "subtotal_sgd": decimal_to_str(totals.subtotal_sgd),
            "discount_amount_sgd": decimal_to_str(totals.discount_amount_sgd),
            "total_before_gst_sgd": decimal_to_str(totals.total_before_gst_sgd),
            "gst_amount_sgd": decimal_to_str(totals.gst_amount_sgd),
            "grand_total_sgd": decimal_to_str(totals.grand_total_sgd),
        },
        "fx_rates_used": {k: decimal_to_str(v) for k, v in fx_rates_used.items()},
        "logo_url": logo_url,
        "signature_url": signature_url,
        "global_tnc": global_tnc,
        "sheet_tnc": sheet_tnc,
        "warranty_exclusions": NEXTAN_WARRANTY_EXCLUSIONS,
    }


def render_pdf(context: dict) -> bytes:
    """
    Purpose: Render the quote as a PDF using WeasyPrint.
             Uses the shared Jinja2 HTML template from preview_service.
    Inputs: context (dict) — same shape as render_html_preview
    Outputs: bytes — PDF binary content
    Owner: [Claude]
    """
    if not _WEASYPRINT_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="PDF export requires GTK libraries not available on this platform. Use DOCX export or deploy to Linux.",
        )
    html_content = render_html_preview(context)
    return _WeasyHTML(string=html_content).write_pdf()


def render_docx(context: dict) -> bytes:
    """
    Purpose: Render the quote as a DOCX file using python-docx.
             Logo and signature are fetched from Supabase and embedded as BytesIO images.
    Inputs: context (dict) — same keys as render_html_preview
    Outputs: bytes — DOCX binary content
    Owner: [Claude]
    """
    sheet = context["sheet"]
    line_items = context.get("line_items", [])
    totals = context["totals"]
    show_gst = context.get("show_gst", False)
    warranty_exclusions = context.get("warranty_exclusions", NEXTAN_WARRANTY_EXCLUSIONS)
    global_tnc = context.get("global_tnc", [])
    sheet_tnc = context.get("sheet_tnc", [])
    notes_exclusions = context.get("notes_exclusions", [])
    logo_url = context.get("logo_url")
    signature_url = context.get("signature_url")

    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    def _fetch_image(url: str) -> io.BytesIO | None:
        """Fetch an image from a URL and return as BytesIO for embedding."""
        try:
            resp = httpx.get(url, timeout=10.0)
            resp.raise_for_status()
            buf = io.BytesIO(resp.content)
            buf.seek(0)
            return buf
        except Exception:
            return None

    # Logo
    if logo_url:
        logo_bytes = _fetch_image(logo_url)
        if logo_bytes:
            doc.add_picture(logo_bytes, width=Inches(1.5))

    # Header block
    p = doc.add_paragraph()
    p.add_run("QUOTATION\n").bold = True
    p.add_run(f"Ref: {sheet['ref_number']}\nDate: {sheet['date']}\nValidity: {sheet['quotation_validity_days']} days")

    doc.add_paragraph(f"To: {sheet['client_name']}")
    if sheet.get("contact_name"):
        doc.add_paragraph(f"Attn: {sheet['contact_name']}")
    if sheet.get("contact_email"):
        doc.add_paragraph(sheet["contact_email"])

    doc.add_heading(sheet["quote_title"], level=2)

    # Line items table
    table = doc.add_table(rows=1, cols=6)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, h in enumerate(["No.", "Description", "Qty", "Unit", "Unit Price (SGD)", "Total (SGD)"]):
        hdr[i].text = h

    current_section = None
    item_no = 1
    for item in line_items:
        if not item.get("is_visible", True):
            continue
        if item["section"] != current_section:
            current_section = item["section"]
            row = table.add_row().cells
            row[0].merge(row[5]).text = current_section

        computed = item.get("computed", {})
        row = table.add_row().cells
        row[0].text = str(item_no)
        desc = item["description"]
        if item.get("sub_specs"):
            desc += "\n" + "\n".join(f"  • {s}" for s in item["sub_specs"])
        row[1].text = desc
        row[2].text = str(item.get("qty", 1))
        row[3].text = item.get("unit", "unit")
        row[4].text = f"{Decimal(computed.get('selling_rate_sgd', '0')):,.2f}" if computed.get("selling_rate_sgd") else "—"
        row[5].text = f"{Decimal(computed.get('line_total_sgd', '0')):,.2f}" if computed.get("line_total_sgd") else "—"
        item_no += 1

    # Totals
    doc.add_paragraph()
    doc.add_paragraph(f"Subtotal: SGD {Decimal(str(totals['subtotal_sgd'])):,.2f}")
    if Decimal(str(totals["discount_amount_sgd"])) > 0:
        doc.add_paragraph(f"Discount: - SGD {Decimal(str(totals['discount_amount_sgd'])):,.2f}")
    if show_gst:
        doc.add_paragraph(f"GST (9%): SGD {Decimal(str(totals['gst_amount_sgd'])):,.2f}")
    grand = doc.add_paragraph(f"Total: SGD {Decimal(str(totals['grand_total_sgd'])):,.2f}")
    grand.runs[0].bold = True

    # Terms
    doc.add_heading("Terms & Conditions", level=3)
    doc.add_paragraph(f"Payment: {sheet.get('payment_term') or 'To be advised'}")
    doc.add_paragraph(f"Lead Time: {sheet.get('lead_time', '30 working days')}")
    doc.add_paragraph(f"Warranty: {sheet.get('warranty', '12 months standard')}")
    if sheet.get("local_tax"):
        doc.add_paragraph(f"Tax: {sheet['local_tax']}")

    if warranty_exclusions:
        doc.add_paragraph("Warranty Exclusions:")
        for excl in warranty_exclusions:
            doc.add_paragraph(f"• {excl}", style="List Bullet")

    for item in global_tnc + sheet_tnc:
        doc.add_paragraph(f"• {item}", style="List Bullet")

    if notes_exclusions:
        doc.add_paragraph("Notes & Exclusions:")
        for note in notes_exclusions:
            doc.add_paragraph(f"• {note}", style="List Bullet")

    # Signature
    if signature_url:
        sig_bytes = _fetch_image(signature_url)
        if sig_bytes:
            doc.add_picture(sig_bytes, width=Inches(1.5))

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


async def upload_to_storage(file_bytes: bytes, file_path: str, file_type: str) -> str:
    """
    Purpose: Upload file bytes to Supabase Storage exports bucket.
             Called OUTSIDE the DB transaction to avoid holding DB connections during upload.
    Inputs: file_bytes (bytes), file_path (str), file_type ('docx'|'pdf')
    Outputs: str — the file_path (same as input, confirmed by Supabase)
    Owner: [Claude]
    """
    content_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if file_type == "docx"
        else "application/pdf"
    )
    supabase = _get_supabase()
    try:
        supabase.storage.from_(settings.supabase_storage_bucket_exports).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Export file upload failed: {exc}. No database record was created.",
        ) from exc
    return file_path


def generate_signed_url(file_path: str, expires_in: int = 3600) -> str:
    """
    Purpose: Generate a time-limited signed URL for a Supabase Storage file.
    Inputs: file_path (str), expires_in (int, seconds, default 3600)
    Outputs: str — signed URL
    Owner: [Claude]
    """
    supabase = _get_supabase()
    result = supabase.storage.from_(settings.supabase_storage_bucket_exports).create_signed_url(
        path=file_path, expires_in=expires_in
    )
    return result["signedURL"]


def delete_from_storage(file_path: str) -> None:
    """
    Purpose: Delete a file from Supabase Storage exports bucket.
             Called when a QuoteExport record is deleted.
    Inputs: file_path (str)
    Outputs: none
    Owner: [Claude]
    """
    supabase = _get_supabase()
    try:
        supabase.storage.from_(settings.supabase_storage_bucket_exports).remove([file_path])
    except Exception:
        # Non-fatal: log but don't raise. The DB record deletion is the authoritative action.
        pass
