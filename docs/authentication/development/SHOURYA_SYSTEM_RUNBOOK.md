# Shourya — System & Development Runbook

**Project:** Samanvay-AI / BharatCodex
**Developer:** Shourya Mishra
**Primary Environment:** Windows + PowerShell
**Repository:** `C:\Users\HP\Samanvay-AI`

---

## 1. Purpose

This document records the local development environment, known system limitations, recurring errors, and the correct execution procedure for work on Samanvay-AI.

The purpose is to prevent repeated environment mistakes, unnecessary setup attempts, wasted coding-agent tokens, and incorrect conclusions about implementation status.

Before performing implementation, testing, debugging, or verification work, the relevant sections of this document MUST be considered.

---

# 2. System Environment

## Operating System

* Windows
* Primary shell: PowerShell

## User Environment

```text
User profile:
C:\Users\HP
```

## Repository

```text
C:\Users\HP\Samanvay-AI
```

## Python

```text
Python 3.13
```

The project uses a Python virtual environment for Samanvay-AI.

Typical environment:

```text
(samanvay-ai)
```

The environment should be activated before running project Python commands.

## C/C++ Toolchain

MinGW is installed at:

```text
C:\mingw64\bin\g++.exe
```

This is available when native compilation is required.

## Conda / Jupyter

Installed development tooling includes:

* Anaconda
* JupyterLab
* Python development tooling

These should not be introduced into a task unless the task actually requires them.

---

# 3. Primary Development Rules

The following rules apply to coding-agent work on this machine.

### Rule 1 — Inspect before modifying

Do not immediately implement.

First inspect:

* relevant file
* relevant function/class
* existing helper
* existing tests
* current git status/diff when relevant

Only inspect the minimum required scope.

### Rule 2 — Reuse existing project utilities

Before creating a new helper, dependency, schema, or mechanism:

1. Search the relevant module.
2. Check existing utilities.
3. Reuse existing project conventions.

Do not introduce a new implementation when an existing project mechanism already performs the required job.

### Rule 3 — Do not install dependencies unnecessarily

Do not install:

* new Python packages
* new authentication libraries
* new database software
* new security libraries
* new tooling

unless the task explicitly requires it and the existing project cannot satisfy the requirement.

### Rule 4 — Do not perform broad refactoring

A bounded task means a bounded change.

Do not:

* redesign unrelated modules
* rename unrelated functions
* reorganize the repository
* rewrite existing security architecture
* clean up unrelated code
* update unrelated documentation

---

# 4. Database Environment

## PostgreSQL Status

The local PostgreSQL server is currently unavailable.

Known result:

```text
connection to server at "localhost" (::1),
port 5432 failed:
Connection refused
(0x0000274D/10061)
```

Therefore:

```text
localhost:5432
```

must NOT be assumed to have a running PostgreSQL server.

## Important Rule

Do NOT automatically:

* install PostgreSQL
* start PostgreSQL
* create a database
* modify database configuration
* create migrations
* change the project's database architecture

merely because a test requires PostgreSQL.

If database availability is not part of the current task, leave the environment unchanged.

If a test genuinely requires PostgreSQL and the server is unavailable:

```text
REPORT TEST AS BLOCKED BY DATABASE AVAILABILITY
```

Do not claim that the test passed.

Do not fake a test result.

---

# 5. Correct Database Diagnostic

If database connectivity must be verified, use a minimal diagnostic.

Expected failure in the current environment:

```text
localhost:5432 → Connection refused
```

The important distinction is:

```text
Implementation problem
        ≠
Database environment unavailable
```

A connection-refused error alone does NOT prove that the application implementation is incorrect.

---

# 6. PowerShell Rules

PowerShell is the primary shell.

Commands must be written using valid PowerShell syntax.

Do not repeatedly attempt malformed shell commands.

When a command becomes complex, prefer:

1. a simple PowerShell command,
2. a temporary script only when genuinely necessary,
3. removal of the temporary script afterward.

Do not leave diagnostic scripts or temporary files in the repository.

---

# 7. Temporary Files

Temporary diagnostic files may be created only when required.

Examples:

```text
test_db_check.py
debug_*.py
tmp_*.py
```

After use:

1. verify the diagnostic is complete,
2. remove the temporary file,
3. check `git status`,
4. confirm no unintended repository change remains.

Temporary diagnostics must never become accidental project files.

---

# 8. Git Safety

Before implementation:

```text
Check git status.
```

After implementation:

```text
Check git diff.
Check git status.
```

The agent must report:

* files intentionally modified
* files unexpectedly modified
* temporary files
* generated files
* unexpected configuration changes

Do not commit or push unless explicitly requested.

---

# 9. Correct Work Sequence

For any bounded Samanvay-AI task, follow this order.

```text
1. Read task specification
        ↓
2. Identify exact allowed files
        ↓
3. Inspect relevant symbols
        ↓
4. Inspect existing utilities/helpers
        ↓
5. Inspect relevant tests
        ↓
6. Check environment only if required
        ↓
7. Implement minimum required change
        ↓
8. Inspect git diff
        ↓
9. Run focused tests
        ↓
10. Separate implementation result from environment failures
        ↓
11. Report final status
```

