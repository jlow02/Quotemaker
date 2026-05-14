"""
Purpose: HTML quote preview generation. Shared Jinja2 template used by both
         the preview endpoint (raw HTML) and the PDF export (WeasyPrint).
Owner: [Claude]
"""
from typing import Any

from jinja2 import Environment, BaseLoader

from app.constants import NEXTAN_WARRANTY_EXCLUSIONS

# ── Inline Jinja2 template ──────────────────────────────────────────────────
# Kept inline for v1 to avoid template file deployment concerns.
# Move to templates/quote.html if customisation requirements grow.

_QUOTE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: Arial, sans-serif; font-size: 10pt; color: #222; margin: 0; padding: 20px; }
  .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
  .logo img { max-height: 60px; }
  .ref-block { text-align: right; font-size: 9pt; }
  h1 { font-size: 14pt; margin: 0 0 4px 0; }
  .client-block { margin-bottom: 16px; font-size: 9pt; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 9pt; }
  th { background: #1a1a2e; color: white; padding: 6px 8px; text-align: left; }
  td { padding: 5px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }
  tr:nth-child(even) { background: #f9f9f9; }
  .section-header td { background: #e8e8e8; font-weight: bold; }
  .bundle-sub td { padding-left: 20px; color: #555; }
  .totals-table { width: 40%; margin-left: auto; }
  .totals-table td { border: none; }
  .grand-total td { font-weight: bold; border-top: 2px solid #222; }
  .terms { font-size: 8pt; margin-top: 20px; }
  .terms h3 { font-size: 9pt; margin-bottom: 4px; }
  .signature-block { margin-top: 40px; display: flex; justify-content: flex-end; }
  .signature-block img { max-height: 50px; }
  ul.bullets { margin: 2px 0; padding-left: 16px; }
  ul.bullets li { margin-bottom: 1px; }
  .invisible { display: none; }
</style>
</head>
<body>

<div class="header">
  <div class="logo">
    {% if logo_url %}<img src="{{ logo_url }}" alt="NEXTAN Logo">{% else %}<strong>NEXTAN</strong>{% endif %}
  </div>
  <div class="ref-block">
    <strong>QUOTATION</strong><br>
    Ref: {{ sheet.ref_number }}<br>
    Date: {{ sheet.date }}<br>
    Validity: {{ sheet.quotation_validity_days }} days
  </div>
</div>

<div class="client-block">
  <strong>To:</strong> {{ sheet.client_name }}<br>
  {% if sheet.contact_name %}<strong>Attn:</strong> {{ sheet.contact_name }}<br>{% endif %}
  {% if sheet.contact_email %}{{ sheet.contact_email }}<br>{% endif %}
</div>

<h1>{{ sheet.quote_title }}</h1>
<p>Dear {% if sheet.contact_name %}{{ sheet.contact_name }}{% else %}Sir/Madam{% endif %},<br>
We are pleased to submit the following quotation for your consideration.</p>

{% set ns = namespace(current_section='', item_no=1) %}
<table>
  <thead>
    <tr>
      <th style="width:4%">No.</th>
      <th style="width:40%">Description</th>
      <th style="width:8%">Qty</th>
      <th style="width:8%">Unit</th>
      <th style="width:20%">Unit Price (SGD)</th>
      <th style="width:20%">Total (SGD)</th>
    </tr>
  </thead>
  <tbody>
  {% for item in line_items %}
  {% if item.is_visible %}
    {% if item.section != ns.current_section %}
      {% set ns.current_section = item.section %}
      <tr class="section-header"><td colspan="6">{{ item.section }}</td></tr>
    {% endif %}
    <tr>
      <td>{{ ns.item_no }}{% set ns.item_no = ns.item_no + 1 %}</td>
      <td>
        {{ item.description }}
        {% if item.sub_specs %}
        <ul class="bullets">{% for s in item.sub_specs %}<li>{{ s }}</li>{% endfor %}</ul>
        {% endif %}
      </td>
      <td>{{ item.qty }}</td>
      <td>{{ item.unit }}</td>
      <td>{{ item.computed.selling_rate_sgd | format_decimal }}</td>
      <td>{{ item.computed.line_total_sgd | format_decimal }}</td>
    </tr>
    {% if item.is_bundle_parent and not item.is_bundle_override_active %}
      {% for sub in item.sub_components %}
      {% if sub.is_visible %}
      <tr class="bundle-sub">
        <td></td>
        <td>
          &nbsp;&nbsp;• {{ sub.description }}
          {% if sub.sub_specs %}
          <ul class="bullets">{% for s in sub.sub_specs %}<li>{{ s }}</li>{% endfor %}</ul>
          {% endif %}
        </td>
        <td>{{ sub.qty }}</td>
        <td>{{ sub.unit }}</td>
        <td></td>
        <td></td>
      </tr>
      {% endif %}
      {% endfor %}
    {% endif %}
  {% endif %}
  {% endfor %}
  </tbody>
</table>

<table class="totals-table">
  <tr><td>Subtotal</td><td style="text-align:right">SGD {{ totals.subtotal_sgd | format_decimal }}</td></tr>
  {% if totals.discount_amount_sgd | float > 0 %}
  <tr><td>Discount</td><td style="text-align:right">- SGD {{ totals.discount_amount_sgd | format_decimal }}</td></tr>
  {% endif %}
  {% if show_gst %}
  <tr><td>GST (9%)</td><td style="text-align:right">SGD {{ totals.gst_amount_sgd | format_decimal }}</td></tr>
  {% endif %}
  <tr class="grand-total"><td><strong>Total</strong></td><td style="text-align:right"><strong>SGD {{ totals.grand_total_sgd | format_decimal }}</strong></td></tr>
</table>

<div class="terms">
  <h3>Terms &amp; Conditions</h3>
  <p><strong>Payment:</strong> {{ sheet.payment_term or 'To be advised' }}</p>
  <p><strong>Lead Time:</strong> {{ sheet.lead_time }}</p>
  <p><strong>Warranty:</strong> {{ sheet.warranty }}</p>
  {% if sheet.local_tax %}<p><strong>Tax:</strong> {{ sheet.local_tax }}</p>{% endif %}

  <p><strong>Warranty Exclusions:</strong></p>
  <ul class="bullets">
    {% for excl in warranty_exclusions %}<li>{{ excl }}</li>{% endfor %}
  </ul>

  {% if global_tnc %}
  <p><strong>General Terms:</strong></p>
  <ul class="bullets">{% for t in global_tnc %}<li>{{ t }}</li>{% endfor %}</ul>
  {% endif %}

  {% if sheet_tnc %}
  <ul class="bullets">{% for t in sheet_tnc %}<li>{{ t }}</li>{% endfor %}</ul>
  {% endif %}

  {% if notes_exclusions %}
  <p><strong>Notes &amp; Exclusions:</strong></p>
  <ul class="bullets">{% for n in notes_exclusions %}<li>{{ n }}</li>{% endfor %}</ul>
  {% endif %}
</div>

<div class="signature-block">
  {% if signature_url %}<img src="{{ signature_url }}" alt="Authorised Signature">{% endif %}
</div>

</body>
</html>
"""

_env = Environment(loader=BaseLoader())
_env.filters["format_decimal"] = lambda v: f"{float(v):,.2f}" if v is not None else "—"


def render_html_preview(context: dict[str, Any]) -> str:
    """
    Purpose: Render the quote HTML preview from a snapshot context dict.
             The same context dict is used by export_service for PDF generation.
    Inputs: context (dict) — keys: sheet, line_items, totals, show_gst,
            logo_url, signature_url, global_tnc, sheet_tnc,
            notes_exclusions, warranty_exclusions
    Outputs: str — complete HTML string
    Owner: [Claude]
    """
    context.setdefault("warranty_exclusions", NEXTAN_WARRANTY_EXCLUSIONS)
    template = _env.from_string(_QUOTE_TEMPLATE)
    return template.render(**context)
