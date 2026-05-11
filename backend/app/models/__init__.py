"""
Purpose: Import all models so Alembic and SQLAlchemy can discover them.
Owner: [Claude]
"""
from app.models.user import User
from app.models.ref_number_sequence import RefNumberSequence
from app.models.organisation import Organisation
from app.models.contact import Contact
from app.models.costing_sheet import CostingSheet
from app.models.scenario import Scenario
from app.models.line_item import LineItem
from app.models.fx_rate_override import FXRateOverride
from app.models.tnc_addition import CostingSheetTncAddition, GlobalTncAddition
from app.models.quote_export import QuoteExport
from app.models.product import Product
from app.models.scenario_template import ScenarioTemplate, TemplateLineItem
from app.models.global_setting import GlobalSetting

__all__ = [
    "User", "RefNumberSequence",
    "Organisation", "Contact",
    "CostingSheet", "Scenario", "LineItem",
    "FXRateOverride",
    "CostingSheetTncAddition", "GlobalTncAddition",
    "QuoteExport",
    "Product",
    "ScenarioTemplate", "TemplateLineItem",
    "GlobalSetting",
]