Do NOT begin with:

```text
Full repository audit
```

unless the task explicitly requires it.

---

# 10. Coding-Agent Token Protection

Coding agents have limited model/tool budgets.

Therefore every task should be tightly bounded.

The agent should:

* inspect only relevant files
* search only relevant symbols
* avoid dumping entire files
* avoid broad repository scans
* avoid repeated searches
* avoid repeated database diagnostics
* avoid speculative architecture changes
* avoid unnecessary tests
* avoid unrelated cleanup

The agent should stop investigating once sufficient evidence exists.

---

# 11. Authentication Architecture Constraint

The implemented authentication model is organizational username/password with a server-side session cookie.

Verification currently runs against the local account store using bcrypt. The repository has NO implemented external identity provider or organizational credential integration: there is no LDAP, Active Directory, OIDC, SAML, directory, or federation integration in the codebase.

Rules for future agents:

1. Do not assume an external identity provider exists. It does not.
2. Do not invent LDAP, Active Directory, OIDC, SAML, Google OAuth, directory, or federation integration.
3. The credential-authority direction is already decided: **External Organizational Authority / Federation** — Samanvay must not become the authoritative organizational password store (`docs/authentication/10_DECISIONS.md` D-CRED-1). However, the exact provider/protocol is not yet selected — **OPEN ARCHITECTURE DECISION**. Agents MUST NOT invent LDAP, Active Directory, OIDC, SAML, Kerberos, REST, or another identity integration. Until the integration contract is formally specified, preserve the current local-bcrypt implementation and do not implement an external provider.
4. Follow the currently implemented session-cookie authentication: `POST /auth/login` → server-side `AuthSession` → hashed session secret → HttpOnly session cookie (`__Host-samanvay_session` in production) → CSRF-protected unsafe requests.
5. Read this runbook before performing any authentication work.
6. Describe the local bcrypt verification only as the **prototype credential authority**, **development/demo authentication**, or **local prototype credential verification**. Never describe it as an organizational identity provider, an organizational credential integration, or the production CPSE identity architecture. In a real organizational deployment, credential verification is expected to be delegated to the organization-approved identity infrastructure; the exact provider/protocol is deployment-specific and unresolved (`docs/authentication/10_DECISIONS.md` D-CRED-1).

Do NOT independently introduce:

* Google Login
* a new OIDC implementation
* a new JWT authentication architecture
* bearer tokens or localStorage/sessionStorage authentication credentials
* another identity provider

unless the project architecture is explicitly changed.

The submitted prototype's implemented conceptual flow (prototype credential authority — development/demo authentication):

```text
username + password
        ↓
prototype credential verification
        ↓
account-state checks
        ↓
Samanvay AuthSession
        ↓
__Host-samanvay_session
```

The real organizational deployment flow (target direction; exact provider/protocol deployment-specific and unresolved):

```text
organizational username + password
        ↓
organization-approved credential authority
        ↓
successful identity/authentication handoff
        ↓
Samanvay AuthSession
        ↓
__Host-samanvay_session
```

The local prototype credential verification is NOT the organization's authoritative credential store and is NOT the production CPSE identity architecture. The external authority owns organizational credential verification and password lifecycle; Samanvay owns application session management, authorization, RBAC, CPSE/resource boundaries, CSRF protection, application security events, session revocation, and application-level account-state enforcement where applicable. The session architecture is identical in both flows and is unchanged.

Authentication architecture must not be redesigned during unrelated authorization tasks.

---

# 12. Authentication/Security Work Rules

For authentication and authorization tasks:

Do not modify unrelated:

* RBAC
* CPSE isolation
* session architecture
* CSRF semantics
* workflow semantics
* audit architecture
* database schema

unless explicitly included in the task.

Security telemetry should observe security decisions rather than change those decisions.

---

# 13. Security Telemetry Convention

The canonical authorization-failure event is:

```text
AUTHORIZATION_FAILURE
```

When adding telemetry:

* use the existing event mechanism
* use existing helper functions
* use `success=False`
* record the server-side actor identity where available
* use existing reason/action conventions
* never record passwords
* never record session tokens
* never record authentication secrets

Do not create a second telemetry mechanism when the existing security-event infrastructure is sufficient.

---

# 14. Existing Authorization Telemetry

The following already have canonical authorization-failure telemetry:

```text
require_permission
require_any_permission
```

Do not duplicate their telemetry.

If a task involves them, first verify existing behavior before modifying anything.

---

# 15. Known Authentication/Security Implementation Areas

The security work has already covered authorization boundaries including:

```text
Requisition
Inventory
Ingest
Graph
Matching
Audit
Account administration
Provisioning
Document reads
Frontend session authentication
CSRF protection
Security telemetry
```

Before implementing a new security task, inspect the existing implementation first.

Do not assume that an older audit finding is still unresolved.

The current repository implementation is authoritative.

---

# 16. Known Recurring Error — Database Connection

### Error

