# Context Handoff
> Written by Cowork at end of session 2026-05-22. Read this AFTER completing the bootstrap sequence.
> Bootstrap sequence: AGENTS.md → todo.md → lessons.md → THIS FILE.

---

## Current Phase
**Phase 9 — NEXTAN Branded DOCX Export + Feature Completions**

---

## Last Completed Step
P9-02: Discount + GST toggle + pricing summary deployed to Vercel. tsc 0 errors. Live.

---

## What Was Done This Session (2026-05-22)

### 1. P9-02 — Discount + GST toggle + pricing summary (DONE)
- **New file:** `frontend/src/components/costing/CostingSheetTotals.tsx`
  - Discount type select (None / Percentage / Flat)
  - Discount value number input (debounced 750ms)
  - GST toggle (custom styled button, no radix-switch — not installed)
  - Pricing summary panel: Subtotal → Discount → Total before GST → GST → TOTAL
  - All values from `scenario.totals` (server-computed) — zero client-side math
- **Modified:** `frontend/src/pages/CostingSheetDetail.tsx`
  - `updateScenario` added to imports
  - Local state: `discountType`, `discountValue`, `showGst`
  - `updateScenarioMutation` with `invalidateQueries(['scenarios', sheetId])`
  - 750ms debounce on discount value; immediate save on type/GST changes
  - Old `grandTotal` / `grandTotalDisplay` client-side calculation removed
  - `CostingSheetTotals` inserted between LineItemTable and TermsAndNotesPanel
- Commits: `a03f9c0a` (new component), `d02d195e` (updated page)
- Vercel deploy: `dpl_6qZRWQtHjizFJ6we` → READY

### 2. DeepSeek trial result
- P9-02 was the **first DeepSeek frontend coding trial** (Justin approved 1-phase test)
- Gemini gave: APPROVED WITH CONDITIONS (classified as Medium task)
- DeepSeek self-assessed: Feasible with moderate risk
- Issues caught by TypeScript compile gate (not runtime):
  - Truncated `export default CostingSheet` instead of `export default CostingSheetDetail` — DeepSeek error
  - Missing `select.tsx` / `switch.tsx` in shadcn/ui directory — spec gap (Cowork should have checked)
- Verdict: ~85% correct. TypeScript gate caught both issues before deploy. Worth continuing.
- **Justin approved continuing DeepSeek for future frontend tasks.**

### 3. Protocol fix — DeepSeek orientation gap (DONE)
- **Gap found:** DeepSeek had no orientation template. It followed the SDG spec but skipped required artifacts (spec_feedback, blast radius declaration, assumptions log) because it wasn't briefed on its own rules.
- **Fix:**
  - `templates/deepseek_orientation.md` CREATED (commit `0086e30c`)
  - `AGENTS.md` Section 14.10 added (commit `8ae5a316`)
  - `tasks/lessons.md` lesson #39 added (commit `f758c3d3`)
- **Rule going forward:** Every DeepSeek call MUST prepend `templates/deepseek_orientation.md` with brackets filled in. If response does not start with `spec_feedback:` — discard and resend. Same as Gemini Section 13.1.

---

## Inflight Tasks (exact status)

| ID | Task | Status | Owner | Notes |
|---|---|---|---|---|
| P9-03 | Upload NEXTAN logo to Supabase `assets` bucket | ⚪ PENDING | Justin + Cowork | **Justin must provide the logo PNG first** (save to workspace folder). Cowork then uploads to Supabase Storage bucket `assets` and sets `nextan_logo_url` GlobalSetting via API. |
| P9-04 | Remove debug try/except from exports.py | ⚪ PENDING | Claude | In `backend/app/routers/exports.py` `create_export()`. One-line cleanup. Do AFTER P9-05 passes. |
| P9-05 | Visual DOCX check | ⚪ PENDING | Justin + Cowork | Download an exported DOCX from live app. Verify it matches NEXTAN sample format: branded header, line items by section, totals, T&C block, sign-off. If broken, fix export_service.py. |

**Recommended order:** P9-05 → P9-04 → P9-03 (logo whenever Justin has the file ready)

---

## Open Decisions

