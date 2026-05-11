"""
Purpose: Pricing calculations — line item and scenario totals.
         Pure computation; no DB calls. Injected at router layer into response schemas.
Owner: [Claude]
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.constants import GST_RATE
from app.schemas.pricing import ComputedLineItemPricing, ScenarioTotals

_QUANTIZE_4 = Decimal("0.0001")
_QUANTIZE_2 = Decimal("0.01")


def compute_line_item_pricing(
    cost_rate: Decimal,
    qty: Decimal,
    markup_pct: Decimal,
    contingency_pct: Decimal,
    fx_rate: Decimal,
    is_bundle_parent: bool,
    is_bundle_override_active: bool,
    bundle_override_price: Optional[Decimal],
    sub_component_totals: Optional[list[Decimal]] = None,
) -> ComputedLineItemPricing:
    """
    Purpose: Compute cost_sgd, selling_rate_sgd, and line_total_sgd for a single line item.
             For bundle parents: uses override price if active, else sums sub-component totals.
    Inputs:
        cost_rate (Decimal) — stored cost per unit in cost_currency
        qty (Decimal) — quantity
        markup_pct (Decimal) — markup as decimal (0.10 = 10%)
        contingency_pct (Decimal) — contingency as decimal
        fx_rate (Decimal) — 1 cost_currency = X SGD
        is_bundle_parent (bool)
        is_bundle_override_active (bool)
        bundle_override_price (Optional[Decimal])
        sub_component_totals (Optional[list[Decimal]]) — line_total_sgd for each sub-component
    Outputs: ComputedLineItemPricing
    Owner: [Claude]
    """
    cost_sgd = (cost_rate * fx_rate).quantize(_QUANTIZE_4, rounding=ROUND_HALF_UP)
    selling_rate_sgd = (cost_sgd * (1 + markup_pct + contingency_pct)).quantize(
        _QUANTIZE_4, rounding=ROUND_HALF_UP
    )

    if is_bundle_parent:
        if is_bundle_override_active and bundle_override_price is not None:
            line_total_sgd = Decimal(str(bundle_override_price)).quantize(
                _QUANTIZE_2, rounding=ROUND_HALF_UP
            )
        elif sub_component_totals:
            line_total_sgd = sum(sub_component_totals).quantize(
                _QUANTIZE_2, rounding=ROUND_HALF_UP
            )
        else:
            line_total_sgd = Decimal("0")
    else:
        line_total_sgd = (selling_rate_sgd * qty).quantize(_QUANTIZE_2, rounding=ROUND_HALF_UP)

    return ComputedLineItemPricing(
        cost_sgd=cost_sgd,
        selling_rate_sgd=selling_rate_sgd,
        line_total_sgd=line_total_sgd,
    )


def compute_item_from_orm(
    item,
    fx_rate: Decimal,
    sub_component_totals: Optional[list[Decimal]] = None,
) -> ComputedLineItemPricing:
    """
    Purpose: Shared computation kernel — converts a LineItem ORM object's fields into
             ComputedLineItemPricing. Used by both the line-item API router (_inject_pricing)
             and the export/preview router (_build_export_context / _process_item) to ensure
             pricing logic is defined in one place only.
    Inputs:
        item — LineItem ORM object (any object with cost_rate, qty, markup_pct,
               contingency_pct, is_bundle_parent, is_bundle_override_active, bundle_override_price)
        fx_rate (Decimal) — pre-resolved rate (1 item.cost_currency = X SGD)
        sub_component_totals (Optional[list[Decimal]]) — line_total_sgd for sub-components
    Outputs: ComputedLineItemPricing
    Owner: [Claude]
    """
    return compute_line_item_pricing(
        cost_rate=Decimal(str(item.cost_rate)),
        qty=Decimal(str(item.qty)),
        markup_pct=Decimal(str(item.markup_pct)),
        contingency_pct=Decimal(str(item.contingency_pct)),
        fx_rate=fx_rate,
        is_bundle_parent=item.is_bundle_parent,
        is_bundle_override_active=item.is_bundle_override_active,
        bundle_override_price=Decimal(str(item.bundle_override_price)) if item.bundle_override_price else None,
        sub_component_totals=sub_component_totals,
    )


def compute_scenario_totals(
    line_totals: list[Decimal],
    discount_type: Optional[str],
    discount_value: Optional[Decimal],
    show_gst: bool,
) -> ScenarioTotals:
    """
    Purpose: Compute subtotal, discount, GST, and grand total for a scenario.
             Only sums is_visible=True top-level items (sub-components included via bundle total).
    Inputs:
        line_totals (list[Decimal]) — line_total_sgd for each visible top-level line item
        discount_type (Optional[str]) — 'percentage' | 'flat' | None
        discount_value (Optional[Decimal])
        show_gst (bool)
    Outputs: ScenarioTotals
    Owner: [Claude]
    """
    subtotal = sum(line_totals, Decimal("0")).quantize(_QUANTIZE_2, rounding=ROUND_HALF_UP)

    if discount_type == "percentage" and discount_value is not None:
        discount_amount = (subtotal * discount_value).quantize(_QUANTIZE_2, rounding=ROUND_HALF_UP)
    elif discount_type == "flat" and discount_value is not None:
        discount_amount = Decimal(str(discount_value)).quantize(_QUANTIZE_2, rounding=ROUND_HALF_UP)
    else:
        discount_amount = Decimal("0")

    total_before_gst = (subtotal - discount_amount).quantize(_QUANTIZE_2, rounding=ROUND_HALF_UP)

    gst_amount = (
        (total_before_gst * Decimal(str(GST_RATE))).quantize(_QUANTIZE_2, rounding=ROUND_HALF_UP)
        if show_gst
        else Decimal("0")
    )
    grand_total = (total_before_gst + gst_amount).quantize(_QUANTIZE_2, rounding=ROUND_HALF_UP)

    return ScenarioTotals(
        subtotal_sgd=subtotal,
        discount_amount_sgd=discount_amount,
        total_before_gst_sgd=total_before_gst,
        gst_amount_sgd=gst_amount,
        grand_total_sgd=grand_total,
    )
