# Lessons Learned
> Maintained by Cowork. Updated immediately after any Human Operator correction.
> Purpose: prevent repeating the same mistakes across sessions.

## Format
Each entry records a pattern to avoid, with the context that triggered it.

---

## Lessons Log

### [2026-05-10] — Protocol Build Session
**What happened:** During the initial protocol build, the Code Quality & Transferability section (Verify Before Done, Modular Architecture, Self-Documenting Code, Simplicity First) was dropped during a document rewrite and not noticed until a final pre-write audit.
**Pattern to avoid:** When rewriting or restructuring AGENTS.md, explicitly cross-reference every section of the previous version before writing the new one. Do not assume carry-over.

### [2026-05-10] — Gemini API vs Browser
**What happened:** Initial orchestration scripts used the deprecated `google-generativeai` package and a model name (`gemini-1.5-pro`) that was no longer available, causing two separate errors before the correct `google-genai` package and model selection logic was implemented.
**Pattern to avoid:** Always use auto-discovery for model names rather than hardcoding. Use `client.models.list()` to find available models dynamically.

### [2026-05-10] — Session Bootstrap Not Self-Triggering
**What happened:** The first real project session ("Build quote generator") skipped the Session Bootstrap Protocol entirely — it did not read AGENTS.md, todo.md, or lessons.md before starting. It jumped straight into implementation planning because the user's opening message was a project brief, not the bootstrap one-liner.
**Pattern to avoid:** Never begin any work until the bootstrap sequence is explicitly confirmed. If the first user message does not reference START_HERE.md or AGENTS.md, respond with: "Before I begin, I need to run the session bootstrap. Please confirm: should I read AGENTS.md, todo.md, and lessons.md first?" Do not infer permission to skip it.

### [2026-05-10] — Wrong Gemini Model Specified / Stale Auto-Discovery Preference List
**What happened:** Scripts had `gemini-2.5-pro` at the top of the preference list. Live check via `client.models.list()` confirmed `models/gemini-3.1-pro-preview` is actually available and is the current flagship. Phase 1 PRD was therefore generated with gemini-2.5-flash rather than the best available model.
**Pattern to avoid:** The preference list in orchestration scripts must be kept current. Verified correct order as of 2026-05-10: `["gemini-3.1-pro-preview", "gemini-3.1-pro", "gemini-2.5-pro", "gemini-2.5-flash"]`. At the start of each major phase, run `client.models.list()` and confirm the top preference is still available before proceeding. Never copy the list from a prior session without verifying.

### [2026-05-10] — Cowork Delegated Gemini Interaction to Human Operator
**What happened:** The quote generator session prepared the Gemini handoff package correctly but then asked the Human Operator to manually open Gemini, select the model, and paste the content. This contradicts the protocol — Cowork handles Gemini interactions via the Chrome MCP browser automation.
**Pattern to avoid:** ~~Cowork must use Chrome MCP for Gemini.~~ SUPERSEDED — see lesson below. Chrome MCP cannot interact with gemini.google.com. All Gemini interactions use the Gemini API.

### [2026-05-10] — gemini.google.com Cannot Be Automated via Chrome MCP (Full Block)
**What happened:** Attempted full automation of Gemini via Chrome MCP. Findings per tool:
- `navigate` to gemini.google.com → "Navigation to this domain is not allowed" (hard block)
- `navigate` to google.com → works; JavaScript `window.location.href` to Gemini from there → tab DOES navigate to gemini.google.com (async)
- `screenshot`, `find`, `read_page`, `javascript_tool` on gemini.google.com → all blocked: "Permission denied for this action on this domain"
- Computer-use on Chrome → tier "read" only; no clicking or typing allowed
**Conclusion:** The Chrome MCP deliberately blocks gemini.google.com at the server level. This is a hard technical constraint, not configurable.
**Protocol correction (final):** All Gemini interactions use the Gemini API (`google-genai` package). API key stored in `.env`. Cowork calls the API directly — no Human Operator action required. Manual paste is the emergency fallback only. AGENTS.md Section 13 updated accordingly. Confirmed by Gemini as Lead Architect on 2026-05-10.

