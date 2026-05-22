# Task Board
> Maintained by Cowork. Updated at the start and end of every session.

## Status Key
- 🔴 BLOCKED — cannot proceed, needs resolution
- 🟡 IN PROGRESS — currently being worked on
- 🟢 DONE — completed and verified
- ⚪ PENDING — queued, not started yet

---

## Current Phase
**Phase:** Phase 9 — NEXTAN Branded DOCX Export + Feature Completions

---

## Active Tasks

| ID | Task | Status | Notes |
|---|---|---|---|
| P9-01 | Fix DOCX export — branded NEXTAN quotation | 🟢 DONE | `render_docx` rewritten; nullable field `or ""` fix deployed (commit `b6a8021b`); 201 confirmed 2026-05-22 |
| P9-02 | Add Discount + GST toggle + section subtotals pricing summary | ⚪ PENDING | Frontend task — CostingSheetDetail.tsx |

---

## Completed Tasks

| ID | Task | Completed |
|---|---|---|
| P9-01 | DOCX export fix: nullable fields `or ""`, syntax error fix, deploy confirmed 201 | 2026-05-22 |
| P8-01 | Phase 8 bug fixes: sub_components, AddLineItemDialog, delete button, grand total, DOCX export | 2026-05-13 |
| P8-02 | Render backend deployment — live at https://quotemaker-y9wb.onrender.com | 2026-05-14 |
| P8-04 | Smoke test suite — 11/11 passed against Render (commit 03b460d8) | 2026-05-14 |
| P8-03 | Vercel frontend — live at https://quotemaker-mu.vercel.app (VITE_API_URL → Render confirmed) | 2026-05-14 |
| P8-05 | DB audit — 0 corrupt rows found, all markup_pct/contingency_pct already correct decimals | 2026-05-14 |
| P8-07 | Dashboard blank-page fix — snake_case field mapping + null-safe date formatting; deployed to Vercel | 2026-05-14 |
| P8-06 | CORS fix — added https://quotemaker-mu.vercel.app to CORS_ORIGINS on Render; redeployed | 2026-05-14 |
| P5-S01 | Gemini Phase 5 Implementation Sketch generated | 2026-05-11 |
| P5-S02 | Claude Section 16 review — APPROVED WITH CONDITIONS | 2026-05-11 |
| P5-01 | Gemini implements React frontend — 38 files, 66/66 endpoints | 2026-05-11 |
| P6-01 | Claude reviews services.ts — 2 blockers fixed (raw axios, undefined api var) | 2026-05-11 |
| P7-01 | Cowork automated audit — tsc: 0 errors, eslint: 131/150 warnings, 0 errors | 2026-05-11 |
| PRE-01 | Extract company logo and signature from template | 2026-05-10 |
| PRE-02 | Compile and confirm Project Brief (30 decisions) | 2026-05-10 |
| PRE-03 | Prepare Phase 1 Gemini handoff package | 2026-05-10 |
| P1-01 | Gemini generates PRD | 2026-05-10 |
| P1-02 | Cowork saves Gemini PRD to /docs/PRD.md | 2026-05-10 |
| P2-01 | Gemini defines Domain Models | 2026-05-10 |
| P2-02 | Cold Gemini review of Domain Models (2 passes) | 2026-05-10 |
| P2-03 | Claude backend feasibility review | 2026-05-10 |
| P2-04 | Human Operator locks Domain Models | 2026-05-10 |
| P3-01 | Claude implements FastAPI backend | 2026-05-11 |
| P3-02 | FastAPI generates openapi.json | 2026-05-11 |
| P3-03 | Human Operator approves openapi.json as locked contract | 2026-05-11 |
| P4-01 | Gemini adversarial review of Claude backend | 2026-05-11 |

---

## P9-01 Fix Detail (completed 2026-05-22)

| Fix | File | Description |
|---|---|---|
| render_docx rewrite | `backend/app/services/export_service.py` | Full rewrite to match NEXTAN sample quotation format: header table, line items by section, totals rows, terms table, T&C, sign-off. Commit `1417d953`. |
| Nullable fields `or ""` | `export_service.py` lines 325–353 | `sheet.get("field", "")` → `sheet.get("field") or ""` for all header/title fields. Fixes `TypeError: 'NoneType' object is not iterable` when contact_name/email are NULL in DB. Commit `e41480cf`. |
| Syntax error fix | `export_service.py` line 676 | Edit tool stripped `pass` from final `except` block → `IndentationError`. Fixed via Python `str.replace()` write. Commit `b6a8021b`. |
| Debug wrapper added | `backend/app/routers/exports.py` | try/except around `render_docx()` call returning full traceback as JSON 500 detail. Commit `85dddb26`. Remove once stable. |
| Exports router company fields | `backend/app/routers/exports.py` | Added `company_name`, `company_contact_name`, `company_contact_email`, `company_contact_phone` from GlobalSetting to export context. |
| GlobalSettings seeded | Supabase DB | Seeded `company_name`, `company_contact_name`, `company_contact_email`, `company_contact_phone` via API. |

---

## Pending — Next Session

| ID | Task | Notes |
|---|---|---|
| P9-02 | Discount + GST toggle + section subtotals UI | Frontend: CostingSheetDetail.tsx. Backend already supports `discount_type`, `discount_value`, `show_gst` on Scenario model. Just needs UI controls + display. |
| P9-03 | Upload NEXTAN logo to Supabase `assets` bucket | Justin must save logo PNG as a file to workspace, then upload to Supabase Storage and set `nextan_logo_url` GlobalSetting. |
| P9-04 | Remove debug try/except from exports.py | Once DOCX export confirmed stable, clean up the debug wrapper in `create_export` in `exports.py`. |
| P9-05 | Test DOCX output visually | Download an exported DOCX from the live app and verify it matches the NEXTAN sample format (header, sections, T&C, sign-off). |

---

## Open Conditions (must close before merge to main)

| ID | Condition | From | Owner |
|---|---|---|---|
| C-P4-01 | ✅ CLOSED 2026-05-14 — both integration tests pass against live Render backend | Gemini P4 R2 | CLOSED |
| C-P5-S01 | ✅ `docs/adr/ADR-001-jwt-storage.md` written | Claude sketch review | CLOSED 2026-05-11 |
| C-P5-S02 | ✅ useMutation + setQueryData — header in services.ts | Claude sketch review | CLOSED 2026-05-11 |

---

## Blocked Items
*None.*