```text
OperationalError
psycopg2.OperationalError

connection to server at "localhost" (::1),
port 5432 failed:
Connection refused
```

### Meaning

The local PostgreSQL service is unavailable.

### Correct response

```text
Do not modify application code solely because of this.
Do not fake test results.
Report the test as environment-blocked.
```

Only address PostgreSQL if database setup is explicitly part of the task.

---

# 17. Known Recurring Error — Malformed PowerShell Commands

Previous work encountered repeated PowerShell command syntax/quoting problems.

### Prevention

Use simple commands.

Prefer:

```powershell
git status
git diff
Get-Content <file>
Select-String -Path <file> -Pattern "<pattern>"
```

over unnecessarily complex nested shell commands.

If a command fails because of shell syntax, fix the command before drawing any conclusion about the project.

A shell syntax failure is NOT an application implementation failure.

---

# 18. Known Recurring Error — Agent Runs Out of Model Limit

A previous implementation attempt consumed the available coding-agent model budget before completing verification.

### Prevention

For implementation tasks:

```text
Discovery
→ Minimal implementation
→ Diff inspection
→ Focused tests
→ Final report
```

Do not combine:

```text
Full security audit
+
Architecture redesign
+
Implementation
+
Database setup
+
Full test suite
```

into one task.

Split work into bounded phases.

---

# 19. Known Recurring Error — Claiming Completion Without Verification

An agent must NOT report:

```text
Implementation complete
```

merely because code was edited.

Completion requires evidence.

At minimum:

```text
Git diff inspected
Relevant files verified
Focused tests attempted
Environment limitations reported
```

If testing is blocked:

```text
IMPLEMENTATION STATUS: complete / requires review
TEST STATUS: blocked by environment
```

Do not combine the two into a false "all verified" statement.

---

## Known Recurring Error — Runbook Path Mismatch

### Issue

The runbook is located under:

```text
docs/authentication/development/SHOURYA_SYSTEM_RUNBOOK.md
```

not:

```text
docs/development/SHOURYA_SYSTEM_RUNBOOK.md
```

The previously referenced path `docs/development/SHOURYA_SYSTEM_RUNBOOK.md` does not exist.

### Prevention

Coding agents must read the actual path `docs/authentication/development/SHOURYA_SYSTEM_RUNBOOK.md` before beginning Samanvay-AI work.

---

## Known Recurring Error — AUTH-TELEMETRY Implementation Defects

### A. Missing helper import

Lesson: when adding an existing helper call, verify the helper is imported before claiming implementation completion.

### B. Dependency-scope error

Lesson: never reference a FastAPI dependency variable such as `db` at route/dependency factory definition time unless it is actually in lexical scope; inspect the existing dependency pattern first.

### C. User object vs user_id mismatch

Lesson: verify helper parameter types against the actual call-site value. An integer ID must not be passed where an object with `.id` is expected.

### D. Constant name vs constant value

Lesson: when using policy reason constants, inspect the actual constant value and pass that value rather than inventing/prefixing a string.

### E. Telemetry must not change authorization semantics

Lesson: instrumentation changes must preserve the original authorization guard, permission requirement, and response behavior.

---

## Known Recurring Error — Task 17 Tooling: Shell-Integration Capture Failure and Malformed PowerShell

### Issue A — shell-integration output capture failure and stray artifact file

During Task 17, the initial `git status --short` output could not be captured through shell integration ("output could not be captured through shell integration ... command may still be running"). The command was re-run later and its output verified normally. In the same session window an untracked stray file named `tatus --short` (a colored `git diff --stat` capture, evidently a redirect/typo artifact) appeared in the repository root. Task 17 issued no command containing output redirection; the file remains untracked, is not referenced by any document or code, was not committed, and is reported in the Task 17 final report rather than deleted because its origin is uncertain.

### Issue B — malformed PowerShell one-liner

A single-line byte-inspection command constructed during Task 17 contained invalid nested ternary syntax and failed with `ParserError: Missing ')' in method call`. A simpler byte-scan loop was used instead and succeeded. A later `git show --stat | Select-Object -First 3` reported exit code 1 only because `-First 3` closed the pipeline early; the required output had already been captured.

### Prevention

* Prefer simple PowerShell commands (Section 17); avoid clever one-liners.
* When shell integration reports uncaptured output, re-run the command and verify results before drawing conclusions.
* Never rely on output-redirect artifacts; do not commit stray files.
* Treat pipeline-stop exit codes from `Select-Object -First N` as non-failures when the required output was already obtained.

---

## Known Recurring Error — Task 18 Session Lifecycle Verification

### Issue A — Task 18 WIP found in `git stash`, not on the working tree

At resume, `git status --short` was clean and the Task 18 files
(`tests/unit/test_session_security.py`,
`tests/api/test_session_lifecycle.py`, plus the implementation delta in
`backend/app/services/auth_session_service.py`,
`backend/app/api/dependencies.py`, `backend/app/api/routers/auth.py`)
were absent from the working tree but present as
`stash@{0}` ("WIP: Task 18 session lifecycle hardening"). The same files
were referenced by stale `.pytest_cache` entries and orphaned
`__pycache__` bytecode, which confirmed they had been executed before but
never committed. No work was redone: the stash was popped and the
untracked test files restored from the stash state, then verification
continued from the checkpoint.