### [2026-05-10] — Gemini API Requires .env File for Sandbox Access
**What happened:** GOOGLE_API_KEY was stored as a Windows environment variable (`setx`), which is inaccessible from the Linux sandbox that runs scripts. Attempts to read it via `os.environ` failed.
**Pattern to avoid:** Always store secrets in a `.env` file at the project root. The sandbox reads files; it cannot read Windows environment variables. `.env` must be in `.gitignore`. `.env.example` must exist with placeholder values.

### [2026-05-10] — Never Assert Model Names or API Behaviour From Training Data
**What happened:** Cowork recommended "Gemini 2.5 Pro" to the Human Operator based on training knowledge, when Gemini 3.1 Pro was already available. Training data has a cutoff — external services, model versions, and API behaviour change after it.
**Pattern to avoid:** Never state a specific model name, API version, SDK method, or external service behaviour as current fact based on training knowledge alone. Before asserting anything about an external service (model names, API endpoints, pricing, feature availability), use web search to verify, or use the service's own discovery mechanism (e.g. `client.models.list()`). If search is unavailable, explicitly caveat: "This is based on my training data and may be outdated — please verify."
**Applies to:** Gemini models, Claude models, OpenAI models, any third-party API, SDK versions, browser extension capabilities, and any technology that evolves over time.

### [2026-05-11] — Orchestrator Declared Consensus Without Confirming With Blocking Agent
**What happened:** After collecting reviews from Gemini (BLOCKED), GPT (APPROVED WITH CONDITIONS), and DeepSeek, Claude synthesised a "unified direction" that resolved Gemini's three blocking conditions in Claude's favour — without sending the proposed resolutions back to Gemini for confirmation. The Human Operator caught this and correctly identified it as Claude pushing its own position through under the guise of synthesis.
**Pattern to avoid:** A BLOCKED verdict cannot be resolved by the orchestrator unilaterally. Any proposed resolution to a raised objection must be sent back to the objecting agent and their explicit updated verdict received before the issue is considered closed. The orchestrator's synthesis is always a biased document when the orchestrator was a participant in the debate — it must be treated as one agent's opinion, not an objective summary.
**Rule added:** AGENTS.md Section 11.6 — Synthesis Must Be Confirmed, Not Declared.

### [2026-05-10] — Cold Review Framing Works
**What happened:** The first Cold Gemini review returned a BLOCKED verdict with 5 sharp issues. The adversarial framing ("your job is to find what is wrong") was effective. A subsequent debate produced a hybrid solution on Issue 3 (API isolation layer) that neither agent had proposed independently.
**Pattern to note:** Adversarial framing produces genuine critique. Quick agreement without debate is a yellow flag. The debate format (structured rebuttal, point-by-point response) resolves disagreements faster than open-ended discussion.

### [2026-05-11] — Phase-Locked Acceptance Criteria Creates Bottleneck
**What happened:** The proposed AC refinement loop (Condition 4 in QA Ownership debate) originally stated "Justin locks the final AC set at the start of each phase." Gemini correctly flagged this as a bottleneck — critical discoveries made mid-phase would be blocked from incorporation until the next phase, potentially shipping known defects.
**Pattern to avoid:** Do not treat acceptance criteria as frozen at phase start. The correct model: Justin establishes a baseline at phase start (defines initial scope), but approved refinement requests are incorporated into the current phase's test spec upon approval. "Phase-locked" and "baseline" are different things. Use "baseline" language, not "locked."

### [2026-05-11] — Bash Append Creates Duplicate Sections When File Already Has Content
**What happened:** Used `cat >> file` to append Section 15 in a previous session. In the current session, additional edits were made to the same file via the Edit tool. When Section 15 was re-appended for recovery, a duplicate "## 15. QA OWNERSHIP PROTOCOL" appeared at line 595. Section 16 then got absorbed into the duplicate content and disappeared.
**Pattern to avoid:** When a file has been modified across multiple sessions via both Edit tool and bash append, check for duplicate section headers before appending. Use `grep -n "^## SectionName"` to confirm the section doesn't already exist. If recovering lost content, truncate to the clean line first (`head -n N > clean && cp clean target`), then append.