| Decision | Status |
|---|---|
| Continue using DeepSeek for frontend coding? | ✅ YES — Justin approved. Use orientation template every call. |
| shadcn/ui `select.tsx` + `switch.tsx` missing | Not installed. Native `<select>` + custom toggle button used instead. Can install `@radix-ui/react-switch` if proper Switch needed in future. |
| Debug wrapper in exports.py | Still live. Remove after P9-05 confirms DOCX output is visually correct. |

---

## Key Artifact Locations

| Artifact | Location |
|---|---|
| Protocol | `AGENTS.md` v5.4 + Section 14.10 (DeepSeek orientation added this session) |
| Task board | `tasks/todo.md` |
| Lessons | `tasks/lessons.md` (39 lessons as of 2026-05-22) |
| Gemini orientation template | `templates/gemini_orientation.md` |
| DeepSeek orientation template | `templates/deepseek_orientation.md` ← NEW THIS SESSION |
| OpenAPI locked contract | `backend/openapi.json` |
| DOCX export service | `backend/app/services/export_service.py` |
| DOCX debug wrapper | `backend/app/routers/exports.py` — `create_export()` function |
| Pricing summary component | `frontend/src/components/costing/CostingSheetTotals.tsx` ← NEW THIS SESSION |
| Main page component | `frontend/src/pages/CostingSheetDetail.tsx` |
| API service layer | `frontend/src/api/services.ts` |
| Environment secrets | `ai-crew/.env` (RENDER_API_KEY, GITHUB_TOKEN, VERCEL_TOKEN, DEEPSEEK_API_KEY, GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_KEY) |

---

## Live URLs

| Service | URL |
|---|---|
| Frontend (Vercel) | https://quotemaker-mu.vercel.app |
| Backend (Render) | https://quotemaker-y9wb.onrender.com |
| GitHub repo | https://github.com/jlow02/Quotemaker |

---

## How to Call DeepSeek (MANDATORY procedure from this session)

```python
# ALWAYS do this — never skip the orientation
from dotenv import load_dotenv
load_dotenv('ai-crew/.env')

orientation = open('templates/deepseek_orientation.md').read()
# Fill in: [PROJECT_NAME], [CURRENT_PHASE], [COMPLETED_PHASES], [TASK_ID], [TASK], [SDG_SPEC]

full_prompt = orientation_filled + "\n\n" + sdg_spec

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": full_prompt}],
    temperature=0.1
)

# VALIDATE: response must begin with spec_feedback:
# If it doesn't — discard and resend with orientation
```

---

## How to Call Gemini (existing procedure — unchanged)

```python
# ALWAYS prepend templates/gemini_orientation.md
# Fill in [BRACKET] fields before sending
# Section 13.1 of AGENTS.md — same rule as DeepSeek
```

---

## Critical Lessons to Remember (top 5 most relevant right now)

1. **Edit tool on large files (>400 lines)**: After any Edit on a large file, immediately run `python3 -m py_compile <file>` and `tail -5 <file>`. Edit can strip trailing lines silently. If it does, use Python `str.replace()` to fix — not Edit again.

2. **dict.get("key", default) does NOT guard against None**: Use `value or ""` for any nullable DB field in DOCX rendering. `.get(key, default)` only falls back if the key is absent — not if it's present with None.

3. **DeepSeek must be oriented**: Prepend `templates/deepseek_orientation.md` to every call. Without it, DeepSeek skips spec_feedback, blast radius, and assumptions log.

4. **Check what shadcn/ui components actually exist** before writing the spec: `ls frontend/src/components/ui/`. Not all standard shadcn components are installed. Currently missing: `select.tsx`, `switch.tsx`.

5. **GitHub repo name is `jlow02/Quotemaker`** (capital Q). Not `jlow02/quotemaker`. API calls fail silently with 404 if wrong case.

---

## Next Action After Resume

1. Complete bootstrap: AGENTS.md → todo.md → lessons.md → this file
2. Ask Justin: "Do you have the NEXTAN logo PNG ready for P9-03, or shall we start with the visual DOCX check (P9-05)?"
3. Proceed with whichever Justin chooses
