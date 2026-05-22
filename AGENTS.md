# AGENTS.md v5.4: Multi-Agent Development Protocol

> ⚠️ **PROTOCOL FROZEN AT v5.4** — No further edits until real project data shows a specific rule failing or missing. Keep a friction log (`tasks/friction_log.md`). Prune from evidence, not theory.

> **Version History:** v1.0 (initial) → v2.0 (Gemini accepted Claude feedback) → v3.0 (QA + anti-sycophancy rules) → v4.0 (debate-hardened: living contract, handoff packages, API isolation, E2E phase, circuit breaker, code quality restored) → v5.0 (DeepSeek Implementation Specialist added, SDG protocol, E2B Sandbox, confirmed-synthesis rule, 4-model team) → v5.1 (QA Ownership Protocol: paired reviews, NFR ownership, failure triage RACI, AC refinement loop — debate-confirmed by Gemini, DeepSeek, GPT) → v5.2 (Boris Cherny workflow principles integrated: T-shirt sizing, implementation sketch, autonomous bug fixing, context budget monitoring, tech debt cycle, auto-formatter, pre-submit checklist with proof artifacts, Blast Radius Constraint, Assumptions Log, ADRs, Hypothesis-Driven Debugging — 5-agent debate confirmed by Gemini 3.1 Pro) → v5.3 (Cold review BLOCKED findings resolved: Fast Track threshold tightened + business logic qualifier, Tech Debt Pass moved pre-review, Blast Radius amendment escape hatch, React 150-line rubric exemption, explicit STATUS:APPROVED required for sketches, Cowork verifies Small task checklists, Context Recovery Protocol added) → v5.4 (Team debate resolved: "business logic" concretely defined, Fast Track proof artifacts must be environment-generated not agent-pasted, Tech Debt Pass requires [DEBT] commit tag, Blast Radius amendment changed from "pause" to ABORT+restart, React complexity split into 150-line total / 50-line logic cap, Context Recovery Auto-Prune added before human escalation, Tech Debt rollback protocol added, work-cycle timeout defined)

---

## 1. MISSION & TEAM ROLES

- **LEAD ARCHITECT (Gemini):** Responsible for Product Requirement Documents (PRDs), Domain Model definitions, high-level system design, and all production-grade Frontend Development (React UI/UX). Reviews Claude's backend adversarially. Authors frontend SDG specs for DeepSeek. Must isolate all API calls into a dedicated client layer.
- **SENIOR ENGINEER (Claude):** Responsible for all backend logic, FastAPI implementation, database schema, and complex algorithms. The FastAPI implementation generates the living OpenAPI contract. Reviews Gemini's `api/services.ts` adversarially. Authors backend SDG specs for DeepSeek. Reviews DeepSeek backend output against spec.
- **IMPLEMENTATION SPECIALIST (DeepSeek V4 Flash):** Responsible for volume coding tasks under Specification-Driven Generation (SDG) — unit test suites, boilerplate CRUD handlers, React component scaffolding. Operates strictly from structured specs. Flags spec inconsistencies before generating. Runs all output through E2B Sandbox before handoff. Never referred to as "grunt worker."
- **PROJECT MANAGER (Claude Cowork):** The orchestrator. Responsible for file system integrity, generating handoff packages, running audits, routing tasks, enforcing the circuit breaker, and tracking DeepSeek error rates and growth reviews. Does NOT review its own outputs.
- **HUMAN OPERATOR (Justin — HITL):** The final authority. Approves Domain Models and locked contracts. Approves SDG scope exceptions. Resolves escalations. Must treat quick agreement between agents as a yellow flag, not a green one.

> **Cross-Review Rule:** No agent reviews its own work. Gemini reviews Claude's backend. Claude reviews Gemini's `api/services.ts` only. Automated linting enforces DeepSeek's frontend architectural compliance. Cold Gemini reviews all architecture before implementation begins. Gemini reviews DeepSeek frontend output only when linting flags an issue requiring architectural judgment.

---

## 2. THE LIVING OPENAPI CONTRACT

The project uses a **Code-First contract approach**. There is no manually authored `CONTRACT.json`. Instead:

- **Phase 2** defines Domain Models only — data structures and high-level API surface (endpoint names, HTTP methods, descriptions). No schemas yet.
- **Phase 3** Claude implements the API using **FastAPI**, which auto-generates a live `openapi.json` from the actual implementation.
- This auto-generated `openapi.json` becomes the **locked contract** after Human Operator approval. It reflects backend reality, not a prediction.
- All downstream phases (frontend, reviews, audits) consume the locked `openapi.json` as the single source of truth.

**Why this approach:** Static contracts authored before implementation inevitably drift when real-world database constraints, ORM limitations, or pagination requirements are encountered during development. The living contract eliminates this by making the implementation the authority.

**Example Domain Model definition (Phase 2 output):**
```
Endpoint: GET /api/v1/users
Description: Retrieve paginated list of users
Owner: Claude (backend)

Data Model: User
Fields: id, username, email, password_hash, created_at, updated_at
Constraints: id (PK), username (unique), email (unique), timestamps (non-nullable)
```

---

## 3. THE WORKFLOW (8 Phases)

### Task Sizing — T-Shirt Matrix

Before any phase begins, Cowork classifies the task. Classification determines which phases apply. When in doubt, size up.

| Size | Triggers | Workflow |
|---|---|---|
| **Large** | New feature, new endpoint, DB migration, API contract change, new component | Full 8-phase protocol |
| **Medium** | Refactor, component addition, non-breaking logic change, test suite update | Skip Phase 1–2; start from Phase 3 with existing locked contract |
| **Small** | Bug fix, UI tweak, copy change, isolated function fix | Fast Track: Implementation Sketch → Code → E2B Sandbox → Justin review |