### [2026-05-11] — Always Use python3 Explicitly When Checking Python File Integrity
**What happened:** Ran `python -c "import ast; ast.parse(...)"` to validate router files. Reported fx_rates.py and exports.py as broken with syntax errors. Both files were actually fine — the issue was using the `python` binary (Python 2.x behaviour in the sandbox) instead of `python3`. Nearly triggered unnecessary rework on complete, healthy files.
**Pattern to avoid:** Always use `python3` explicitly for any Python file validation in the sandbox. Never use bare `python` — it may resolve to Python 2. Verify with `python3 --version` if uncertain.

### [2026-05-11] — Session Must Update todo.md Before Closing
**What happened:** The previous session completed the full FastAPI backend (66 routes, all models, schemas, services, routers) but closed without updating todo.md. The task board showed P3-01 as "IN PROGRESS" when the backend was effectively complete. The next session (this one) wasted time re-assessing work that was already done.
**Pattern to avoid:** The last action of every session must be updating todo.md to reflect exact current state — not the phase label but the specific files/tasks completed. If a session ends abruptly (context limit, timeout), Cowork must still write a one-line status to todo.md before the context expires. "Claude implements FastAPI backend — IN PROGRESS" is not useful. "P3-01: All 66 routes implemented and app boots — awaiting openapi.json generation and Justin lock" is useful.

### [2026-05-11] — Task Granularity in todo.md Must Be File-Level for Phase 3+
**What happened:** P3-01 was a single task covering the entire backend implementation. With 13 models, 14 schemas, 6 services, and 14 routers, there was no way to know from the task board which components were done and which were not. When resuming, had to scan every file manually to assess state.
**Pattern to avoid:** For implementation phases, break tasks to the component level: models, schemas, services, and routers as separate tracked items. Each gets its own status. This makes partial progress visible and makes session handoffs precise.

### [2026-05-11] — Bash Background Processes Die Between Calls
**What happened:** Ran `python3 long_script.py >> log &` to background a 270s generation job. The process started (PID returned), but the next bash call showed the log file at 0 bytes and the process no longer running. Each bash call is an isolated sandbox — background processes are killed when the call exits.
**Pattern to avoid:** Never use `&` to background long-running scripts expecting them to persist. The bash sandbox is stateless between calls. For tasks exceeding the 45s timeout, design scripts to accept a chunk index argument (`sys.argv[1]`) and call them once per chunk. Each call completes in <45s; assemble results afterward.

### [2026-05-11] — 45s Bash Timeout Requires Index-Based Chunked Scripts
**What happened:** Phase 5 frontend generation required 9 Gemini API calls (~30s each = ~270s total). A single orchestration script timed out. The fix: restructure into a script accepting a group index, one streaming call per invocation, save to `/tmp/p5_chunk_N.txt`, called N times in sequence.
**Pattern to avoid:** Any multi-step generation task where (num_api_calls × avg_seconds) > 40 must use the index-based pattern before writing the script. Assemble all chunks in a separate final bash call.

### [2026-05-11] — Gemini Omits `export` Keyword on Some Chunk Boundaries
**What happened:** services.ts was generated in 8 domain groups. Several groups produced `async function` without `export`, even though the prompt specified exported functions.
**Pattern to avoid:** After assembling chunked TypeScript, always post-process: `re.sub(r'^(?<!export )async function ', 'export async function ', content, flags=re.MULTILINE)`. Verify with `grep -c "^export async function"` against expected count. Never trust consistent export across all chunks.

### [2026-05-11] — Isolated File Generation Causes Coupling Between Interdependent Files
**What happened:** `axios.ts` was generated without knowledge of `authStore.ts`. Gemini defined its own local Zustand store inside `axios.ts`, creating two competing auth stores when `authStore.ts` was generated afterward.
**Pattern to avoid:** When generating interdependent files, pass the first ~2000 chars of already-generated files as context in the dependent file's prompt. Correct dependency order matters: generate `authStore.ts` before `axios.ts`, or explicitly provide the authStore interface in the axios.ts prompt. Never generate a file that imports from another without showing that other file's interface.

