"""
Purpose: Integration tests for C-P4-01 — runs against live backend via HTTP.
         No app imports required — pure httpx against the running API.
Owner: [Claude]

Requirements:
    pip install pytest pytest-asyncio httpx
    Run: BASE_URL=https://quotemaker-y9wb.onrender.com pytest tests/test_integration.py -v
"""
import asyncio
import os
import time

import httpx
import pytest

pytestmark = pytest.mark.asyncio

BASE = os.environ.get("BASE_URL", "http://localhost:8000")
EMAIL = "jlow02@gmail.com"
PASSWORD = "nextan2026"


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _login(client: httpx.AsyncClient) -> dict:
    """
    Purpose: Log in and return auth headers.
    Inputs:  httpx.AsyncClient
    Outputs: dict with Authorization header
    Owner:   [Claude]
    """
    r = await client.post(f"{BASE}/api/v1/auth/login",
                          json={"username": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── C-P4-01 Test 1: FX override concurrent upsert ─────────────────────────────

async def test_fx_override_concurrent_upsert_no_500():
    """
    Purpose: Fire 10 concurrent POST /costing-sheets/{id}/fx-overrides for the same
             currency pair. All must return 2xx — no 500 UniqueViolation races.
             Proves the INSERT ... ON CONFLICT DO UPDATE is atomic.

    Before fix: concurrent inserts hit uq_fx_override constraint → 500 to ≥1 caller.
    After fix:  upsert handles all concurrent writes cleanly.

    Inputs:  Live backend at BASE_URL
    Outputs: All 10 concurrent requests return HTTP 200 or 201
    Owner:   [Claude]
    """
    async with httpx.AsyncClient(timeout=30) as client:
        headers = await _login(client)

        # Create a dedicated sheet for this test
        r = await client.post(f"{BASE}/api/v1/costing-sheets", headers=headers,
                              json={"quote_title": "FX Concurrency Test", "client_name": "Test"})
        assert r.status_code == 201, f"Create sheet failed: {r.text}"
        sheet_id = r.json()["id"]

        try:
            async def upsert(rate_str: str) -> httpx.Response:
                return await client.post(
                    f"{BASE}/api/v1/costing-sheets/{sheet_id}/fx-overrides",
                    headers=headers,
                    json={"base_currency": "USD", "override_rate": rate_str},
                )

            # 10 concurrent upserts for the same currency (USD → SGD), each with
            # a slightly different rate — last writer wins, but no 500s allowed.
            rates = [f"1.3{i}" for i in range(10)]
            results = await asyncio.gather(*[upsert(r) for r in rates])

            statuses = [resp.status_code for resp in results]
            errors_5xx = [resp.text for resp in results if resp.status_code >= 500]

            assert not errors_5xx, \
                f"Got 5xx in concurrent upsert — race condition not fixed: {errors_5xx}"
            assert all(s in (200, 201) for s in statuses), \
                f"Expected all 200/201, got: {statuses}"

        finally:
            await client.delete(f"{BASE}/api/v1/costing-sheets/{sheet_id}",
                                headers=headers, timeout=30)


# ── C-P4-01 Test 2: 200 line items under 2s ───────────────────────────────────

async def test_list_line_items_200_items_under_2s():
    """
    Purpose: Performance regression test — GET /scenarios/{id}/line-items with
             200 items must complete in <2s. Proves N+1 query elimination is intact.

    Before fix: ~200 separate DB queries → >10s for large scenarios.
    After fix:  1 selectinload query + 1 fx_overrides query → <500ms typical.

    Setup: items are bulk-inserted directly via Supabase REST API (single request)
    to keep total test runtime fast. The GET assertion targets the Quotemaker
    API endpoint — that is what is under test.

    Inputs:  Live backend at BASE_URL; Supabase credentials in env or defaults
    Outputs: Response time < 2.0s for 200 line items
    Owner:   [Claude]
    """
    import json as _json
    import uuid as _uuid
    from datetime import datetime, timezone

    ITEM_COUNT = 200
    SUPA_URL = os.environ.get("SUPABASE_URL", "https://cidmvdzlroqtweptarlf.supabase.co")
    SUPA_KEY = os.environ.get(
        "SUPABASE_SERVICE_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNpZG12ZHpscm9xd"
        "GVwdGFybGYiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNzc3NzI0"
        "NTI5LCJleHAiOjIwOTMzMDA1Mjl9.V4WtI0Rw-wkbOX4aAPs1hZALo5LNQItdmLqYi3qs_z0",
    )
    supa_h = {
        "apikey": SUPA_KEY,
        "Authorization": f"Bearer {SUPA_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        headers = await _login(client)

        # Create sheet + scenario via Quotemaker API
        r = await client.post(f"{BASE}/api/v1/costing-sheets", headers=headers,
                              json={"quote_title": "Perf Test 200 Items", "client_name": "Test"})
        assert r.status_code == 201, f"Create sheet failed: {r.text}"
        sheet_id = r.json()["id"]

        r = await client.post(f"{BASE}/api/v1/costing-sheets/{sheet_id}/scenarios",
                              headers=headers,
                              json={"name": "Perf Scenario", "display_order": 1})
        assert r.status_code == 201, f"Create scenario failed: {r.text}"
        scenario_id = r.json()["id"]

        try:
            # Bulk-insert 200 items via Supabase REST in a single request (fast setup)
            now = datetime.now(timezone.utc).isoformat()
            rows = [{
                "id": str(_uuid.uuid4()),
                "scenario_id": scenario_id,
                "section": "Hardware",
                "display_order": i,
                "description": f"Item {i:03d}",
                "qty": "1.0000",
                "unit": "unit",
                "cost_rate": "100.0000",
                "cost_currency": "SGD",
                "markup_pct": "0.2000",
                "contingency_pct": "0.0500",
                "is_visible": True,
                "is_bundle_parent": False,
                "is_bundle_override_active": False,
                "created_at": now,
                "updated_at": now,
            } for i in range(ITEM_COUNT)]

            r = await client.post(f"{SUPA_URL}/rest/v1/line_items",
                                  headers=supa_h, content=_json.dumps(rows), timeout=20)
            assert r.status_code in (200, 201), \
                f"Supabase bulk insert failed: HTTP {r.status_code}: {r.text[:200]}"

            # ── The actual assertion: time the GET via Quotemaker API ──
            start = time.perf_counter()
            r = await client.get(
                f"{BASE}/api/v1/scenarios/{scenario_id}/line-items", headers=headers)
            elapsed = time.perf_counter() - start

            assert r.status_code == 200, f"GET line items failed: {r.text}"
            items = r.json()
            assert len(items) == ITEM_COUNT, \
        