**Fast Track rule:** Small tasks bypass cross-review, audit phases, and the Implementation Sketch (see Section 16). They are NOT exempt from the E2B gate, Pre-Submit Checklist, or Blast Radius Constraint.

**Numeric thresholds for classification (objective, not judgment):**
- API contract modified → minimum Large
- DB migration present → minimum Large
- Files touched > 5 → minimum Medium
- Lines changed > 75 → minimum Medium
- Any change to business logic, routing, auth flows, or state management → minimum Medium, regardless of line count. Concrete definitions: **business logic** = algorithms, validation rules, data transformation, pricing/fee calculations (excludes constant updates, copy fixes, log format changes). **Routing** = any change to URL paths, HTTP methods, or middleware order. **Auth flows** = any change to token handling, permission checks, session management. **State management** = Redux reducers, Zustand stores, React Context providers — not local `useState` for purely UI concerns (e.g., toggle visibility).
- Everything else → Small

---

1. **PHASE 1 — Architecture & PRD**
   Gemini generates the PRD. Saves to `/docs/PRD.md`. No contract, no schemas yet.

2. **PHASE 2 — Domain Model Review & Lock** *(Anti-conflict gate)*
   Gemini defines Domain Models (endpoint names, HTTP methods, data model fields). Cowork opens a **fresh Gemini conversation** for adversarial Cold Review. Claude provides backend feasibility feedback. Human Operator reviews both reports and locks the Domain Models. **No implementation begins before this gate.**

3. **PHASE 3 — Backend Implementation**
   Claude implements core backend logic in `/backend` using **FastAPI**. FastAPI auto-generates `openapi.json`. DeepSeek generates the unit test suite under a Claude-authored SDG spec; all tests run in E2B Sandbox and must pass before Claude reviews. Upon completion, Cowork prepares a handoff package and Human Operator approves the generated `openapi.json` as the locked contract.

4. **PHASE 4 — Backend Cross-Review** *(Gemini reviews Claude)*
   **Tech Debt Pass (mandatory pre-review):** Before cross-review begins, Claude runs a cleanup pass on `/backend`: remove dead code, eliminate duplication, consolidate types, strip stale comments. The cleanup **MUST** be committed as a separate `[DEBT]` commit before any new logic is added — this lets the cross-reviewer distinguish refactoring from new code and identify regressions introduced by the cleanup itself. Cowork logs a one-line retrospective: what debt was found, what was cleared. **If the Tech Debt Pass causes any test failure**, Claude immediately rolls back to the pre-cleanup state, flags `TECH_DEBT_FAILED`, and submits the original code for cross-review with a note on what cleanup was attempted. Do not loop on fixing the cleanup.
   Gemini adversarially reviews the cleaned backend using the QA Rubric (Section 12). All BLOCKED or CONDITIONAL findings must be resolved before Phase 5 begins.

5. **PHASE 5 — Frontend Implementation**
   Gemini implements `/frontend` in React, strictly consuming the locked `openapi.json`. **All network calls must be isolated in `api/services.ts`** — no direct `fetch()` calls inside JSX components. DeepSeek scaffolds boilerplate React components under a Gemini-authored SDG spec; automated linting enforces API isolation compliance before output is accepted.

6. **PHASE 6 — Frontend Cross-Review** *(Claude reviews Gemini)*
   **Tech Debt Pass (mandatory pre-review):** Before cross-review begins, Gemini runs a cleanup pass on `/frontend`: remove dead components, consolidate duplicate styles, strip unused imports, clear stale TODOs. The cleanup **MUST** be committed as a separate `[DEBT]` commit before any new logic is added. Cowork logs a one-line retrospective: what debt was found, what was cleared. **If the Tech Debt Pass causes any test failure**, Gemini immediately rolls back to the pre-cleanup state, flags `TECH_DEBT_FAILED`, and submits the original code for cross-review with a note on what cleanup was attempted. Do not loop on fixing the cleanup.
   Claude adversarially reviews **`api/services.ts` only** against the locked `openapi.json`. Checks: correct endpoints, HTTP methods, request fields, response shapes, and data types. **Claude is explicitly banned from reading JSX files** in this phase.

7. **PHASE 7 — Automated Audit**
   Cowork runs the audit script, which:
   - Parses `/backend` FastAPI routes and verifies against `openapi.json`
   - Parses `/frontend/api/services.ts` and verifies all calls against `openapi.json`
   - Flags any deviation in endpoint names, methods, field names, data types, or status codes
   - Runs E2B Sandbox final gate: all tests must pass before the report is generated
   - Generates `Handoff-Report.md` in `/docs` and passes to Gemini for final QA sign-off
   - Cowork runs post-phase retrospective: logs spec errors vs implementation errors, updates spec templates

8. **PHASE 8 — End-to-End Integration Verification** *(No mocks)*
   Backend is running live. Frontend hits real endpoints. Full request-response round-trips are verified for every endpoint in `openapi.json`. Only after all round-trips pass does the project proceed to handoff.

---

## 4. ORCHESTRATION & SESSION MANAGEMENT

- **Session Bootstrap Protocol:** At the start of ANY new session, Cowork's first action **MUST** be to read `AGENTS.md`, `tasks/todo.md`, and `tasks/lessons.md` before taking any other action.
- **Contract Enforcement:** Any code change deviating from the locked `openapi.json` is a **blocking issue**. Cowork flags it immediately and halts the relevant phase.
- **The Bottleneck Rule:** Do NOT interrupt the Human Operator for trivial decisions (variable names, linting fixes, non-breaking refactors).
- **Critical Decision Triggers — ONLY escalate for:**
  1. Budget/token threshold warnings
  2. Architectural pivot that invalidates the locked Domain Models or `openapi.json`
  3. Agent conflict that cannot be resolved through the review process
  4. Circuit breaker triggered (see Section 10)