### [2026-05-11] — gemini-2.5-flash Is the Right Model for Large Code Gen, Not 3.1-Pro
**What happened:** `gemini-3.1-pro-preview` has mandatory thinking mode — `thinking_budget=0` rejected, `thinking_budget=1024` accepted but thinking tokens eat the output budget, causing streams to die at ~12KB even with `max_output_tokens=65536`. `gemini-2.5-flash` produces 8–16KB code files reliably in 10–40s.
**Pattern to avoid:** For code generation tasks, use preference list `["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.1-flash-lite"]`. The flagship list (`gemini-3.1-pro-preview` first) is correct for reasoning/review tasks only. Maintain two separate preference lists: one for generation, one for analysis.

### [2026-05-11] — Human Operator Can Paste Terminal Commands for Long-Running Tasks
**What happened:** Phase 7 (npm install, tsc --noEmit, eslint) requires commands running 1–3 minutes — beyond the 45s bash timeout and not chunkable. Justin offered to paste commands into his terminal and return output.
**Pattern to note:** At the start of any phase requiring terminal commands >45s, announce upfront: "This phase needs terminal access — I'll send paste commands, please stay on standby." For autonomous phases (review, analysis, file generation), proceed without waiting. Phase 6 = autonomous. Phase 7 = standby needed. Phase 8 = interactive by nature.

### [2026-05-11] — AGENTS.md Is Frozen at v5.4 — Do Not Reopen Protocol Debates
**What happened:** Protocol went through 3 rapid versions (v5.2 → v5.3 → v5.4) in one session via cold reviews and team debates. Each fix introduced edge cases that prompted more debate. The team (Gemini, DeepSeek, GPT) unanimously agreed the protocol was over-engineered for a 2-person + AI team and declared v5.4 frozen.
**Pattern to avoid:** Do not run cold_review_v54.py or initiate new protocol debates. Do not open AGENTS.md for editing unless a specific rule caused a *real, logged failure* in an actual project task (logged in tasks/friction_log.md). If a future session agent is tempted to refine the protocol, redirect to the quote maker work instead. The next AGENTS.md change should be a pruning pass based on evidence, not a prevention pass based on theory.

### [2026-05-11] — Pre-Submit Checklists Require Proof Artifacts, Not Just Checkmarks
**What happened:** Proposed a pre-submit checklist with [x] marks as quality gate. Gemini 3.1 Pro flagged that LLMs will hallucinate [x] to satisfy a system prompt without actually performing the check. A bare checkmark with no evidence is ungameable in theory but trivially gameable in practice.
**Pattern to avoid:** Any checklist used as a quality gate must require a verifiable proof artifact next to each checked item (E2B execution ID, diff line counts, specific file/line references). The cross-reviewer is explicitly instructed to reject output if [x] appears without accompanying evidence.

### [2026-05-13] — SQLAlchemy Relationship Name Must Match All Callers
**What happened:** `LineItem` model defined `bundle_components` as the relationship name. Every router (`line_items.py`) and service used `selectinload(LineItem.sub_components)` and `item.sub_components`. This mismatch caused `AttributeError: 'LineItem' object has no attribute 'sub_components'` → HTTP 500 on every GET /scenarios/{id}/line-items call. The fix was a one-line rename in the model.
**Pattern to avoid:** When defining or renaming an ORM relationship, immediately grep all files for both the old and new name before committing. The model definition is the single source of truth — every `relationship()` name must be unique and must exactly match every `back_populates`, `selectinload()`, `joinedload()`, and `item.attribute` reference across the entire codebase.

### [2026-05-13] — Form Percentage Inputs Must Be Divided by 100 Before Sending to Backend
**What happened:** The add line item form collected `markup_pct` and `contingency_pct` as human-readable percentages (e.g. "10" for 10%). The backend stores them as decimals (0.10 = 10%). Submitting "10" caused the backend to apply 1000% markup, inflating line totals by 10×. One item with 20% markup on 500 SGD × 2 units showed as ~6396 SGD instead of 1250 SGD.
**Pattern to avoid:** Any form field that collects a percentage for a backend field stored as a decimal must divide by 100 in the `handleSubmit` before calling the API. Add a comment in the form clearly documenting the conversion. Also verify the conversion is correct by checking the backend schema field type (Numeric with stored decimal) before writing the form.