Bare `stash@{0}` references fail under PowerShell (brace expansion splits
the argument: "Too many revisions specified: 'stash@' ..."). Quote the
ref (`'stash@{0}'`).

### Issue B — legacy-route API test initially failed on FastAPI's own docs scaffolding

`test_no_legacy_authentication_routes_registered` initially asserted that
no registered route path matches `(oauth|oidc|google|sso|saml|jwks|/token)`
and failed only because FastAPI registers its built-in
`/docs/oauth2-redirect` Swagger-UI redirect route. That route is framework
documentation scaffolding: it authenticates nothing, registers no OAuth
flow, and disappears in production where docs are disabled (D-5J.3-4).
The security boundary was NOT weakened to make the test pass — the test
explicitly allowlists exactly that one framework route while still failing
on any real legacy authentication endpoint.

### Issue C — PostgreSQL-dependent session lifecycle tests are BLOCKED

The DB-backed session lifecycle tests (`test_successful_authentication_...`,
`test_login_response_cookie_attributes`,
`test_raw_session_secret_is_never_stored_in_database`) error at the
application-lifespan fixture with
`psycopg2.OperationalError: connection to server at "localhost", port 5432
failed: Connection refused`. Per Sections 4, 16 and 22 these are reported
as BLOCKED by database availability, never as PASS or as implementation
failures. The DB-free properties (15/15 unit primitives plus the 6 static
API checks: missing-cookie 401, Bearer-is-not-auth, legacy-route audit,
backend/frontend machinery audit, no dependency overrides) were executed
and passed in this environment; the remaining end-to-end properties hold
only via the committed test definitions plus code inspection until a
database is available.

### Prevention

* Check `git stash list` when a checkpoint claims work exists but the tree
  is clean; never re-implement before looking there.
* Do not confuse FastAPI's built-in `/docs/oauth2-redirect` with an
  authentication route.
* Report DB-dependent session tests as BLOCKED while PostgreSQL is
  unavailable; do not fake their results.

---

## Known Recurring Error — Task 19 CSRF + Origin Enforcement

### Approved decision — `POST /match/search` is a protected POST

The Task 19 audit found `POST /api/v1/match/search`
(`backend/app/api/routers/match.py::search_matches`) was the only
mutating-route decorator without `require_csrf` (19/20 covered). The
project owner approved treating it as an authenticated protected POST
under the existing strict-Origin + session-bound-token policy — no
read-only exemption merely because the response looks read-shaped, and
no change to token construction, Origin semantics, cookie/session
design, CORS, or error vocabulary.

### Changes made

* `backend/app/api/routers/match.py`: added the existing
  `_csrf: AuthSession = Depends(require_csrf)` dependency to
  `search_matches` (import + parameter, following the inventory /
  requisition / ingest / audit pattern). No handler, service, permission,
  or tenant logic changed. No unrelated routes or frontend files touched.
* `tests/unit/test_csrf_origin.py` (new, 15 tests, DB-free): HMAC token
  construction vs an independently computed `hmac.new(...)` expectation;
  token verify matrix (valid / wrong / cross-session / missing / empty /
  whitespace / non-string / malformed stored hash); Origin matrix (exact
  allowlist hit / missing / malformed / untrusted / suffix-spoof /
  trailing-slash contract); `require_csrf` ordering through the real
  dependency with stub request/session/DB doubles (Origin-denied → 403
  before token validation; token-denied → 403 with the handler never
  reached); route-wiring assertion that `match/search` declares
  `require_csrf`.

### Test outcomes (actual)

* `python -m pytest tests/unit/test_csrf_origin.py -q` → **15 passed**.
* `python -m pytest tests/unit/test_session_security.py
  tests/unit/test_security.py -q` → **19 passed** (Task 18 regression
  intact).
* DB-free lifecycle subset (6 checks) → **6 passed**; DB-free auth
  regression (seed-users / me-unauthorized / retired-seed) →
  **3 passed**.
* DB-backed CSRF acceptance/rejection over HTTP (real token issuance →
  protected mutation → 403-negative cases) remains **BLOCKED**:
  PostgreSQL unavailable at `localhost:5432` (Runbook sections 4, 16,
  22). Not executed, never claimed as PASS.

### Implementation notes

* No genuine implementation errors were encountered. The new test file
  was written in three editor calls only because a single write exceeded
  the editor payload limit; the intermediate state briefly dropped one
  test, which was restored before any test run — no test was ever run
  against the partial file.
* `require_csrf` is called directly (not via FastAPI injection) in the
  ordering tests, so its `Depends(...)` defaults are bypassed by passing
  explicit stub doubles — the real function body, including both 403
  branches and telemetry staging, is what executes.

---

# 20. Test Reporting Convention

Every test report should distinguish:

### PASS

The test actually executed and passed.