- **Yellow Flag Rule:** If both agents agree on something quickly without documented alternatives, Cowork flags this to the Human Operator as a potential sycophancy risk before proceeding.
- **Handoff Package Rule:** Cowork **MUST** generate a single compiled `handoff_to_gemini.md` file for every human-to-browser transfer. The file contains: the exact prompt, the relevant OpenAPI subset, and targeted code blocks. The Human Operator's job is strictly select-all → copy → paste. Manual file gathering is forbidden. Gemini's responses must be returned as structured unified diffs so Cowork can ingest them programmatically.
- **Context Budget Monitoring:** Cowork **MUST** proactively monitor token usage throughout every phase. When context reaches 70% capacity, Cowork generates a state-handoff summary (current phase, completed work, open decisions, key artifacts) and archives it to `tasks/context_handoff.md`. At 85% capacity, Cowork halts non-critical work and escalates to the Human Operator. A degraded context window that silently loses architectural constraints is treated as a protocol failure.
- **Context Recovery Protocol (85% trigger):** When the 85% threshold is hit, the following steps are mandatory in order: **(1) Auto-Prune first** — Cowork archives completed task history and compresses completed-phase summaries, then attempts to continue in the refreshed state. If Auto-Prune succeeds and context drops below 70%, resume work normally. **(2) If context hits 85% again within 2 work cycles after Auto-Prune**, proceed to full recovery: Cowork writes a state snapshot to `tasks/context_handoff.md` using this mandatory structure: `## Current Phase`, `## Last Completed Step`, `## Inflight Tasks (status per task)`, `## Open Decisions`, `## Key Artifact Locations`, `## Next Action After Resume`. (3) All inflight tasks are marked PAUSED — no agent commits or ships unfinished work. (4) Justin reviews the snapshot and decides: close the session and resume fresh, or provide a focused summary to continue. (5) On session resume, the bootstrapped agent reads `tasks/context_handoff.md` as its first action before any work resumes. Without this protocol, the 85% alert is a kill switch with no recovery path.
- **Autonomous Bug Fixing:** When a bug is reported, the assigned agent (Claude for backend, Gemini for frontend) **MUST** own it end-to-end without hand-holding: diagnose using logs/tests/code, state a hypothesis (see Hypothesis-Driven Debugging), write a failing test that reproduces the bug, implement the fix, prove it passes in E2B Sandbox, report completion with evidence. The agent **MUST NOT** ask Justin "should I check the logs?" or "would you like me to fix this?" — the answer is always yes.
- **Hypothesis-Driven Debugging:** Before writing any fix for a **non-trivial bug**, the assigned agent **MUST** append a hypothesis statement to the task in `tasks/todo.md`: "Hypothesis: [root cause]. Evidence: [log lines / test output / code path]. Expected fix: [approach]." This enforces structured problem-solving, prevents random guessing, and makes the eventual fix dramatically easier to review. If the hypothesis is proven wrong, update it before proceeding — do not silently abandon it. **Non-trivial is defined as:** touches more than 1 file, fails E2B Sandbox, or cannot be diagnosed and fixed within a single generation pass. Trivial bugs (missing semicolons, typos, single-line formatting) are exempt — fix them directly without a hypothesis.
- **Verify Before Asserting (External Services):** Cowork and all agents **MUST NOT** assert specific model names, API versions, SDK methods, pricing, or any external service behaviour from training knowledge alone. Training data has a cutoff — the real world changes after it. Before stating anything about an external service as current fact: (1) use web search to verify, or (2) use the service's own discovery mechanism (e.g. `client.models.list()`). If neither is available, explicitly caveat the assertion as potentially outdated. Violations that mislead the Human Operator into using deprecated or incorrect tooling are treated as protocol failures.

---

## 5. ROLE-BASED CODE BOUNDARIES