### [2026-05-13] — WeasyPrint Requires GTK3 — Not Available on Windows; Use DOCX Instead
**What happened:** The backend had a `/exports` endpoint generating PDF via WeasyPrint. WeasyPrint requires GTK3 libraries (`libpango`, `libcairo`, etc.) which are not present on Windows. Calling the export endpoint caused an unhandled server crash. The export button on the frontend then triggered the crash response, which caused the CostingSheetDetail page to reload (because `onSettled` was invalidating queries and triggering `isLoading`).
**Pattern to avoid:** WeasyPrint PDF export is Linux/Mac only. For any Windows dev environment or Railway (Linux but missing GTK3 by default), use `python-docx` for DOCX export instead. If PDF is truly required, use a headless Chrome approach (puppeteer/playwright) or a cloud PDF API. Never deploy WeasyPrint without confirming GTK3 is in the runtime environment.

### [2026-05-13] — Railway Deployment: Env Vars Must Be Set Before First Deploy
**What happened:** Railway deployment crashed with `pydantic_core.ValidationError: 4 validation errors for Settings` — all 4 were missing environment variables (DATABASE_URL, SUPABASE_URL, SUPABASE_KEY, SECRET_KEY). Railway does not inherit local `.env` files. Every required env var must be manually added in Railway → Project → Variables before the first deploy. A 502 or CRASHED status almost always means missing env vars if the code itself is working locally.
**Pattern to avoid:** Before pushing to Railway, maintain a deployment checklist: (1) all required env vars documented in `.env.example`, (2) each var added to Railway Variables tab, (3) root directory set to `backend` (or whatever the app root is), (4) domain generated in Settings → Networking. After adding vars, always click Restart to trigger a new deployment — Railway does not auto-redeploy on variable changes in all cases.

### [2026-05-13] — Supabase Storage Buckets Must Exist Before Any Upload Attempt
**What happened:** The export service tried to upload a DOCX to the `exports` Supabase Storage bucket, and the asset service referenced the `assets` bucket. Neither bucket existed — both had to be created manually via the Supabase API using the service role key. The error was a silent 404/403 from Supabase that manifested as a 500 from the backend.
**Pattern to avoid:** At deployment time, verify all required Supabase Storage buckets exist before running the app. Add a startup check or a one-time provisioning script. The buckets needed are: `exports` (for DOCX/PDF files) and `assets` (for logo/signature images). Creation via Python: `supabase.storage.create_bucket(name, options={"public": False})`.

### [2026-05-14] — CORS_ORIGINS Must Include the Frontend Production Domain Before Launch

**What happened:** The Render deployment had `CORS_ORIGINS` set to a garbage value (not the intended `http://localhost:3000`). Even if it had been correct, it didn't include the Vercel production URL. The browser login showed "Network Error" immediately — CORS preflight returned HTTP 400 with no `access-control-allow-origin` header, silently blocking all API calls from the frontend. Direct API calls (curl, smoke tests) worked fine because they don't send an `Origin` header. This made the backend appear healthy when it was inaccessible from the browser.
**Pattern to avoid:** Before declaring Phase 8 complete, always verify CORS from the browser's perspective: run `curl -X OPTIONS <backend>/api/v1/auth/login -H "Origin: <frontend-url>"` and confirm you get HTTP 200 with `access-control-allow-origin: <frontend-url>` in the response. A passing smoke test suite does NOT prove CORS works — smoke tests are server-to-server. Also: when setting CORS_ORIGINS on Render, always include both the dev origin (`http://localhost:3000`) AND the production frontend URL (`https://<project>.vercel.app`) from day one.