### FAIL

The test actually executed and failed.

### BLOCKED

The test could not execute because of an environment dependency.

### NOT RUN

The test was intentionally not executed.

Never convert:

```text
BLOCKED
```

into:

```text
PASS
```

---

# 21. Focused Testing Rule

For a bounded code change, run the smallest relevant test set first.

Preferred:

```text
Targeted test
        ↓
Related regression test
        ↓
Broader test suite only if necessary
```

Do not automatically run the entire repository test suite for every small change.

---

# 22. Test Environment Limitation

If PostgreSQL is unavailable and the relevant tests require database access:

```text
Focused test execution may be blocked.
```

The correct final report should explicitly state:

```text
Test execution blocked because PostgreSQL is unavailable at localhost:5432.
No database setup was performed.
```

---


## Task 20 — Migration Infrastructure Recovery

### Audit findings
* `backend/alembic/baseline_schema.py` previously lacked `BASELINE_REVISION` and
  `BASELINE_TABLES`, causing an import error in `tests/unit/test_migration_integrity.py`.
  **Resolved:** added `BASELINE_REVISION = "0001"` and `BASELINE_TABLES` (12 tables in
  teardown-safe order, matching `reversed(list(Base.metadata.sorted_tables))`).
* `backend/app/services/schema_verification.py` previously had an IndentationError around
  line 444. A syntax check subsequently passed; the file was verified for duplicated or
  overlapping code regions and none found. **No change required.**
* `scripts/generate_baseline_schema.py` appeared to contain potentially duplicated code.
  Syntax check passed and the generator was reviewed in full; no functional defect found —
  the `header`/`body`/`footer` string-splitting is intentional and produces the frozen
  baseline correctly. **No change required.**

### Files modified (Task 20)
* `backend/alembic/baseline_schema.py` (added baseline identity + table list)
* `backend/alembic/versions/0001_baseline.py` (new, baseline migration)
* `backend/alembic/env.py` (new)
* `backend/alembic/__init__.py` (new)
* `backend/app/services/schema_verification.py` (new)
* `scripts/adopt_schema.py` (new)
* `scripts/generate_baseline_schema.py` (new)
* `tests/unit/test_migration_integrity.py` (new)

### Test outcomes (actual)
* `python -m pytest tests/unit/test_migration_integrity.py -q` → **BLOCKED**:
  `ModuleNotFoundError: No module named 'pydantic_settings'` at import time
  (`backend/app/models/base.py` → `backend/app/core/config.py` → `pydantic_settings.BaseSettings`).
  Not executed, never claimed as PASS or FAIL.
* DB-free auth regression tests (`tests/unit/test_csrf_origin.py`,
  `tests/unit/test_session_security.py`, `tests/unit/test_security.py`) → **BLOCKED**:
  `ModuleNotFoundError: No module named 'fastapi'` at import time. Not executed, never
  claimed as PASS or FAIL.

### Outstanding PostgreSQL-dependent verification
* Live PostgreSQL schema verification (`scripts/adopt_schema.py --dry-run`, `--stamp`)
  is BLOCKED because PostgreSQL is unavailable at `localhost:5432`.
* Production startup verification (`verify_schema_version`) is BLOCKED for the same reason.
* These remain BLOCKED; only the DB-free static checks (syntax, import of baseline module,
  AST-based migration-chain inspection) are available.

### Completion pass (Task 20, October 2026) — verified findings

#### Symptom A — eight failing tests, reproducible
`python -m pytest tests/unit/test_migration_integrity.py -q` → **8 failed,
20 passed**. The three `verify_*_fails_closed` tests reported
"DID NOT RAISE RuntimeError"; four `test_adopt_*` tests returned exit 3 with
`psycopg2.OperationalError ... Connection refused`; the idempotent-stamp test
reported `connect` called twice.

#### Root cause A (established)
* The three verify tests set rows attributes on the object returned by
  `_fake_engine()` — the **engine** mock — while the inner **connection**
  mock kept its default `[("0001",)]`, so verification legitimately saw a
  matching revision and did not raise. The implementation was proven correct
  for all three cases by supplying rows through `_fake_engine(rows=...)`.
* The four adopt tests patched `sqlalchemy.inspect` and
  `adopt_schema.actual_from_inspector` but never patched
  `adopt_schema.engine`, so `_verify()` used the real module-level engine
  and attempted a live connection to `localhost:5432`.
* The idempotent-stamp test (i) asserted `connect.assert_called_once()`
  although the design performs two read-only connects (verify + stamp
  pre-check), and (ii) configured fake rows via `fetchall.return_value`
  although `_alembic_version_rows` iterates the Result directly
  (a MagicMock `__iter__` defaults to empty), so the fake reported "not
  stamped" and the stamp proceeded to `begin()`.

#### Resolution A (verified)
`tests/unit/test_migration_integrity.py`: rows now supplied via
`_fake_engine(rows=...)`; every `main()`-invoking adopt test patches both
`adopt_schema.engine` and `adopt_schema.inspect`; the fake result implements
`fetchall()` and `__iter__()`; connect-count assertions assert the verified
two-read flow while write safety is asserted by `_assert_no_writes()`
(a statement-class scan of every `execute()` call) plus `engine.begin`
assertions. Result: **35 passed** (28 original + 7 new), no assertion was
weakened to obtain the result.