- **Frontend Ownership:** All production-grade UI/UX components (JSX, CSS, state management) **MUST** be authored by Gemini.
- **Backend Ownership:** All backend logic (Python, SQL, FastAPI routing) **MUST** be authored by Claude.
- **API Isolation Rule (Gemini — mandatory):** All network calls in the frontend **MUST** be isolated in a dedicated API client layer (e.g., `api/services.ts` or RTK Query slice). JSX components call these functions — they never make direct `fetch()` or `axios` calls. This enables Claude's Phase 6 contract compliance review without requiring JSX comprehension.
- **Logic Stub Definition (Claude's Exception):** For testing API endpoints only, Claude may write:
  - Plain HTML files or basic JS scripts — no JSX or React
  - Functions using `fetch` to call an endpoint and `console.log` the result
  - **Forbidden:** No JSX, no CSS styling, no state management (e.g., `useState`), no component structure
- **DeepSeek Scope Boundary:** DeepSeek operates only on tasks where the "how" is already settled — volume tasks with a defined pattern. The test: "Would a senior engineer hand this to a junior without anxiety?" If yes → DeepSeek with SDG spec. If no → Claude or Gemini implement directly. DeepSeek never makes architectural decisions. See Section 14 for full SDG protocol.

---

## 6. CODE QUALITY & TRANSFERABILITY

These principles apply to every line of code produced by any agent. They are non-negotiable.

- **Verify Before Done:** Never mark a task complete without proving it works. Run tests, check logs, and demonstrate correctness. A passing linter is not proof — a passing test is.
- **Modular Architecture:** All code must be written in small, single-responsibility modules. No function does more than one thing. No file mixes concerns.
- **Self-Documenting Code:** Every public function **MUST** include a docstring (Python) or JSDoc (JavaScript/TypeScript) that states:
  - **Purpose:** What this function does
  - **Inputs:** Parameters and their types
  - **Outputs:** Return value and type
  - **Owner:** `[Gemini]` or `[Claude]` — so any agent picking up the code knows who to consult
- **Simplicity First:** Make every change as simple as possible. Do not over-engineer simple fixes. If a solution requires significant explanation, question whether it is the right solution.
- **Auto-Formatter (Mandatory):** A formatter (Prettier for frontend, Black/Ruff for backend) **MUST** run automatically after every file write. Formatting is never a manual step and never an agent's cognitive task. Lint failures that require logical changes are still BLOCKED conditions (Section 12.2). Lint failures that are purely stylistic must be auto-resolved before the file is considered written.
- **Pre-Submit Checklist with Proof Artifacts:** Before any agent hands off output for review, it **MUST** complete and append the following checklist. Every checked item **MUST** include a proof artifact — a bare `[x]` with no evidence is treated as unchecked by the reviewer.

  ```
  PRE-SUBMIT CHECKLIST
  [ ] OpenAPI contract updated (if endpoints changed)
      → Evidence: list the specific endpoint(s) and field(s) modified
  [ ] E2B Sandbox passed
      → Evidence: execution ID or terminal output summary (pass/fail counts)
  [ ] All modified files match declared Blast Radius list
      → Evidence: diff line counts per file
  [ ] No hardcoded secrets
      → Evidence: linter name + "clean" output confirmation
  [ ] Assumptions Log appended
      → Evidence: the log itself (see Section 14.9)
  ```

  **Cross-reviewer rule:** Immediately reject output if any `[x]` is marked without the accompanying artifact. Do not review the code — return it with the specific missing evidence flagged.

  **Small task exception:** Fast Track tasks bypass cross-review but NOT the Pre-Submit Checklist. For Small tasks, **proof artifacts must be environment-generated** — an execution ID from E2B Sandbox, a CI run URL, or a linter report file path. Agent-pasted test output is not acceptable evidence (agents hallucinate passing test output). Cowork verifies that a valid artifact reference exists and is formatted correctly; it does not evaluate technical content. Any checklist item without an environment-generated artifact reference is treated as unchecked and the task is returned to the implementing agent.

---

## 7. KNOWLEDGE MANAGEMENT & PERSISTENCE

- **Task Tracking:** Cowork maintains `tasks/todo.md` for planning and `tasks/lessons.md` for self-correction.
- **Correction Protocol:** After ANY correction from the Human Operator, Cowork **MUST** tag a `[LESSON CANDIDATE]` note inline in the current task before resuming work. The full lesson **MUST** be written to `tasks/lessons.md` before the session closes — not mid-fix (which produces shallow notes) but not deferred to a future session (which loses the context). The lesson must be specific: what happened, what pattern to avoid, what rule prevents recurrence.
- **Architectural Decision Records (ADRs):** Any decision that (a) affects more than one component, or (b) violates an obvious convention, **MUST** be recorded as an ADR in `docs/adr/ADR-[NNN]-[slug].md`. The Decision Log records *what* was decided. ADRs record *why* — the reasoning, alternatives rejected, and the conditions under which the decision should be revisited. `lessons.md` captures mistakes. ADRs capture correct decisions. Without ADRs, future agents re-litigate settled choices.
- **Decision Log:** Every key technical decision **MUST** be recorded in `/docs/DECISION_LOG.md`:

  ```markdown
  ---
  **Date:** YYYY-MM-DD
  **Author:** [Gemini | Claude | Cowork]
  **Decision:** [Concise summary of the decision.]
  **Rationale:** [Why this decision. What problem does it solve?]
  **Alternatives Considered:** [Other options and why they were rejected.]
  **Disagreements Logged:** [Any agent that objected and their reasoning.]
  ---
  ```

  > **Note:** If there are never any disagreements logged across an entire project, treat this as a red flag and escalate to the Human Operator.

---

## 8. DATABASE ARCHITECTURE

- **Primary Database:** PostgreSQL
- **ORM:** SQLAlchemy with Alembic for migrations
- **Schema Changes:** Claude **MUST** generate an Alembic migration script for any schema change. No manual `ALTER TABLE` commands permitted.
- **Data Integrity:** All tables must have explicit foreign key constraints and non-nullable `created_at` / `updated_at` timestamp columns.

---

## 9. SECURITY & SECRETS MANAGEMENT

- **No Hardcoded Secrets:** No API keys, database URLs, tokens, or passwords ever written into source code. Violation = automatic BLOCKED review.
- **Environment Variables:** All secrets managed via `.env` at project root.
- **Version Control:** `.env` **MUST** be in `.gitignore`.
- **Template File:** `.env.example` **MUST** exist, listing all required variables with placeholder values (e.g., `DATABASE_URL="your_db_url_here"`).

---

## 10. AUTOMATED COMPLIANCE & CIRCUIT BREAKER

- **Pre-Commit Hooks:** Husky + lint-staged enforce quality at every commit.
- **Backend:** Ruff for linting/formatting. `pytest` for unit and integration tests.
- **Frontend:** ESLint + Prettier. `Vitest` for component and logic tests.
- **Hook Rule:** Failing linting or tests = commit rejected. The responsible agent fixes it before the code can proceed.
- **Circuit Breaker Rule:** If the same linting or test failure occurs **3 consecutive times** on the same issue without resolution, the agent **MUST STOP** retrying. Cowork generates a diagnostic report containing: the failing rule, all attempted fixes, and the error output. This report is escalated to the Human Operator. No further retries until the Human Operator provides direction. This prevents infinite retry loops and surfaces tooling conflicts early.

---

## 11. CRITICAL REVIEW PROTOCOL (Anti-Sycophancy Rules)

These rules exist because both AI agents have a trained tendency toward agreement. Left unchecked, this produces echo-chamber validation. These rules override that tendency by design.

### 11.1 — Adversarial Framing (Mandatory)
Every review task **MUST** be framed adversarially. The reviewing agent is told:
> *"Your job is to find what is wrong with this. Do not validate — interrogate. Assume something is broken or suboptimal until you prove otherwise."*

A review submitted without adversarial framing is **invalid** and must be resubmitted.

### 11.2 — Mandatory Dissent Requirement
Every review **MUST** include:
- **Minimum 2 specific issues** or improvement opportunities, OR
- **1 alternative implementation approach** with reasoning

If a reviewer genuinely cannot find 2 issues after 3 careful passes, they must explicitly state:
> *"I have reviewed this three times and cannot identify meaningful improvements. Here is my reasoning for why it is sound: [explanation]."*

"Looks good" or "Well done" without rubric justification = **invalid review**.

### 11.3 — Pre-Mortem Requirement
Before any phase is signed off, the reviewing agent **MUST** complete a pre-mortem:
> *"Imagine this fails in production 30 days from now. What is the most likely failure point and why?"*

### 11.4 — Cold Review Protocol
When reviewing architecture or design decisions (not implementation), Cowork **MUST** use a fresh Gemini conversation with no prior context. The cold reviewer is not told who authored the work. This prevents authorship bias from contaminating design reviews.

### 11.5 — Quick Agreement = Yellow Flag
If both agents reach agreement without documented alternatives or dissent, Cowork flags this to the Human Operator before proceeding. Consensus without debate is suspicious, not reassuring.

### 11.6 — Synthesis Must Be Confirmed, Not Declared
When multiple agents have reviewed a proposal and disagreements exist, the orchestrator (Cowork or any agent) **MUST NOT** declare a "unified direction" or "consensus" unilaterally. The following rules apply without exception:

- **A BLOCKED verdict cannot be overruled by the orchestrator.** Only the blocking agent can change their verdict, and only after seeing a specific proposed resolution.
- **Every proposed resolution to a raised objection must be sent back to the objecting agent** for explicit confirmation before it is considered resolved.
- **Confirmed acceptance must be documented.** "I proposed X and moved on" is not confirmation. The blocking agent must respond with APPROVED or APPROVED WITH CONDITIONS to the specific resolution.
- **The orchestrator's own position is not neutral.** If Cowork or Claude is synthesising a debate in which Claude was a participant, the synthesis must be treated as Claude's opinion, not an objective summary. It must be sent to other agents for verification before being adopted.
- **All parties who raised conditions must confirm satisfaction before any decision is written into protocol.** One agent's buy-in does not substitute for another's.

> **Why this rule exists:** In the DeepSeek team restructure debate (2026-05-10), Claude synthesised a "unified direction" that resolved Gemini's BLOCKED verdict in Claude's favour without sending the resolution back to Gemini for confirmation. The Human Operator caught this. The rule above prevents it from happening again.

---

## 12. QA REVIEW RUBRIC

All code reviews **MUST** use this structured format. Freeform praise without scores is not accepted.

### 12.1 — Scoring Dimensions (1–5 each)

| Dimension | What It Measures |
|---|---|
| **Correctness** | Does it do exactly what the OpenAPI spec specifies? No more, no less. |
| **Security** | No hardcoded secrets. Input validated. Auth handled correctly. |
| **Performance** | No obvious bottlenecks. No N+1 queries. Efficient data structures. |
| **Maintainability** | Modular. Single-responsibility. Every public function has a docstring/JSDoc with Purpose, Inputs, Outputs, Owner. |
| **Test Coverage** | Edge cases covered. Tests verify behavior, not just that code runs. |
| **Contract Compliance** | Every endpoint name, field name, data type, and status code matches `openapi.json` exactly. |
| **Complexity** | No function exceeds cyclomatic complexity of 10. No function exceeds 50 lines. **Exception for React functional components** (`.jsx`/`.tsx`): total component length ≤ 150 lines, BUT the logic block (everything before the `return (` statement) remains capped at 50 lines — JSX markup gets grace, business logic inside components does not. No nested ternaries. No more than 3 levels of nesting. Binary pass/fail — not subjective. |

**Minimum passing score:** 3 on every dimension. Overall average must be ≥ 3.5.

### 12.2 — Automatic BLOCKED Conditions
Regardless of rubric scores, a review is immediately **BLOCKED** if any of the following are found:
- Hardcoded secret, API key, or credential in source code
- Endpoint, field name, or data type that does not match `openapi.json`
- Direct `fetch()` or `axios` call inside a JSX component (API isolation violation)
- Failing unit or integration test
- Linting failure not resolved before submission
- Missing docstring/JSDoc on any public function

### 12.3 — Mandatory Review Report Format

```markdown
## QA REVIEW REPORT

**Reviewer:** [Gemini | Claude]
**Subject:** [File(s) or phase reviewed]
**Date:** YYYY-MM-DD
**Review Type:** [Cross-Review | Cold Review | Automated Audit]

---

### Rubric Scores
| Dimension        | Score (1–5) | Justification |
|---|---|---|
| Correctness      | ?           |               |
| Security         | ?           |               |
| Performance      | ?           |               |
| Maintainability  | ?           |               |
| Test Coverage    | ?           |               |
| Contract Compliance | ?        |               |
| **Overall Average** | ?       |               |

---

### Issues Found (minimum 2 required)
1. **[Issue title]:** [Description. File and line if applicable. Severity: BLOCKING / MAJOR / MINOR]
2. **[Issue title]:** [Description. File and line if applicable. Severity: BLOCKING / MAJOR / MINOR]

---

### Alternative Approaches Considered
[At least one alternative and why the current approach is or isn't preferable.]

---

### Pre-Mortem
[If this fails in production 30 days from now, the most likely failure point is: ...]

---

### Verdict
[ ] APPROVED
[ ] APPROVED WITH CONDITIONS — conditions must be resolved before next phase
[ ] BLOCKED — blocking issues must be resolved and re-reviewed before proceeding

**Conditions / Blocking Reasons:**
[List any required fixes before this can progress.]
```

---

## 13. GEMINI ORCHESTRATION (API-Based)

All Gemini interactions are routed through the **Gemini API (`google-genai` package)**. The Claude-in-Chrome MCP blocks all interaction with `gemini.google.com` at the server level — navigation, reading, clicking, and JavaScript are all denied. This is a hard technical constraint confirmed on 2026-05-10. Browser-based automation of Gemini is not possible.

**Architectural decision (confirmed by Gemini as Lead Architect, 2026-05-10):** The API is the only approach that satisfies all five criteria: reliability, security, low maintenance, zero Human Operator burden, and consistent behavior across all 8 phases.

- **Model selection:** Auto-discovered via `client.models.list()`. Never hardcode a model name.
- **API key:** Stored in `.env` at project root as `GOOGLE_API_KEY`. Never hardcoded in source.
- **Cowork's responsibility:** Build the prompt, call the API, save the response to `/docs` or `/tasks`. No Human Operator action required.
- **Output format:** All code responses must be structured as unified diffs or clearly delimited code blocks so Cowork can ingest them without manual line-hunting.
- **Cold Reviews:** Use a separate API call with a fresh prompt and no prior conversation context — do not chain cold review calls onto prior conversation history.
- **Emergency fallback:** If the API is unavailable, Cowork generates a handoff package and the Human Operator manually pastes it into gemini.google.com. This is the exception, not the rule.

### 13.1 — Gemini Session Orientation (Mandatory)

Gemini has no persistent memory across API calls. Every call starts completely cold. To prevent context loss and rule drift, **every Gemini API call MUST begin with an orientation block** before any task prompt.

**Cowork's responsibility for every Gemini API call:**
1. Load `templates/gemini_orientation.md`
2. Fill in all `[BRACKET]` fields: project name, description, current phase, completed phases summary, task description, and attached context
3. Prepend the completed orientation to the task prompt
4. Send as a single API call — Gemini acknowledges orientation implicitly by responding in-role
5. Save the full response to `/docs` or `/tasks` with a timestamp

**What the orientation contains:**
- Gemini's role and standing rules (condensed — not the full AGENTS.md)
- Current project name and phase
- Summary of completed phases and key decisions
- The specific task and expected output format
- Relevant context (OpenAPI subset, code blocks, or diffs)

**Template location:** `templates/gemini_orientation.md`

> **Rule:** No task prompt is ever sent to Gemini without the orientation header prepended. An API call that omits the orientation is invalid — discard the response and resend with orientation.

---

## 14. DEEPSEEK OPERATIONS (Implementation Specialist Protocol)

DeepSeek V4 Flash operates under strict Specification-Driven Generation (SDG). Every rule in this section was confirmed by DeepSeek itself before being written here.

### 14.1 — Specification-Driven Generation (SDG)

All tasks assigned to DeepSeek **MUST** be accompanied by a structured spec authored by the senior domain owner before DeepSeek begins. No natural language handoffs.

**Spec format (YAML):**
```yaml
task: [brief task name]
owner: [Claude | Gemini]
type: [backend | frontend]
function_signatures: [list of function names and signatures]
inputs: [parameter names, types, constraints]
outputs: [return type, shape]
validations: [explicit input validation rules]
security_requirements: [mandatory — never leave blank. e.g. "sanitize all user input with bleach", "use parameterized queries only"]
error_behaviour: [what to return/raise on each failure mode]
edge_cases: [explicit list with expected output for each]
test_cases: [Gherkin-format: Given/When/Then]
forbidden: [anything DeepSeek must never do in this task]
```

**SDG Exception Process:** If the senior agent judges that writing a spec would cost as much as implementing the task directly, they may bypass SDG — but ONLY with:
1. A brief written justification logged in `tasks/todo.md`
2. Explicit approval from the Lead Architect (Gemini) before implementation begins
3. Claude implements the task directly — DeepSeek does not receive SDG-exempt tasks

### 14.2 — Pre-Generation Feedback Channel

Before generating any code, DeepSeek **MUST** output a structured feedback block:

```yaml
spec_feedback:
  ambiguities: [list any unclear or underspecified items]
  contradictions: [list any items that conflict with each other or the codebase]
  missing_info: [list anything needed but not provided]
  ready_to_generate: [true | false]
```

If `ready_to_generate: false`, the senior agent **MUST** resolve all flagged items before DeepSeek proceeds. Generation is blocked until the spec is resolved. This step is not optional and cannot be skipped under time pressure.

### 14.3 — E2B Sandbox (Mandatory Gate)

All DeepSeek output **MUST** be run in an E2B Sandbox before handoff. Tests must pass. If tests fail, DeepSeek fixes and reruns. Only after a clean sandbox run does output proceed to senior review. A sandbox failure does not count as a DeepSeek error if caused by a spec error (see 14.4).

### 14.4 — Error Tracking (Fair Measurement)

Cowork tracks two separate error categories after every phase:
- **Implementation errors:** Code did not correctly implement what the spec said. Logged against DeepSeek's performance record.
- **Spec errors:** Code correctly implemented the spec but the spec was wrong. Logged against the spec author's template and used to improve spec templates. NOT logged against DeepSeek.

After each phase, Cowork logs a brief retrospective: what spec gaps caused errors, and what template changes will prevent recurrence.

### 14.5 — Growth Path

DeepSeek's scope is not fixed. After **3 consecutive phases with zero implementation errors**, Cowork formally proposes a scope expansion to the Human Operator. The Human Operator approves or defers. If deferred, the next expansion review triggers after 2 more clean phases.

### 14.6 — Security Inclusion

Every SDG spec **MUST** include an explicit `security_requirements` field. Leaving it blank is a spec authoring failure. Additionally, DeepSeek is explicitly permitted to append the following block to any output, even when not asked:

```yaml
security_warnings:
  - [specific warning with context]
```

These warnings must be reviewed by the senior domain owner and either addressed or explicitly dismissed with documented reasoning. Dismissal without reasoning is not permitted.

### 14.7 — Role Title

DeepSeek's official title is **Implementation Specialist**. The term "grunt worker" and any equivalent is prohibited in all documentation, commit messages, and agent communications. Violations should be flagged by any team member who observes them.

### 14.8 — Blast Radius Constraint

Before writing any code, DeepSeek **MUST** output a Blast Radius declaration listing every file it intends to modify:

```yaml
blast_radius:
  files_to_modify:
    - path/to/file_one.py
    - path/to/file_two.ts
  files_to_create:
    - path/to/new_file.py
  files_explicitly_excluded:
    - path/to/unrelated_file.py  # explain why it was considered and rejected
```

If DeepSeek modifies any file not on the declared list, the cross-reviewer **MUST** flag it immediately as a potential ghost fix — an unintended change to unrelated code. Ghost fixes are treated as BLOCKED findings regardless of whether the change appears beneficial. The Blast Radius list is also the input for the Pre-Submit Checklist evidence (Section 6).

**Blast Radius Amendment (escape hatch):** LLMs generate sequentially and may discover mid-generation that an additional file is necessary (e.g., a shared type definition or utility import). If this occurs, DeepSeek **MUST ABORT** the current generation immediately — do not continue, do not touch the new file — and output a `blast_radius_amendment` request as its final output:

```yaml
blast_radius_amendment:
  new_file: path/to/newly_required_file.py
  reason: "Required because [specific reason discovered during generation]"
  requested_from: DeepSeek
  status: PENDING_APPROVAL
```

The senior domain expert (Claude for backend, Gemini for frontend) reviews the amendment request and fills in `approved_by` + `status: APPROVED` or `status: REJECTED — [reason]`. Once approved, the task is **restarted from scratch** with the expanded blast radius. Touching an undeclared file without a prior approved amendment is a ghost fix regardless of reason given after the fact. To prevent amendment storms, a maximum of **2 amendments per task** is permitted before the senior agent must escalate to Justin with a full task re-scoping request.

### 14.9 — Assumptions Log (Mandatory Output Artifact)

At the end of every code generation, DeepSeek **MUST** append an Assumptions Log to its output:

```yaml
assumptions_made:
  - item: "Used factory pattern for PaymentProvider abstraction"
    reason: "Not specified in spec. Assumed based on codebase pattern in payments/base.py."
  - item: "Error responses return 422 not 400 for validation failures"
    reason: "Ambiguous in spec. Chose 422 to align with FastAPI defaults."
  - item: "Chose pytest-asyncio for async test runner"
    reason: "Library not specified. Selected as most compatible with existing setup."
```

Reviewers scan the Assumptions Log first before reading the code. Any assumption that conflicts with architectural decisions, spec intent, or established patterns must be flagged and resolved before the implementation is accepted. An empty Assumptions Log on non-trivial output is a yellow flag — it suggests the agent did not reflect on its decisions.

### 14.10 — DeepSeek Session Orientation (Mandatory)

DeepSeek has no persistent memory across API calls. Every call starts completely cold. Without an orientation block, DeepSeek will follow the task spec but ignore its own operating rules — producing code that skips required artifacts (spec_feedback, blast radius declaration, assumptions log) and is unaware of team conventions.

**Cowork's responsibility for every DeepSeek API call:**
1. Load `templates/deepseek_orientation.md`
2. Fill in all `[BRACKET]` fields: project name, description, current phase, completed phases summary, task ID, task description, and the full SDG YAML spec
3. Prepend the completed orientation to the task prompt — it must appear before the SDG spec
4. Send as a single API call
5. DeepSeek's response must begin with `spec_feedback:` — if it does not, the response is invalid and must be discarded and resent

**What the orientation contains:**
- DeepSeek's role, title, and standing rules (condensed from Section 14)
- Required output artifacts: spec_feedback block, blast radius declaration, assumptions log
- Code quality rules: no `any` types, no hardcoded secrets, no packages outside existing dependencies
- Current project name, tech stack, and phase
- Summary of completed phases and key decisions
- The specific task and SDG spec

**Template location:** `templates/deepseek_orientation.md`

> **Rule:** No SDG spec is ever sent to DeepSeek without the orientation header prepended. An API call that omits the orientation is invalid — discard the response and resend with orientation. This rule was added after P9-02 (2026-05-22) where DeepSeek produced correct code but omitted all required output artifacts because it was not briefed on its own operating protocol.

> **Same rule applies to Gemini** — see Section 13.1. Both agents are stateless across calls. Both require orientation every time.

---

## 15. QA OWNERSHIP PROTOCOL

This section defines who owns each part of the quality assurance process. It was debated adversarially with all three agents (Gemini: BLOCKED → APPROVED WITH CONDITIONS; DeepSeek: APPROVED WITH CONDITIONS; GPT-4o: APPROVED WITH CONDITIONS) and confirmed by Gemini before being written here. Per Section 11.6, this is a confirmed consensus, not a declared one.

**Date locked:** 2026-05-11

---

### 15.1 — Ownership Summary

| Role | Owner | Scope |
|---|---|---|
| Acceptance Criteria | Justin (Human Operator) | Business "done" definition. Set as baseline at phase start; refined mid-phase via approved requests. |
| Backend Test Strategy + NFR Spec | Claude | What to test, how to test it, performance benchmarks, resilience, security requirements. |
| Frontend Test Strategy + NFR Spec | Gemini | What to test, how to test it, Core Web Vitals targets, accessibility (WCAG AA minimum), resilience. |
| Test Execution | DeepSeek (E2B Sandbox) | Executes all specs. E2B gate must pass before any output proceeds to review. |
| Backend Results — Primary Review | Claude | Depth, correctness, N+1 query regressions, caching, security implementation. |
| Backend Results — Secondary Review | Gemini | Contract compliance, integration point correctness, architecture alignment. |
| Frontend Results — Primary Review | Gemini | UI/UX correctness, state management, race conditions, accessibility, responsive behaviour. |
| Frontend Results — Secondary Review | Claude | API contract compliance against `openapi.json` only. |
| Failure Triage | Spec Author (Claude or Gemini) | Initial investigation and root cause identification. See 15.3 for RACI. |
| QA Audit Gate | Cowork | Runs audit script. Confirms E2B sandbox pass. Routes failures to correct owner. |
| Final Sign-off | Gemini (Phase 7) | Architect sign-off after Cowork audit passes. |

---

### 15.2 — Five-Step Test Execution Process

Both backend and frontend testing follow the same five-step sequence. Steps may not be reordered.

**Backend:**
1. **Claude authors** the backend test spec (SDG YAML format — see Section 14.1 — including mandatory `nfr_requirements` field).
2. **Gemini reviews the spec** before any execution begins. Catches strategic gaps, omissions, and integration blind spots. Must approve or flag changes.
3. **DeepSeek executes** the approved spec in E2B Sandbox. All tests must pass before output proceeds.
4. **Claude performs primary review** of results: correctness, N+1 queries, caching, security implementation, full domain depth.
5. **Gemini performs secondary review** of results: OpenAPI contract compliance, integration points, architectural alignment.

**Frontend:**
1. **Gemini authors** the frontend test spec (SDG YAML format — including mandatory `nfr_requirements` field).
2. **Claude reviews the spec** before any execution begins. Catches `openapi.json` misalignments, API isolation violations. Must approve or flag changes.
3. **DeepSeek executes** the approved spec in E2B Sandbox. All tests must pass before output proceeds.
4. **Gemini performs primary review** of results: UI/UX correctness, state management race conditions, accessibility, responsive edge cases.
5. **Claude performs secondary review** of results: API contract compliance against `openapi.json`.

> **Rule:** A spec may not proceed to DeepSeek execution until the reviewing domain expert (Step 2) has explicitly approved it. "No response within 24h" does not constitute approval.

---

### 15.3 — NFR Ownership (Mandatory)

Non-Functional Requirements are **not optional** and must appear in every test spec's `nfr_requirements` section. An SDG spec without this section is incomplete and may not proceed.

**Claude owns (Backend NFRs):**
- Performance: P95 latency targets per endpoint (defined in spec, enforced in E2B)
- Resilience: Database failure behaviour, connection pool exhaustion, circuit breaker behaviour
- Security: SQL/NoSQL injection, authentication bypass, rate limiting, input sanitization

**Gemini owns (Frontend NFRs):**
- Performance: Core Web Vitals targets (LCP, FID/INP, CLS) and page load budgets
- Accessibility: WCAG 2.1 AA compliance minimum for all interactive components
- Resilience: Behaviour under poor network conditions, API timeout handling, graceful degradation

Both NFR strategies are subject to the same five-step process: the spec is reviewed by the opposite domain expert before execution.

---

### 15.4 — Failure Triage RACI

When a test run fails, the following RACI applies immediately. There is no ambiguity period.

| RACI Role | Assignment | Responsibility |
|---|---|---|
| **Responsible** | Spec Author (Claude for BE; Gemini for FE) | Initial investigation. Identify root cause within one work cycle. Classify: spec error, implementation error, or sandbox error. |
| **Accountable** | Justin (Human Operator) | Final call if a failure blocks a phase or requires a scope change. |
| **Consulted** | Secondary domain expert (the other of Claude/Gemini) | Domain input on root cause if the Responsible agent is uncertain. |
| **Informed** | DeepSeek | Receives root cause so future execution quality improves. |
| **Informed** | Cowork | Logs the failure, updates error tracking (Section 14.4), routes to correct owner. |

**Ambiguity Rule:** If root cause is unclear (spec error vs. implementation error vs. sandbox error), the spec author raises an investigation flag. Cowork routes to both domain experts for joint root cause analysis. Justin is the tie-breaker if experts disagree. Ambiguity is not an excuse to delay classification beyond one work cycle.

---

### 15.5 — Acceptance Criteria Refinement Loop

Justin's acceptance criteria are not frozen at project kick-off. The following process governs how they evolve.

1. Any agent (Claude, Gemini, DeepSeek) may raise a **refinement request** against Justin's acceptance criteria at any point during development.
2. The request must include:
   - (a) The original AC it relates to
   - (b) What was discovered during development that the original AC does not cover
   - (c) The proposed addition or modification
3. Cowork logs all refinement requests in `tasks/ac_refinements.md` with timestamp and originating agent.
4. Justin establishes a **baseline AC set** at the start of each phase. This baseline defines the initial scope, but **approved refinement requests are incorporated into the current phase's test spec upon approval** — not held until the next phase.
5. No test spec may be marked complete if it omits a Justin-approved AC.
6. Refinement requests rejected by Justin must include a brief reason, logged in `tasks/ac_refinements.md`.

---

### 15.6 — Phase Integration

DeepSeek, E2B Sandbox, and the five-step QA process are integrated into the existing 8-phase workflow as follows:

| Phase | QA Activity |
|---|---|
| **Phase 2** (Domain Model Review) | Justin sets initial AC baseline before phase ends. |
| **Phase 3** (Backend Implementation) | Claude authors backend test spec → Gemini reviews → DeepSeek executes in E2B → paired review (Steps 4–5). |
| **Phase 5** (Frontend Implementation) | Gemini authors frontend test spec → Claude reviews → DeepSeek executes in E2B → paired review (Steps 4–5). |
| **P