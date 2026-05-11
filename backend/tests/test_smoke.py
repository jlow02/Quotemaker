"""
Smoke test suite — runs against a live backend (local or Railway).
Usage:
  Local:   BASE_URL=http://localhost:8000 pytest tests/test_smoke.py -v
  Railway: BASE_URL=https://your-app.railway.app pytest tests/test_smoke.py -v
"""
import os
import pytest
import httpx

BASE = os.environ.get("BASE_URL", "http://localhost:8000")
EMAIL = "jlow02@gmail.com"
PASSWORD = "nextan2026"


@pytest.fixture(scope="session")
def token():
    r = httpx.post(f"{BASE}/api/v1/auth/login",
                   data={"username": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def headers(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth ───────────────────────────────────────────────────────────────────────

def test_login(token):
    assert len(token) > 20

def test_me(headers):
    r = httpx.get(f"{BASE}/api/v1/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == EMAIL


# ── Costing Sheet lifecycle ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def sheet_id(headers):
    r = httpx.post(f"{BASE}/api/v1/costing-sheets", headers=headers, json={
        "quote_title": "Smoke Test Project",
        "client_name": "Test Client",
    })
    assert r.status_code == 201, f"Create sheet failed: {r.text}"
    return r.json()["id"]

def test_create_sheet(sheet_id):
    assert sheet_id

def test_get_sheet(headers, sheet_id):
    r = httpx.get(f"{BASE}/api/v1/costing-sheets/{sheet_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["quote_title"] == "Smoke Test Project"


# ── Scenarios ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def scenario_id(headers, sheet_id):
    r = httpx.post(f"{BASE}/api/v1/costing-sheets/{sheet_id}/scenarios",
                   headers=headers, json={"name": "Option A", "display_order": 1})
    assert r.status_code == 201, f"Create scenario failed: {r.text}"
    return r.json()["id"]

def test_create_scenario(scenario_id):
    assert scenario_id

def test_list_scenarios(headers, sheet_id, scenario_id):
    r = httpx.get(f"{BASE}/api/v1/costing-sheets/{sheet_id}/scenarios", headers=headers)
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()]
    assert scenario_id in ids


# ── Line Items ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def line_item_id(headers, scenario_id):
    r = httpx.post(f"{BASE}/api/v1/scenarios/{scenario_id}/line-items",
                   headers=headers, json={
                       "section": "Hardware",
                       "description": "4K IP Camera",
                       "qty": "2",
                       "unit": "unit",
                       "cost_rate": "500",
                       "cost_currency": "SGD",
                       "markup_pct": "0.20",   # 20% — stored as decimal
                       "contingency_pct": "0.05",
                   })
    assert r.status_code == 201, f"Create line item failed: {r.text}"
    data = r.json()
    assert data["computed"] is not None, "computed pricing must be present"
    # With 20% markup + 5% contingency: selling = 500 * 1.25 = 625; total = 625 * 2 = 1250
    assert float(data["computed"]["line_total_sgd"]) == pytest.approx(1250.0, rel=0.01), \
        f"Unexpected total: {data['computed']['line_total_sgd']}"
    return data["id"]

def test_create_line_item(line_item_id):
    assert line_item_id

def test_list_line_items(headers, scenario_id, line_item_id):
    r = httpx.get(f"{BASE}/api/v1/scenarios/{scenario_id}/line-items", headers=headers)
    assert r.status_code == 200
    ids = [i["id"] for i in r.json()]
    assert line_item_id in ids

def test_markup_and_contingency_in_computed(headers, scenario_id):
    """Verify markup % and contingency % are correctly applied in computed pricing."""
    r = httpx.get(f"{BASE}/api/v1/scenarios/{scenario_id}/line-items", headers=headers)
    items = r.json()
    item = next(i for i in items if i["description"] == "4K IP Camera")
    computed = item["computed"]
    # cost_sgd = 500 * 1 (SGD) = 500
    assert float(computed["cost_sgd"]) == pytest.approx(500.0, rel=0.01)
    # selling = 500 * (1 + 0.20 + 0.05) = 625
    assert float(computed["selling_rate_sgd"]) == pytest.approx(625.0, rel=0.01)
    # total = 625 * 2 = 1250
    assert float(computed["line_total_sgd"]) == pytest.approx(1250.0, rel=0.01)


# ── Export (DOCX) ──────────────────────────────────────────────────────────────

def test_export_docx(headers, scenario_id):
    r = httpx.post(f"{BASE}/api/v1/scenarios/{scenario_id}/exports",
                   headers=headers, json={"file_type": "docx"}, timeout=30)
    assert r.status_code == 201, f"Export failed: {r.text}"
    data = r.json()
    assert data["file_type"] == "docx"
    assert data["file_path"].endswith(".docx")
    assert data["revision_number"] == 0


# ── Cleanup ────────────────────────────────────────────────────────────────────

def test_delete_sheet(headers, sheet_id):
    r = httpx.delete(f"{BASE}/api/v1/costing-sheets/{sheet_id}", headers=headers)
    assert r.status_code in (200, 204), f"Delete failed: {r.text}"
