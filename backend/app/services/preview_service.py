"""
Purpose: HTML quote preview generation. Shared Jinja2 template used by both
         the preview endpoint (raw HTML) and the PDF export (WeasyPrint).
Owner: [Claude]
"""
from typing import Any

from jinja2 import Environment, BaseLoader

from app.constants import NEXTAN_WARRANTY_EXCLUSIONS

# Kept inline for v1 to avoid template file deployment concerns.

_QUOTE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Times New Roman', Times, serif;
  font-size: 12pt;
  color: #000;
  background: #e0e0e0;
}
.page {
  width: 794px;
  min-height: 1123px;
  margin: 20px auto;
  background: #fff;
  padding: 72px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}
.header-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
.header-table td { vertical-align: top; padding: 0; border: none; }
.logo-cell { width: 60%; }
.logo-cell img { max-height: 60px; max-width: 280px; }
.ref-cell { width: 40%; text-align: right; font-size: 10pt; line-height: 1.7; }
.client-block { margin-bottom: 16px; font-size: 11pt; line-height: 1.7; }
.quote-title { font-size: 13pt; font-weight: bold; margin-bottom: 8px; }
.salutation { margin-bottom: 16px; font-size: 11pt; line-height: 1.7; }
.items-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 10pt; }
.items-table th { border: 1px solid #000; padding: 4px 6px; text-align: center; font-weight: bold; background: #fff; }
.items-table td { border: 1px solid #000; padding: 4px 6px; vertical-align: top; }
.items-table .section-row td { background: #d0d0d0; font-weight: bold; text-align: left; border: 1px solid #000; }
.items-table .bundle-sub td { padding-left: 24px; color: #333; }
.num-col { text-align: center; width: 5%; }
.desc-col { width: 42%; }
.qty-col { text-align: center; width: 8%; }
.unit-col { text-align: center; width: 10%; }
.price-col { text-align: right; width: 17.5%; }
.total-col { text-align: right; width: 17.5%; }
.totals-table { width: 55%; margin-left: auto; border-collapse: collapse; font-size: 10pt; margin-bottom: 24px; }
.totals-table td { padding: 3px 6px; border: none; }
.total-label { text-align: left; }
.total-value { text-align: right; }
.grand-row td { font-weight: bold; border-top: 1.5px solid #000; padding-top: 5px; }
.tnc-section { margin-top: 24px; font-size: 10pt; line-height: 1.6; }
.tnc-section h3 { font-size: 11pt; font-weight: bold; margin-bottom: 10px; }
.tnc-section p { margin-bottom: 6px; }
.tnc-section ul { margin: 4px 0 10px 20px; }
.tnc-section ul li { margin-bottom: 2px; }
.signature-block { margin-top: 40px; text-align: right; }
.signature-block img { max-height: 60px; }
@media print {
  body { background: #fff; }
  .page { width: 100%; min-height: unset; margin: 0; padding: 0; box-shadow: none; }
  @page { size: A4; margin: 1in; }
}
</style>
</head>
<body>
<div class="page">

<table class="header-table">
  <tr>
    <td class="logo-cell">
      {% if logo_url %}<img src="{{ logo_url }}" alt="NEXTAN Logo">{% else %}<strong style="font-size:16pt">NEXTAN</strong>{% endif %}
    </td>
    <td class="ref-cell">
      <strong>QUOTATION</strong><br>
      Ref: {{ sheet.ref_number }}<br>
      Date: {{ sheet.date }}<br>
      Validity: {{ sheet.quotation_validity_days }} days
    </td>
  </tr>
</table>

<div class="client-block">
  <strong>To:</strong> {{ sheet.client_name }}<br>
  {% if sheet.contact_name %}<strong>Attn:</strong> {{ sheet.contact_name }}<br>{% endif %}
  {% if sheet.contact_email %}{{ sheet.contact_email }}<br>{% endif %}
</div>

<div class="quote-title">{{ sheet.quote_title }}</div>

<div class="salutation">
  Dear {% if sheet.contact_name %}{{ sheet.contact_name }}{% else %}Sir/Madam{% endif %},<br>
  We are pleased to submit the following quotation for your consideration.
</div>

{% set ns = namespace(current_section='', item_no=1) %}
<table class="items-table">
  <thead>
    <tr>
      <th class="num-col">No.</th>
      <th class="desc-col">Description</th>
      <th class="qty-col">Qty</th>
      <th class="unit-col">Unit</th>
      <th class="price-col">Unit Price (SGD)</th>
      <th class="total-col">Total (SGD)</th>
    </tr>
  </thead>
  <tbody>
  {% for item in line_items %}
  {% if item.is_visible %}
    {% if item.section != ns.current_section %}
      {% set ns.current_section = item.section %}
      <tr class="section-row"><td colspan="6">{{ item.section }}</td></tr>
    {% endif %}
    <tr>
      <td class="num-col">{{ ns.item_no }}{% set ns.item_no = ns.item_no + 1 %}</td>
      <td class="desc-col">
        {{ item.description }}
        {% if item.sub_specs %}
        <ul style="margin: 3px 0 0 16px; padding: 0;">{% for s in item.sub_specs %}<li>{{ s }}</li>{% endfor %}</ul>
        {% endif %}
      </td>
      <td class="qty-col">{{ item.qty }}</td>
      <td class="unit-col">{{ item.unit }}</td>
      <td class="price-col">{{ item.computed.selling_rate_sgd | format_decimal }}</td>
      <td class="total-col">{{ item.computed.line_total_sgd | format_decimal }}</td>
    </tr>
    {% if item.is_bundle_parent and not item.is_bundle_override_active %}
      {% for sub in item.sub_components %}
      {% if sub.is_visible %}
      <tr class="bundle-sub">
        <td class="num-col"></td>
        <td class="desc-col">
          &nbsp;&nbsp;- {{ sub.description }}
          {% if sub.sub_specs %}
          <ul style="margin: 3px 0 0 16px; padding: 0;">{% for s in sub.sub_specs %}<li>{{ s }}</li>{% endfor %}</ul>
          {% endif %}
        </td>
        <td class="qty-col">{{ sub.qty }}</td>
        <td class="unit-col">{{ sub.unit }}</td>
        <td class="price-col"></td>
        <td class="total-col"></td>
      </tr>
      {% endif %}
      {% endfor %}
    {% endif %}
  {% endif %}
  {% endfor %}
  </tbody>
</table>

<table class="totals-table">
  <tr>
    <td class="total-label">Subtotal</td>
    <td class="total-value">SGD {{ totals.subtotal_sgd | format_decimal }}</td>
  </tr>
  {% if totals.discount_amount_sgd | float > 0 %}
  <tr>
    <td class="total-label">Discount</td>
    <td class="total-value">- SGD {{ totals.discount_amount_sgd | format_decimal }}</td>
  </tr>
  {% endif %}
  {% if show_gst %}
  <tr>
    <td class="total-label">GST (9%)</td>
    <td class="total-value">SGD {{ totals.gst_amount_sgd | format_decimal }}</td>
  </tr>
  {% endif %}
  <tr class="grand-row">
    <td class="total-label"><strong>TOTAL</strong></td>
    <td class="total-value"><strong>SGD {{ totals.grand_total_sgd | format_decimal }}</strong></td>
  </tr>
</table>

<div class="tnc-section">
  <h3>Terms &amp; Conditions</h3>
  <p><strong>Payment:</strong> {{ sheet.payment_term or 'To be advised' }}</p>
  <p><strong>Lead Time:</strong> {{ sheet.lead_time or '30 working days' }}</p>
  <p><strong>Warranty:</strong> {{ sheet.warranty or '12 months standard' }}</p>
  {% if sheet.local_tax %}<p><strong>Tax:</strong> {{ sheet.local_tax }}</p>{% endif %}

  <p><strong>Warranty Exclusions:</strong></p>
  <ul>{% for excl in warranty_exclusions %}<li>{{ excl }}</li>{% endfor %}</ul>

  {% if global_tnc %}
  <p><strong>General Terms:</strong></p>
  <ul>{% for t in global_tnc %}<li>{{ t }}</li>{% endfor %}</ul>
  {% endif %}

  {% if sheet_tnc %}
  <ul>{% for t in sheet_tnc %}<li>{{ t }}</li>{% endfor %}</ul>
  {% endif %}

  {% if notes_exclusions %}
  <p><strong>Notes &amp; Exclusions:</strong></p>
  <ul>{% for n in notes_exclusions %}<li>{{ n }}</li>{% endfor %}</ul>
  {% endif %}
</div>

{% if signature_url %}
<div class="signature-block">
  <img src="{{ signature_url }}" alt="Authorised Signature">
</div>
{% endif %}

</div>
</body>
</html>
"""

_env = Environment(loader=BaseLoader())
_env.filters["format_decimal"] = lambda v: f"{float(v):,.2f}" if v is not None else "0.00"


def render_html_preview(context: dict[str, Any]) -> str:
    """
    Purpose: Render the quote HTML preview from a snapshot context dict.
             The same context dict is used by export_service for PDF generation.
    Inputs: context (dict) -- keys: sheet, line_items, totals, show_gst,
            logo_url, signature_url, global_tnc, sheet_tnc,
            notes_exclusions, warranty_exclusions
    Outputs: str -- complete HTML string
    Owner: [Claude]
    """
    context.setdefault("warranty_exclusions", NEXTAN_WARRANTY_EXCLUSIONS)
    template = _env.from_string(_QUOTE_TEMPLATE)
    return template.render(**context)
