"""
Purpose: FastAPI application factory. Registers all routers, configures CORS and lifespan.
Owner: [Claude]
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    auth, users, organisations, contacts,
    costing_sheets, scenarios, line_items,
    fx_rates, tnc_additions, exports, preview,
    products, scenario_templates, settings as settings_router,
)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Purpose: Application lifespan handler. Runs startup/shutdown logic.
    Inputs: app (FastAPI)
    Outputs: none
    Owner: [Claude]
    """
    # Startup: nothing required — DB handled by Alembic migrations pre-deploy
    yield
    # Shutdown: nothing required — SQLAlchemy connection pool handles cleanup


def create_app() -> FastAPI:
    """
    Purpose: Create and configure the FastAPI application instance.
    Inputs: none
    Outputs: FastAPI app
    Owner: [Claude]
    """
    app = FastAPI(
        title="NEXTAN Costing & Quote Generator API",
        version="1.0.0",
        description="Internal costing sheets and client-facing branded quote exports.",
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ─────────────────────────────────────────────────────────────
    for router in [
        auth.router,
        users.router,
        organisations.router,
        contacts.router,
        costing_sheets.router,
        scenarios.router,
        line_items.router,
        fx_rates.router,
        tnc_additions.router,
        exports.router,
        preview.router,
        products.router,
        scenario_templates.router,
        settings_router.router,
    ]:
        app.include_router(router, prefix=API_PREFIX)

    return app


app = create_app()
