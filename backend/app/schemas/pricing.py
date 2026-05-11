"""
Purpose: Computed pricing fields injected into LineItemRead at the router layer.
         These are never stored in the DB — always derived from stored fields + FX rates.
Owner: [Claude]
"""
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class ComputedLineItemPricing(BaseModel):
    """
    Purpose: Derived pricing values for a single line item.
             Injected by the router layer after calling pricing_service.compute_line_item_pricing.
    Inputs: N/A (computed, not from DB)
    Outputs: cost_sgd, selling_rate_sgd, line_total_sgd
    Owner: [Claude]
    """
    cost_sgd: Optional[Decimal] = None           # cost_rate converted to SGD
    selling_rate_sgd: Optional[Decimal] = None   # cost_sgd * (1 + markup_pct + contingency_pct)
    line_total_sgd: Optional[Decimal] = None     # selling_rate_sgd * qty (or bundle override)


class ScenarioTotals(BaseModel):
    """
    Purpose: Aggregated totals for a scenario.
             Computed from all visible line items, applying discount and optional GST.
    Inputs: N/A (computed)
    Outputs: subtotal_sgd, discount_amount_sgd, total_before_gst_sgd, gst_amount_sgd, grand_total_sgd
    Owner: [Claude]
    """
    subtotal_sgd: Decimal
    discount_amount_sgd: Decimal
    total_before_gst_sgd: Decimal
    gst_amount_sgd: Decimal
    grand_total_sgd: Decimal