### [2026-05-14] — Always Use APIs Instead of Browser Automation When an API Exists
**What happened:** Spent multiple sessions using Chrome MCP browser automation to update environment variables on Render (clicking Edit, fighting React controlled component state, clipboard not transferring across domains, scheduled tasks running blind). Each attempt wasted tokens and often failed. The Render REST API (`api.render.com/v1`) supports full env var CRUD with a personal API key. One `curl` call replaces the entire browser workflow. Similarly, GitHub has a REST API for file updates, Vercel has an API, and Supabase has management APIs. Once API keys were stored in `.env` and the API-first approach was adopted, every task completed in a single bash call.
**Pattern to avoid:** Never open a browser dashboard to perform an action that has a REST API. Before any automation task involving Render, GitHub, Vercel, Supabase, or any external service, ask: "Does this service have an API?" If yes, use it. Only fall back to browser automation for truly UI-only actions (e.g. OAuth flows, CAPTCHA). Store all API keys in `.env` at the start of the project — not after the first time you need them.
**Stored keys (as of 2026-05-14):** `RENDER_API_KEY`, `GITHUB_TOKEN`, `VERCEL_TOKEN`, `DEEPSEEK_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY` — all in `ai-crew/.env`.
**Secondary lesson:** Never ask the Human Operator to manually interact with any UI to verify something the API can answer. Run the smoke tests, call the API, read the logs — then report. Only escalate to Justin when something genuinely requires human judgment or credentials that cannot be stored.

### [2026-05-14] — Supabase Legacy JWT Keys Are Invalid After JWT Secret Rotation
**What happened:** The Supabase project's JWT secret was rotated at some point, invalidating all legacy `eyJhbG...` service_role keys. Every Supabase Storage upload returned `{'statusCode': 400, 'error': 'Unauthorized', 'message': 'signature verification failed'}`. The fix was switching to the new `sb_secret_` format key from Supabase's "Publishable and secret API keys" tab (not the "Legacy" tab). Additionally, `supabase-py` versions below 2.16.0 reject `sb_secret_` keys with "Invalid API key" — the library itself must be on ≥2.16.0.
**Pattern to avoid:** When Supabase Storage returns `signature verification failed`, do not re-paste the same JWT key or rotate the JWT — the JWT secret has been rotated and legacy keys are permanently invalid. Go to Supabase Dashboard → Settings → API Keys → "Publishable and secret API keys" tab → copy the `sb_secret_` format key. Also verify `supabase` in `requirements.txt` is ≥2.16.0 before deploying.

