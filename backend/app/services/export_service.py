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
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from fastapi import HTTPException
from supabase import create_client, Client

try:
    from weasyprint import HTML as _WeasyHTML
    _WEASYPRINT_AVAILABLE = True
except (OSError, ImportError):
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


# ---------------------------------------------------------------------------
# DOCX rendering helpers
# ---------------------------------------------------------------------------

def _fetch_image(url: str) -> io.BytesIO | None:
    """
    Purpose: Fetch an image from a URL and return as BytesIO for embedding in DOCX.
    Inputs: url (str)
    Outputs: io.BytesIO | None — None on any error
    Owner: [Claude]
    """
    try:
        resp = httpx.get(url, timeout=10.0)
        resp.raise_for_status()
        buf = io.BytesIO(resp.content)
        buf.seek(0)
        return buf
    except Exception:
        return None


def _set_cell_bg(cell, hex_color: str) -> None:
    """
    Purpose: Set a table cell background colour via direct XML manipulation.
             python-docx does not expose this through its public API.
    Inputs: cell (docx.table._Cell), hex_color (str, e.g. 'D9D9D9')
    Outputs: none — mutates cell XML in place
    Owner: [Claude]
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _bold_cell(cell, text: str, align: str = "left") -> None:
    """
    Purpose: Write bold text into a table cell with optional alignment.
    Inputs: cell, text (str), align ('left'|'right'|'center')
    Outputs: none — mutates cell in place
    Owner: [Claude]
    """
    cell.text = ""
    para = cell.paragraphs[0]
    run = para.add_run(text)
    run.bold = True
    if align == "right":
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif align == "center":
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER


def _right_cell(cell, text: str) -> None:
    """
    Purpose: Write right-aligned text into a table cell.
    Inputs: cell, text (str)
    Outputs: none — mutates cell in place
    Owner: [Claude]
    """
    cell.text = ""
    para = cell.paragraphs[0]
    para.add_run(text)
    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def _remove_table_borders(table) -> None:
    """
    Purpose: Remove all borders from a table (invisible table for layout only).
    Inputs: table (docx.table.Table)
    Outputs: none — mutates table XML in place
    Owner: [Claude]
    """
    tbl = table._tbl
    tblPr = tbl.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    tblBorders = OxmlElement("w:tblBorders")
    for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = OxmlElement(f"w:{border_name}")
        border.set(qn("w:val"), "none")
        border.set(qn("w:sz"), "0")
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "auto")
        tblBorders.append(border)
    tblPr.append(tblBorders)


def _fmt(val) -> str:
    """
    Purpose: Format a numeric value as a comma-separated 2dp string, or '—' if zero/None.
    Inputs: val (str | Decimal | None)
    Outputs: str
    Owner: [Claude]
    """
    try:
        n = Decimal(str(val))
        return f"{n:,.2f}"
    except Exception:
        return "—"


# ---------------------------------------------------------------------------
# Main DOCX renderer
# ---------------------------------------------------------------------------

SECTIONS_ORDER = ["Hardware", "Software", "Professional Fees", "Maintenance"]

DARK_GREY = "404040"   # Section header row text (white bg + dark font)
LIGHT_GREY = "F2F2F2"  # Section header row background
TOTAL_GREY = "D9D9D9"  # Grand total row background


def render_docx(context: dict) -> bytes:
    """
    Purpose: Render the quote as a branded NEXTAN DOCX quotation.
             Matches the sample quotation format:
             logo → client header → title → line items by section → terms table → T&C → sign-off.
    Inputs: context (dict) — output of _build_export_context in exports.py
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
    company_name = context.get("company_name", "NEXTAN Pte Ltd")
    company_contact_name = context.get("company_contact_name", "")
    company_contact_email = context.get("company_contact_email", "")
    company_contact_phone = context.get("company_contact_phone", "")

    doc = Document()

    # Page margins — standard A4 margins
    for section in doc.sections:
        section.top_margin = Inches(0.9)
        section.bottom_margin = Inches(0.9)
        section.left_margin = Inches(1.1)
        section.right_margin = Inches(1.1)

    # ------------------------------------------------------------------ #
    # 1. LOGO
    # ------------------------------------------------------------------ #
    if logo_url:
        logo_bytes = _fetch_image(logo_url)
        if logo_bytes:
            p = doc.add_paragraph()
            run = p.add_run()
            run.add_picture(logo_bytes, width=Inches(2.0))

    doc.add_paragraph()  # vertical spacer

    # ------------------------------------------------------------------ #
    # 2. CLIENT HEADER TABLE
    # Layout (5 cols):
    #   Row 0: Date | : | <date value> | Ref No.: | <ref value>
    #   Row 1: To   | : | <client name + address — merged cols 2-4>
    #   Row 2: Attn.| : | <contact name — merged cols 2-4>
    #   Row 3: Email| : | <contact email — merged cols 2-4>
    # ------------------------------------------------------------------ #
    hdr_table = doc.add_table(rows=4, cols=5)
    _remove_table_borders(hdr_table)

    # Col widths: label=0.7", colon=0.15", value=2.5", label2=0.85", value2=1.5"
    col_widths_hdr = [Inches(0.7), Inches(0.15), Inches(2.5), Inches(0.85), Inches(1.5)]
    for i, w in enumerate(col_widths_hdr):
        for row in hdr_table.rows:
            row.cells[i].width = w

    # Row 0: Date + Ref No.
    hdr_table.cell(0, 0).text = "Date"
    hdr_table.cell(0, 1).text = ":"
    hdr_table.cell(0, 2).text = sheet.get("date") or ""
    hdr_table.cell(0, 3).text = "Ref No.:"
    hdr_table.cell(0, 4).text = sheet.get("ref_number") or ""

    # Row 1: To (merge cols 2-4)
    hdr_table.cell(1, 0).text = "To"
    hdr_table.cell(1, 1).text = ":"
    merged_to = hdr_table.cell(1, 2).merge(hdr_table.cell(1, 4))
    merged_to.text = sheet.get("client_name") or ""

    # Row 2: Attn (merge cols 2-4)
    hdr_table.cell(2, 0).text = "Attn."
    hdr_table.cell(2, 1).text = ":"
    merged_attn = hdr_table.cell(2, 2).merge(hdr_table.cell(2, 4))
    merged_attn.text = sheet.get("contact_name") or ""

    # Row 3: Email (merge cols 2-4)
    hdr_table.cell(3, 0).text = "Email"
    hdr_table.cell(3, 1).text = ":"
    merged_email = hdr_table.cell(3, 2).merge(hdr_table.cell(3, 4))
    merged_email.text = sheet.get("contact_email") or ""

    doc.add_paragraph()  # spacer

    # ------------------------------------------------------------------ #
    # 3. QUOTE TITLE
    # ------------------------------------------------------------------ #
    title_para = doc.add_paragraph()
    title_run = title_para.add_run(f"Quotation: {sheet.get('quote_title') or ''}")
    title_run.bold = True
    title_run.font.size = Pt(12)

    # ------------------------------------------------------------------ #
    # 4. GENERAL NOTES (asterisk footnotes shown below title)
    # ------------------------------------------------------------------ #
    if sheet.get("general_notes"):
        for line in sheet["general_notes"].split("\n"):
            line = line.strip()
            if line:
                n_para = doc.add_paragraph()
                n_run = n_para.add_run(line)
                n_run.font.size = Pt(9)
                n_run.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

    doc.add_paragraph()  # spacer

    # ------------------------------------------------------------------ #
    # 5. LINE ITEMS TABLE
    # Columns: No. | Description | Qty | Unit Price (S$) | Total Price (S$)
    # ------------------------------------------------------------------ #

    # Group visible top-level items by section
    by_section: dict[str, list[dict]] = {s: [] for s in SECTIONS_ORDER}
    for item in line_items:
        if not item.get("is_visible", True):
            continue
        if item.get("parent_line_item_id"):
            continue
        sec = item.get("section", "Hardware")
        if sec in by_section:
            by_section[sec].append(item)
        else:
            by_section.setdefault(sec, []).append(item)

    # Sort each section by display_order
    for sec in by_section:
        by_section[sec].sort(key=lambda x: x.get("display_order", 0))

    # Build table
    items_table = doc.add_table(rows=1, cols=5)
    items_table.style = "Table Grid"

    # Column widths: No=0.4", Desc=3.2", Qty=0.5", UnitPrice=1.1", Total=1.1"
    col_widths_items = [Inches(0.4), Inches(3.2), Inches(0.5), Inches(1.1), Inches(1.1)]
    for i, w in enumerate(col_widths_items):
        items_table.rows[0].cells[i].width = w

    # Header row
    col_headers = ["No.", "Description", "Qty", "Unit Price\n(S$)", "Total Price\n(S$)"]
    for i, h in enumerate(col_headers):
        cell = items_table.rows[0].cells[i]
        _set_cell_bg(cell, "D9D9D9")
        cell.text = ""
        para = cell.paragraphs[0]
        run = para.add_run(h)
        run.bold = True
        if i >= 2:
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    item_no = 1
    for sec in SECTIONS_ORDER:
        items = by_section.get(sec, [])
        if not items:
            continue

        # Section header row (merged across all 5 cols)
        sec_row = items_table.add_row()
        merged_sec = sec_row.cells[0].merge(sec_row.cells[4])
        _set_cell_bg(merged_sec, LIGHT_GREY)
        para = merged_sec.paragraphs[0]
        run = para.add_run(sec)
        run.bold = True
        run.font.size = Pt(10)

        sec_total = Decimal("0")

        for item in items:
            computed = item.get("computed", {})
            line_total_str = computed.get("line_total_sgd") or "0"
            line_total = Decimal(line_total_str)
            sec_total += line_total

            item_row = items_table.add_row()
            cells = item_row.cells

            # No.
            cells[0].text = str(item_no)

            # Description (include sub_specs as bullet points)
            desc_text = item.get("description", "")
            if item.get("sub_specs"):
                specs = item["sub_specs"]
                if isinstance(specs, list):
                    desc_text += "\n" + "\n".join(f"  • {s}" for s in specs)
            cells[1].text = desc_text

            # Qty
            cells[2].text = str(item.get("qty", 1))
            cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

            # Unit Price (SGD)
            selling_rate = computed.get("selling_rate_sgd")
            _right_cell(cells[3], _fmt(selling_rate) if selling_rate else "—")

            # Total Price (SGD)
            _right_cell(cells[4], _fmt(line_total) if line_total else "—")

            item_no += 1

    # ---- Totals rows ----
    subtotal = Decimal(str(totals.get("subtotal_sgd", "0")))
    discount = Decimal(str(totals.get("discount_amount_sgd", "0")))
    gst_amount = Decimal(str(totals.get("gst_amount_sgd", "0")))
    grand_total = Decimal(str(totals.get("grand_total_sgd", "0")))

    def _add_total_row(label: str, value: str, bold: bool = False, bg: str | None = None) -> None:
        """Purpose: Add a labelled total row to the line items table. Owner: [Claude]"""
        row = items_table.add_row()
        merged = row.cells[0].merge(row.cells[3])
        if bg:
            _set_cell_bg(merged, bg)
            _set_cell_bg(row.cells[4], bg)
        if bold:
            _bold_cell(merged, label, align="right")
            _bold_cell(row.cells[4], value, align="right")
        else:
            merged.text = ""
            merged.paragraphs[0].add_run(label)
            merged.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
            _right_cell(row.cells[4], value)

    _add_total_row("Subtotal (SGD)", _fmt(subtotal))

    if discount > 0:
        _add_total_row("Discount (SGD)", f"- {_fmt(discount)}")

    if show_gst:
        _add_total_row("GST (9%)", _fmt(gst_amount))

    _add_total_row("TOTAL (SGD)", _fmt(grand_total), bold=True, bg=TOTAL_GREY)

    doc.add_paragraph()  # spacer

    # ------------------------------------------------------------------ #
    # 6. TERMS TABLE
    # 3 cols: Label | : | Value — borderless layout
    # ------------------------------------------------------------------ #
    validity_text = f"Quotation price valid for {sheet.get('quotation_validity_days', 90)} days from date of issue"
    notes_text = "\n".join(notes_exclusions) if notes_exclusions else ""

    terms_rows = [
        ("Payment Term", sheet.get("payment_term") or "To be advised"),
        ("Quotation Validity", validity_text),
        ("Lead Time", sheet.get("lead_time") or "30 working days"),
        ("Local Tax", sheet.get("local_tax") or "Prices quoted in SGD are subject to prevailing Singapore GST"),
        ("Warranty", sheet.get("warranty") or "12 months standard against manufacturing defects"),
    ]
    if notes_text:
        terms_rows.append(("Note(s)", notes_text))

    terms_table = doc.add_table(rows=len(terms_rows), cols=3)
    _remove_table_borders(terms_table)

    for i, (label, value) in enumerate(terms_rows):
        row = terms_table.rows[i]
        row.cells[0].width = Inches(1.5)
        row.cells[1].width = Inches(0.2)
        row.cells[2].width = Inches(4.6)
        lbl_para = row.cells[0].paragraphs[0]
        lbl_run = lbl_para.add_run(label)
        lbl_run.bold = True
        lbl_run.font.size = Pt(10)
        row.cells[1].text = ":"
        row.cells[2].text = value

    doc.add_paragraph()  # spacer

    # ------------------------------------------------------------------ #
    # 7. T&C SECTION
    # ------------------------------------------------------------------ #
    tnc_heading = doc.add_paragraph()
    tnc_run = tnc_heading.add_run("Terms & Conditions:")
    tnc_run.bold = True
    tnc_run.font.size = Pt(10)

    warranty_heading = doc.add_paragraph()
    warranty_run = warranty_heading.add_run("Warranty Terms:")
    warranty_run.bold = True
    warranty_run.font.size = Pt(10)

    doc.add_paragraph(
        sheet.get("warranty") or "Standard 12 month warranty against manufacturing defects."
    )

    excl_heading = doc.add_paragraph()
    excl_run = excl_heading.add_run("Exclusions from Warranty:")
    excl_run.bold = True
    excl_run.font.size = Pt(10)

    doc.add_paragraph(
        "NEXTAN assumes no liability as a consequence of following circumstances, "
        "under which will be automatically excluded for warranty:"
    )

    for excl in warranty_exclusions:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(excl)

    # Additional T&C from global + per-sheet additions
    all_tnc = global_tnc + sheet_tnc
    if all_tnc:
        for item in all_tnc:
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(item)

    doc.add_paragraph()  # spacer

    # ------------------------------------------------------------------ #
    # 8. CLOSING PARAGRAPH
    # ------------------------------------------------------------------ #
    closing = doc.add_paragraph(
        "We trust that the above price is acceptable to you and look forward to receiving "
        "your favourable reply soon. Should you have any further queries, please do not "
        "hesitate to contact us."
    )
    closing.runs[0].font.size = Pt(10)

    doc.add_paragraph()  # spacer

    # ------------------------------------------------------------------ #
    # 9. SIGNATURE + SIGN-OFF TABLE
    # ------------------------------------------------------------------ #
    if signature_url:
        sig_bytes = _fetch_image(signature_url)
        if sig_bytes:
            p = doc.add_paragraph()
            p.add_run().add_picture(sig_bytes, width=Inches(1.5))

    # Sign-off table: 2 cols (content | blank — matches sample)
    signoff_rows = ["Yours faithfully"]
    if company_contact_name:
        signoff_rows.append(company_contact_name)
    if company_contact_email:
        signoff_rows.append(f"Email\t: {company_contact_email}")
    if company_contact_phone:
        signoff_rows.append(f"Phone\t: {company_contact_phone}")

    if signoff_rows:
        signoff_table = doc.add_table(rows=len(signoff_rows), cols=2)
        _remove_table_borders(signoff_table)
        for i, text in enumerate(signoff_rows):
            signoff_table.rows[i].cells[0].text = text

    # ------------------------------------------------------------------ #
    # Save to bytes
    # ------------------------------------------------------------------ #
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

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
