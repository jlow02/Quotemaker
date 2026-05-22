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
| P9-02 | Add Discount + GST toggle + section subtotals pricing summary | 🟢 DONE | `CostingSheetTotals.tsx` created; `CostingSheetDetail.tsx` updated; deployed Vercel `dpl_6qZRWQtHjizFJ6we` 2026-05-22 |
| P9-03 | Upload NEXTAN logo to Supabase `assets` bucket | ⚪ PENDING | Justin must save logo PNG to workspace first, then Cowork uploads + sets `nextan_logo_url` GlobalSetting |
| P9-04 | Remove debug try/except from exports.py | ⚪ PENDING | Wrapper in `backend/app/routers/exports.py` `create_export()`. Remove once P9-05 visual check passes |
| P9-05 | Test DOCX output visually | ⚪ PENDING | Download exported DOCX from live app; verify matches NEXTAN sample format (header, sections, T&C, sign-off) |

---

## Completed Tasks

| ID | Task | Completed |
|---|---|---|
| P9-02 | Discount+GST toggle+pricing summary — CostingSheetTotals.tsx (new) + CostingSheetDetail.tsx (updated); tsc 0 errors; Vercel READY | 2026-05-22 |
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

## P9-02 Fix Detail (completed 2026-05-22)

| File | Action | Detail |
|---|---|---|
| `frontend/src/components/costing/CostingSheetTotals.tsx` | CREATED | New component: discount type select, discount value input, GST toggle (custom button), pricing summary panel (Subtotal → Discount → GST → Total). All values from `scenario.totals` — no client-side math. Commits `a03f9c0a`. |
| `frontend/src/pages/CostingSheetDetail.tsx` | MODIFIED | Added `updateScenario` import + `CostingSheetTotals` import; local state for `discountType`, `discountValue`, `showGst`; `updateScenarioMutation` with `invalidateQueries(['scenarios', sheetId])`; handlers with 750ms debounce on `discountValue`; removed client-side `grandTotal`/`grandTotalDisplay`; `CostingSheetTotals` inserted between LineItemTable and TermsAndNotesPanel. Commit `d02d195e`. |

**DeepSeek trial notes (P9-02 was the first DeepSeek frontend trial):**
- Gemini: APPROVED WITH CONDITIONS (Medium task)
- DeepSeek self-assessment: Feasible with moderate risk
- Issues caught by tsc compile gate: truncated `export default` name, missing shadcn/ui components (`select.tsx`, `switch.tsx` not in codebase — replaced with native elements)
- Verdict: ~85% correct. Worth continuing. Orientation gap fixed (see below).

**Protocol changes this session:**
- `templates/deepseek_orientation.md` CREATED — mandatory orientation for all DeepSeek calls (commit `0086e30c`)
- `AGENTS.md` Section 14.10 added — DeepSeek Session Orientation (Mandatory) (commit `8ae5a316`)
- `tasks/lessons.md` lesson #39 added (commit `f758c3d3`)

---

## P9-01 Fix Detail (completed 2026-05-22)

| Fix | File | Description |
|---|---|---|
| render_docx rewrite | `backend/app/services/export_service.py` | Full rewrite to match NEXTAN sample quotation format: header table, line items 