### [2026-05-14] — Frontend Interfaces Must Match API Snake_Case Field Names Exactly
**What happened:** Dashboard.tsx had a mock `CostingSheet` interface with camelCase fields (`title`, `clientOrganization`, `createdAt`, `status`). The actual API returns snake_case (`quote_title`, `client_name`, `created_at`, no `status`). The component cast the API response with `as unknown as CostingSheet[]` to silence TypeScript. At runtime `sheet.createdAt` was `undefined`, so `new Date(undefined)` threw `RangeError: Invalid time value` — crashing the entire React tree and producing a blank white page after login.
**Pattern to avoid:** Never use `as unknown as SomeType` to silence a type mismatch on an API response. The interface must exactly match what the API returns (use the service function's return type). When an interface is introduced, immediately verify it compiles without the `unknown` cast. Also add null guards on all date formatting calls: `{date ? format(new Date(date), 'MMM dd, yyyy') : 'N/A'}` — never `format(new Date(possiblyUndefined), ...)` directly.

### [2026-05-14] — GitHub API File Pushes From Windows-Mounted Filesystem May Contain Null Bytes
**What happened:** Used the Edit tool to modify files on a Windows NTFS-mounted filesystem (`/sessions/.../mnt/ai-crew/`), then read the files back in Python and pushed them to GitHub via the Contents API. The Edit tool left trailing null bytes (`\x00`) at the end of some files. TypeScript compiler (tsc) rejects null bytes with `TS1127: Invalid character` — build failed. Additionally, a second file got truncated mid-content (`export default ExportsHistory` became just `expo`) because the filesystem write was interrupted.
**Pattern to avoid:** When pushing files to GitHub via the API from a Windows-mounted sandbox path: (1) always write the final file to `/tmp/` (Linux tmpfs) first — never push directly from `/sessions/.../mnt/`; (2) verify `content.count(b'\x00') == 0` before base64-encoding; (3) `tail -3 /tmp/file.tsx | cat -A` to visually confirm the final lines look correct; (4) never use `rstrip(b'\x00')` on a file that was read from the Windows mount — the file itself may be truncated or corrupted; instead, reconstruct the entire file content from scratch in the Python script using a heredoc or inline string.

### [2026-05-13] — Export Mutation onSettled Must Not Invalidate Queries That Drive isLoading
**What happened:** The export mutation had `onSettled: () => queryClient.invalidateQueries({ queryKey: ['costingSheet', sheetId] })`. This invalidated the main sheet query, which set `sheetQuery.isLoading = true`, which triggered the full-page loading state ("Loading costing sheet..."), which effectively refreshed the entire page on every export. Looked like the export crashed the page.
**Pattern to avoid:** Never invalidate queries in `onSettled`/`onSuccess` of a mutation unless you actually need the fresh data immediately AND those queries are not part of the page's `isLoading` gate. For export mutations specifically, `onSuccess` should only show a toast — no query invalidation needed. Also: do not include mutation `.isPending` states in the page-level `isLoading` check; use local loading indicators instead.

### [2026-05-22] — dict.get("key", default) Does NOT Guard Against Explicit None Values
**What happened:** `render_docx` in `export_service.py` used `sheet.get("contact_name", "")` expecting a safe empty string fallback. The DB column was `NULL` for that row, so the dict contained `{"contact_name": None}`. `dict.get("key", default)` only uses `default` when the key is **absent** — if the key exists with `None` as its value, you get `None` back. python-docx's `.text` setter iterates the value, throwing `TypeError: 'NoneType' object is not iterable`. The export returned HTTP 500 (text/plain — raw uvicorn crash) with no traceback visible.
**Pattern to avoid:** For any nullable DB field used in document rendering, always use `value or ""` (or `value or "fallback text"`) — never `dict.get("key", "default")` alone. The `or` guard handles `None`, `""`, and missing key simultaneously.
**Fix applied:** Changed all header cell assignments in `render_docx` from `sheet.get("field", "")` → `sheet.get("field") or ""`. Verified 201 response after deploy.

### [2026-05-22] — Edit Tool Can Strip Trailing Lines From Files Near Context Boundary
**What happened:** Used the Edit tool to make small targeted changes to `export_service.py` (676 lines). After the edit, `python3 -m py_compile` reported `IndentationError: expected an indented block after 'except' statement on line 674`. The `pass` on the final `except` block had been stripped — `tail -5` showed only a trailing space character instead of `        pass`. The Edit tool's diff had succeeded but the physical file was missing the last meaningful line.
**Pattern to avoid:** After any Edit tool operation on a file >400 lines, immediately run `python3 -m py_compile <file>` and `tail -5 <file>` to verify integrity. If the Edit tool strips trailing content, do NOT use Edit again — use a Python `open(path).read()` → `str.replace()` → `open(path,'w',newline='\n').write()` approach to fix in a single atomic write.
**Rule:** Always verify syntax after every Edit on large files. Never trust that the Edit succeeded just because the tool reported "updated successfully."

### [2026-05-22] — Render "update_failed" = Server Crashed on Startup (Not Build Failure)
**What happened:** A deploy showed `build_in_progress` → `update_failed`. This is different from `build_failed` (which means the pip install / build step itself crashed). `update_failed` means the build succeeded but the new process crashed after startup — usually a Python syntax error, import error, or missing env var. The previous live deploy (`status=live`) stays active as the rollback.
**Pattern to avoid:** When a Render deploy shows `update_failed`: (1) immediately run `python3 -m py_compile` on all recently changed Python files locally; (2) check for import errors by running `python3 -c "from app.main import app"` in the backend directory; (3) only then trigger a new deploy. Do not trigger re-deploys blindly — diagnose locally first.

### [2026-05-22] — Agents Must Be Oriented on Their Own Rules at Every Call (No Persistent Memory)
**What happened:** DeepSeek was called to implement P9-02 with a detailed SDG spec. It produced structurally correct code but omitted all three required output artifacts: the `spec_feedback` pre-generation block (Section 14.2), the formal `blast_radius` declaration (Section 14.8), and the `assumptions_made` log (Section 14.9). The spec was followed; the agent's own operating protocol was not. Root cause: no orientation block was prepended to the prompt. DeepSeek (like Gemini) is stateless — it has no memory of prior sessions, no knowledge of AGENTS.md, and no awareness of team conventions unless told at call time.
**Pattern to avoid:** Never send a task prompt to DeepSeek or Gemini without prepending the relevant orientation template. The SDG spec alone is not enough — it covers the task but not the agent's operating rules. A well-written