#### Symptom B — live dry-run could never match (code-level defect)
`schema_verification.py` documents a `pg_index` query in
`scripts/adopt_schema.py` that did not exist, so on a live database every
index predicate would be `UNVERIFIABLE` and `_compare_table` would report a
difference for all 23 indexes even on an exactly matching schema.

#### Root cause B (established)
`_verify()` never supplied `index_predicates`, and SQLAlchemy's Inspector
does not expose partial-index predicates.

#### Resolution B (verified with fake connections)
`scripts/adopt_schema.py` now runs a read-only
`SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname =
current_schema()` and extracts predicates with `predicate_from_indexdef()`
(anchor on `) WHERE`, normalize via `check_tokens`, balance via `_balanced`).
No WHERE clause → verified `None` (ordinary non-partial index); empty or
unbalanced predicate → `ValueError` → adoption aborts exit 3 with no write;
missing entry → stays `UNVERIFIABLE` → exit 1. Tests cover matching partial
index, predicate mismatch, missing entry, unparseable definition, and the
plain non-partial index — all DB-free.

#### Preventive instructions
* When faking an engine for code that uses a module-level binding, patch the
  binding the code actually uses (`adopt_schema.engine`,
  `adopt_schema.inspect`); patching `sqlalchemy.inspect` only affects
  modules that import `inspect` **inside** the function.
* Configure BOTH `fetchall()` and `__iter__()` on fake SQLAlchemy results;
  production code may iterate a Result directly.
* **TIMESTAMP symmetry:** a reflected PostgreSQL column type renders through
  `str()` as bare `'TIMESTAMP'` for both tz and naive spellings, and the
  expected-side baseline parser also produces `'TIMESTAMP'` for
  `TIMESTAMP WITH TIME ZONE` — the two sides must stay equal. Do not
  "normalize" only one side (e.g. changing the parser to emit `TIMESTAMPTZ`)
  or every datetime column will mismatch on a live database.
* `pg_indexes.tablename` is the **table** name, not the schema name.

#### Test outcomes (completion pass, actual)
* `python -m pytest tests/unit/test_migration_integrity.py -q` → **35 passed**
  (plus one benign Alembic `path_separator` DeprecationWarning originating
  from `backend/alembic.ini`; the config was left untouched).
* `python -m pytest tests/unit/test_csrf_origin.py
  tests/unit/test_session_security.py tests/unit/test_security.py -q` →
  **34 passed** (Task 18/19 regression intact).
* Offline `ScriptDirectory` head check → `heads == ['0001']`, one revision.
* Baseline regeneration check → 35/35 statements and the table order are
  identical to the frozen `baseline_schema.py`.
* Still BLOCKED: anything requiring live PostgreSQL (unchanged from above).

---

## Task 21 — Frontend Authentication Cutover (Steps 1–2)

### Audit findings (Step 1, read-only)
* Commit `175e4ae` ("auth: harden frontend session auth UX (AUTH-006)")
  deleted the `export function PublicNavbar() {` /
  `export function LandingAuthCTA() {` wrapper lines while adding the
  `isProductionBuild` signup gating, leaving `useAuth()` and the top-level
  `return` outside any function — a hard compile error in modules imported
  by `AppShell`/root `page.tsx`, so the entire frontend failed to build.
