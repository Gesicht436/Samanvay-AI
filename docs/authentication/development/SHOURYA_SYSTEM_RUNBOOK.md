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

Do NOT independently introduce:

* Google Login
* a new OIDC implementation
* a new JWT authentication architecture
* bearer tokens or localStorage/sessionStorage authentication credentials
* another identity provider

unless the project architecture is explicitly changed.

The implemented conceptual flow is:

```text
Organizational username + password
            ↓
Samanvay-AI authentication endpoint (local bcrypt verification today)
            ↓
Samanvay-AI server-side Application Session
            ↓
Authorization / RBAC / CPSE Scope
```

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

