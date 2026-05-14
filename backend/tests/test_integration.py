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

    Inputs:  Live backend at BASE_URL
    Outputs: Response time < 2.0s for 200 line items
    Owner:   [Claude]
    """
    ITEM_COUNT = 200
    BATCH_SIZE = 25  # parallel requests per batch

    async with httpx.AsyncClient(timeout=60) as client:
        headers = await _login(client)

        # Create sheet + scenario
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
            # Create ITEM_COUNT line items in parallel batches
            async def create_item(i: int) -> httpx.Response:
                return await client.post(
                    f"{BASE}/api/v1/scenarios/{scenario_id}/line-items",
                    headers=headers,
                    json={
                        "section": "Hardware",
                        "description": f"Item {i:03d}",
                        "qty": "1",
                        "unit": "unit",
                        "cost_rate": "100.00",
                        "cost_currency": "SGD",
                        "markup_pct": "0.20",
                        "contingency_pct": "0.05",
                    }
                )

            for batch_start in range(0, ITEM_COUNT, BATCH_SIZE):
                indices = range(batch_start, min(batch_start + BATCH_SIZE, ITEM_COUNT))
                batch_results = await asyncio.gather(*[create_item(i) for i in indices])
                failures = [resp.text for resp in batch_results if resp.status_code != 201]
                assert not failures, \
                    f"Item creation failed in batch {batch_start}: {failures[:2]}"

            # ── The actual assertion: time the GET ──
            start = time.perf_counter()
            r = await client.get(
                f"{BASE}/api/v1/scenarios/{scenario_id}/line-items", headers=headers)
            elapsed = time.perf_counter() - start

            assert r.status_code == 200, f"GET line items failed: {r.text}"
            items = r.json()
            assert len(items) == ITEM_COUNT, \
                f"Expected {ITEM_COUNT} items, got {len(items)}"
            assert elapsed < 2.0, \
                f"N+1 regression detected: {ITEM_COUNT} items took {elapsed:.3f}s (limit: 2.0s)"

            print(f"\n  ✅ GET {ITEM_COUNT} items in {elapsed:.3f}s")

        finally:
            # Delete exports first (FK constraint), then sheet cascades everything
            exports_r = await client.get(
                f"{BASE}/api/v1/costing-sheets/{sheet_id}/exports",
                headers=headers, timeout=30)
            if exports_r.status_code == 200:
                for exp in exports_r.json():
                    await client.delete(
                        f"{BASE}/api/v1/exports/{exp['id']}",
                        headers=headers, timeout=30)
            await client.delete(
                f"{BASE}/api/v1/costing-sheets/{sheet_id}",
                headers=headers, timeout=30)