* The same commit added `router.push('/login')` to `Sidebar.tsx` and
  `UserHeaderBadge.tsx` without `const router = useRouter();` ("Cannot
  find name 'router'").
* `Sidebar.tsx` logout catch was empty (silent failure) although its
  `logoutError` state existed; `UserHeaderBadge` already surfaced it.
* `api.seedUsers()` targeted the retired `POST /auth/seed` route (404)
  and had zero call sites.
* No mid-session 401 handling existed: a session revoked/expired after
  page load left a stale in-memory identity and CSRF token until reload.
* Verified already aligned (no change needed): login/me/csrf/logout
  request-response shapes, cookie-only identity, `credentials:'include'`,
  CSRF acquisition + `X-CSRF-Token` transmission, ProtectedRoute
  loading/authenticated/unauthenticated states, signup retirement,
  production gating of seed/persona surfaces.

### Changes made (Step 2 — 6 files, frontend only)
* `frontend/src/components/PublicNavbar.tsx`,
  `frontend/src/components/LandingAuthCTA.tsx`: restored the deleted
  component wrapper lines; the `isProductionBuild` const and the
  `{!isProductionBuild && ...}` signup gating are kept intact.
* `frontend/src/components/Sidebar.tsx`: added
  `const router = useRouter();`; logout catch now calls
  `setLogoutError('Failed to sign out. Please try again.')`, matching
  `UserHeaderBadge` behavior.
* `frontend/src/components/UserHeaderBadge.tsx`: added
  `const router = useRouter();`.
* `frontend/src/lib/api.ts`: removed the dead `seedUsers()` method
  (provisioning methods `getUsers`/`approveUser`/`rejectUser` untouched);
  added module-level `setUnauthorizedHandler` registration and a 401
  notification in `fetchAPI` that fires for every 401 EXCEPT
  `POST /auth/login` (the login 401 is a credential error owned by the
  login flow). 403 CSRF/Origin failures and network errors never trigger
  it; handler exceptions are swallowed so they cannot mask the API error.
* `frontend/src/context/AuthContext.tsx`: `AuthProvider` registers
  `clearIdentity` through `setUnauthorizedHandler` (and unregisters on
  unmount), clearing stale identity + CSRF token on any mid-session 401.
  The handler is idempotent (safe under concurrent 401s) and performs no
  navigation (no redirect loops); `ProtectedRoute` then renders the
  unauthenticated state. Startup restore, login and logout semantics are
  unchanged.
* No backend, migration, schema, dependency, lockfile or configuration
  change; no package installed; no service started.

### Test outcomes (actual)
* `python -m pytest tests/unit/test_csrf_origin.py
  tests/unit/test_session_security.py tests/unit/test_security.py -q`
  → **34 passed** (Task 18/19 regression intact).
* `tests/api/test_session_lifecycle.py` DB-free static subset
  (missing-cookie 401, Bearer-is-not-auth, legacy-route audit,
  backend/frontend JWT-Bearer machinery audit, no dependency overrides)
  → **6 passed, 3 deselected**.
* `tests/api/test_signup_api.py` → **2 passed** (public signup retired).
* `tests/api/test_auth_api.py` static subset (seed-users,
  me-unauthorized, seed-route-retired) → **3 passed, 4 deselected**.
* DB-backed lifecycle/auth tests (`test_successful_authentication_...`,
  `test_login_response_cookie_attributes`,
  `test_raw_session_secret_is_never_stored_in_database`, the lifespan
  auth tests) → **BLOCKED**: `psycopg2.OperationalError ... Connection
  refused` at `localhost:5432` (Sections 4/16/22). Never claimed PASS;
  no database setup performed.
* Frontend `tsc --noEmit` / `next build` → **BLOCKED**: `node_modules` is
  absent and installing dependencies is out of task scope. Substitute
  structural scan over `frontend/src` (every `router.` use has a
  `const router = useRouter`; every `useAuth()` consumer is an exported
  component) → clean; the previously broken files parse per manual
  diff review.

### Error encountered and resolution (shell, Task 17 recurring class)
* One pytest invocation was mangled by shell integration: the
  `.venv\Scripts\python.exe` path lost its leading dot (invoked as
  `venv\Scripts\python.exe` → "The module 'venv' could not be loaded")
  and the output was not captured. Resolution: re-ran with the quoted
  call operator `& '.\.venv\Scripts\python.exe' -m pytest ...`; the
  command completed and the real results are reported above. No
  application conclusion was drawn from the shell failure.

---

## Task 22 — Legacy JWT/OIDC Removal Verification (Steps 1–2)

### Audit findings (Step 1, read-only)
* **F1 — dead code:** `get_optional_user` in `backend/app/api/dependencies.py`
  was a JWT-era leftover. Its implementation had already been migrated to
  the session cookie (fail-closed: absent cookie -> `None`; presented
  malformed/expired/revoked/inactive -> 401 + cookie clear), so it was NOT
  an authentication weakness — but it had **zero callers** in routers,
  tests, scripts, ML/graph code, or the frontend.
* **F2 — stale documentation:** four in-tree READMEs still described the
  pre-migration system as current: `backend/app/api/README.md` (Bearer
  JWT mermaid flow, `HTTPAuthorizationCredentials`/`jwt_secret_key`/HS256,
  `get_optional_user`, `X-CPSE-ID`-derived tenancy),
  `backend/app/api/routers/README.md` (JWT-issuing login, `POST /auth/signup`,
  `POST /auth/seed`, seed-users "with the default password"),
  `backend/app/README.md` (JWT in mermaid/Security/directory comments), and
  `frontend/README.md` (one-click persona "JWT Bearer token injection",
  "AuthContext JWT storage", `/signup` JWT issuance, `PUT /admin/users`).
* Harmless/verified-clean (no action, recorded not to re-flag): all
  executable surfaces (backend `*.py`, frontend `src`, scripts, deps,
  env/docker config) contain no JWT/OIDC/Bearer machinery; `.kilo/`
  worktrees hold old code but are untracked, unreachable, and excluded
  from Docker images by COPY scoping; `architecture.md`/`context.md`/
  `MATCH_ENDPOINT_AUDIT_REPORT.md`/`docs/authentication/*` are historical
  or migration records; `/docs/oauth2-redirect` is FastAPI scaffolding
  (known false positive, section 21-era note).
* Out-of-approved-scope observation (reported, NOT edited):
  `backend/app/core/README.md` still documents `jwt_secret_key`,
  `jwt_algorithm`, `jwt_access_token_expire_minutes`,
  `create_access_token`/`decode_access_token` — none of which exist in
  `backend/app/core/security.py` or `config.py`. Candidate for a future
  docs-only task.

### Changes made (Step 2 — 6 approved files)
* `backend/app/api/dependencies.py`: removed the unused `get_optional_user`
  function only. Pre-edit grep across backend/tests/scripts/ml/graph/
  frontend confirmed the definition was the sole reference; post-edit
  import check confirms the module loads and the symbol is gone. No imports
  orphaned (`Request`, `settings`, `Optional`, `session_service` all still
  used by remaining functions); `get_current_session`, `get_current_user`,
  session validation, cookie-clearing, `require_permission`,
  `require_any_permission`, `require_csrf`, `validate_idempotency_key`,
  `verify_cpse_access`, and `require_roles` untouched.
* `backend/app/api/README.md`: intro wording; mermaid request-lifecycle
  flow rewritten to the session-cookie + CSRF + permission model; section B
  now documents `get_current_session`/`get_current_user` and states no
  optional-auth helper exists; section C documents `require_permission`,
  legacy `require_roles`, and `require_csrf` with the real 403 error codes;
  section E documents session-derived `verify_cpse_access` (X-CPSE-ID never
  establishes tenant authority); auth router row updated (logout/csrf/
  provisioning endpoints; signup retired).
* `backend/app/api/routers/README.md`: section A rewritten — session-cookie
  login (generic 401, rate-limited), CSRF-protected idempotent logout,
  cookie-only `/me`, session-bound `/csrf`, credential-free `seed-users`
  (404 in production), `SYSTEM_ADMIN` listing, `ACCOUNT_PROVISION`/
  `ACCOUNT_APPROVE`/`ACCOUNT_REJECT` + CSRF operations, and explicit 404
  status of `/auth/signup` and `/auth/seed`. Permission identifiers
  verified against `auth.py:316,331,404,433` before writing.
* `backend/app/README.md`: five JWT references replaced (mermaid Security
  label, api-layer header description, `security.py` description, and the
  directory-layout comments for `dependencies.py`/`auth.py`/`security.py`/
  schemas `auth.py`).
* `frontend/README.md`: persona-hub paragraph rewritten (username prefill
  only, operator-typed password, hidden in production, HttpOnly session
  cookie, memory-only identity, `/auth/me` restore, CSRF on unsafe
  requests); directory comments for `login/`, `signup/`, `AuthContext.tsx`;
  route table rows for `/login`, `/signup` (retired), and `/admin/users`
  (corrected to `GET /auth/users`, `POST /auth/users/{id}/approve|reject`).
* `docs/authentication/development/SHOURYA_SYSTEM_RUNBOOK.md`: this entry.
* No router, model, migration, dependency, lockfile, env, or Docker file
  changed; no package installed; no service started; no `.kilo/`,
  `architecture.md`, `context.md`, `MATCH_ENDPOINT_AUDIT_REPORT.md`, or
  `docs/authentication/*` design record touched.


# 23. Git Verification Checklist

After every implementation:

```text
[ ] git status checked
[ ] git diff checked
[ ] only expected files changed
[ ] no temporary files remain
[ ] no debug files remain
[ ] no unexpected dependency changes
[ ] no unexpected configuration changes
```

---

# 24. Final Agent Report Format

For bounded implementation tasks, the agent should report:

```text
### IMPLEMENTATION STATUS

[Completed / Partial / Issue Found]

### MODIFIED FILES

[List only actually modified files]

### TEST STATUS

[Passed / Failed / Blocked / Not Run]

### ENVIRONMENT ISSUES

[Only actual environment issues]

### SECURITY / REGRESSION CHECK

[Pass / Fail]

### REMAINING ACTION

[Exact next action]
```

Do not provide a long unrelated repository summary.

---

# 25. Golden Rule

The most important operational rule for this environment is:

> **Do not change the project to compensate for an environment problem unless the environment change is explicitly part of the task.**

And:

> **Do not treat an environment failure, shell error, or unavailable database as evidence that the application implementation is wrong.**

Every future coding task should separate:

```text
APPLICATION CODE
ENVIRONMENT
TEST EXECUTION
ARCHITECTURE
```

and report them independently.

---

# 26. Quick Pre-Flight Checklist

Before starting a new coding-agent task:

```text
[ ] Read the exact task
[ ] Identify allowed files
[ ] Check git status
[ ] Inspect existing implementation
[ ] Inspect existing helpers
[ ] Inspect relevant tests
[ ] Confirm whether DB is actually required
[ ] Do not start/install PostgreSQL automatically
[ ] Do not introduce new dependencies unnecessarily
[ ] Implement only requested scope
[ ] Inspect diff
[ ] Run focused tests
[ ] Distinguish PASS / FAIL / BLOCKED
[ ] Check git status again
[ ] Report exact next action
```

---

## Document Status

**Purpose:** Local development and execution guardrail
**Scope:** Shourya's Samanvay-AI development environment
**Authority:** Operational guidance; does not override frozen project architecture or security contracts
**Last updated:** October 2026

