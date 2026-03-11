# Aura Implementation Issues (Execution Backlog)

Status: Aligned with GitHub issues in `shailwx/aura` as of 2026-03-11.

## Current Gaps Summary

- Core protocols are mocked (UCP discovery, BMS compliance, AP2 settlement).
- Compliance blocking relies heavily on prompt behavior instead of hard runtime guards.
- Kubernetes deployment manifest references tool server resources that are not defined.
- Session state is in-memory only, so state is lost on restart and cannot scale horizontally.
- API has no authentication/authorization layer for enterprise use.
- Observability, resilience, and CI/CD quality gates are minimal.

## GitHub Alignment Snapshot (2026-03-11)

| Backlog Issue | Existing GitHub Issue(s) | Alignment | Action |
| :--- | :--- | :--- | :--- |
| Issue 1 (Tool server resources) | #1 | Partial overlap | Keep #1, expand scope to include ToolServer/MCP wiring (not just Agent CRDs). |
| Issue 2 (Deterministic compliance gate) | None | Missing | Create new GitHub issue. |
| Issue 3 (Structured intent parsing) | None | Missing | Create new GitHub issue. |
| Issue 4 (Real UCP/BMS/AP2 adapters) | None | Missing | Create new GitHub issue. |
| Issue 5 (API authn/authz) | None | Missing | Create new GitHub issue. |
| Issue 6 (Durable sessions) | None | Missing | Create new GitHub issue. |
| Issue 7 (Retries/timeouts/circuit breaker) | None | Missing | Create new GitHub issue. |
| Issue 8 (Observability) | None | Missing | Create new GitHub issue. |
| Issue 9 (E2E + contract tests) | #2, #3, #4, #5, #6 | Strong overlap | Keep existing issues; reduce duplicate wording in new tickets and add contract/API test scope to #2 or a new test-epic issue. |
| Issue 10 (Prod hardening) | #7, #8 | Partial overlap | Keep #7/#8 and add secrets/env/release/rollback scope in follow-up issues. |

## Overlaps and Conflicts

### Overlaps (safe)

- Backlog Issue 9 overlaps with GitHub #2-#5 (agent/tool tests) and #6 (CI). This is complementary.
- Backlog Issue 10 overlaps with #7 (CD) and #8 (PR governance), but backlog has broader operational scope.

### Conflicts / Misalignment

- **Scope gap in #1:** GitHub #1 focuses on Agent CRDs and currently misses the `aura-tool-server` dependency needed by `kagent.yaml` tool wiring.
- **Demo milestone risk:** #6 is targeted for "Demo Day" while key runtime safety work (Issue 2) has no GitHub ticket yet.
- **Test granularity drift:** Existing test issues are mostly unit-level, while production readiness needs API/E2E and contract-level tests.
- **Command mismatch risk:** Some issue text uses `kagent apply`; docs currently standardize on `kubectl apply -f kagent.yaml` for manifest deployment.

### Recommended Consolidation

- Update GitHub #1 title/body to include ToolServer/MCP wiring and readiness checks.
- Create 7 new GitHub issues for backlog Issues 2-8 (currently uncovered).
- Convert Issue 9 into a test epic linked to #2-#6 and add explicit API + contract test checklists.
- Keep #7 dependent on #6 and additionally on Issue 1 + Issue 2 (safety gate) before automated deploy.

---

## Issue 1 — Deployment Blocker: Define and Deploy Tool Server Resources

**GitHub:** #1 (partial)

**Priority:** P0  
**Why:** `kagent.yaml` references `aura-tool-server` but no ToolServer resource/service is declared.

**Scope**
- Add required Kagent/MCP ToolServer resource definitions.
- Ensure Scout/Sentinel/Closer can resolve tool endpoints in-cluster.
- Add deployment validation steps.

**Implementation Tasks**
- [ ] Add tool server manifest(s) to Kubernetes config.
- [ ] Wire each tool name to the running tool server.
- [ ] Add namespace/service account/rbac settings if required by cluster policy.
- [ ] Validate with `kubectl get` and a smoke run.

**Acceptance Criteria**
- `kubectl apply -f kagent.yaml` succeeds without unresolved resource references.
- All agents report ready state and can call tools at runtime.

---

## Issue 2 — Compliance Safety: Enforce Deterministic Runtime Gate

**GitHub:** Missing

**Priority:** P0  
**Why:** The current block behavior is instruction-driven; payment safety should be code-enforced.

**Scope**
- Add explicit guard logic so settlement cannot proceed when any vendor is rejected.
- Add structured handoff payload from Sentinel to Closer.

**Implementation Tasks**
- [ ] Define typed sentinel output schema (approved/rejected vendors, blocked flag).
- [ ] Make Closer consume structured sentinel output only.
- [ ] Hard-fail settlement if `blocked=true` or compliance hash missing.
- [ ] Add tests proving no payment path executes after rejection.

**Acceptance Criteria**
- Compliance rejection blocks settlement in code, independent of model wording.
- Regression tests cover blocked and approved paths.

---

## Issue 3 — Intent Parsing: Add Structured Procurement Request Extraction

**GitHub:** Missing

**Priority:** P1  
**Why:** Quantity/product/budget are not reliably extracted into typed fields.

**Scope**
- Introduce a procurement request schema and parser.
- Ensure downstream tools use structured inputs (not freeform text assumptions).

**Implementation Tasks**
- [ ] Create Pydantic model for procurement intent.
- [ ] Parse message into `{product, quantity, budget, currency, constraints}`.
- [ ] Add fallback clarifying prompts when required fields are missing.
- [ ] Update pipeline to pass parsed fields explicitly.

**Acceptance Criteria**
- Pipeline consistently computes amount from parsed quantity and chosen vendor price.
- Invalid or incomplete requests produce clear corrective responses.

---

## Issue 4 — Integrations: Replace Mocks with Adapter Interfaces

**GitHub:** Missing

**Priority:** P1  
**Why:** Production functionality requires external APIs, but code is currently mock-only.

**Scope**
- Add provider interfaces for UCP, BMS, and AP2.
- Keep mock providers for local/test mode.

**Implementation Tasks**
- [ ] Define adapter interfaces and response contracts.
- [ ] Implement HTTP-based UCP client.
- [ ] Implement authenticated BMS compliance client.
- [ ] Implement AP2 settlement client with request signing.
- [ ] Add environment flag to switch mock/real providers.

**Acceptance Criteria**
- Service runs in `mock` and `real` integration modes.
- Integration errors are surfaced with actionable messages and retry behavior.

---

## Issue 5 — Security: Add API Authentication and Authorization

**GitHub:** Missing

**Priority:** P1  
**Why:** `/run` is currently unauthenticated.

**Scope**
- Add authn/authz middleware for API endpoints.
- Propagate caller identity through session and audit fields.

**Implementation Tasks**
- [ ] Add JWT/OIDC validation dependency for FastAPI routes.
- [ ] Enforce role-based access (procurement runner vs admin).
- [ ] Add request identity fields to run context.
- [ ] Add tests for unauthorized and forbidden responses.

**Acceptance Criteria**
- Unauthorized requests are rejected.
- Authorized requests include identity metadata in logs/audit records.

---

## Issue 6 — State Management: Replace InMemory Sessions with Durable Store

**GitHub:** Missing

**Priority:** P1  
**Why:** In-memory sessions prevent reliable scale-out and recovery.

**Scope**
- Introduce durable session backend (for example Redis or Cloud SQL).
- Add session TTL and cleanup policy.

**Implementation Tasks**
- [ ] Implement session service abstraction.
- [ ] Add Redis-backed session implementation.
- [ ] Add migration/config for local and cloud environments.
- [ ] Validate multi-instance behavior.

**Acceptance Criteria**
- Sessions persist across process restarts.
- Concurrent workers share session state correctly.

---

## Issue 7 — Reliability: Timeouts, Retries, and Circuit Breaking

**GitHub:** Missing

**Priority:** P2  
**Why:** External integrations need resilience controls.

**Scope**
- Add per-integration timeout and retry policies.
- Add circuit breaker for repeated downstream failures.

**Implementation Tasks**
- [ ] Configure HTTP client defaults (timeout, retries, backoff).
- [ ] Add circuit breaker wrapper for BMS/AP2 calls.
- [ ] Add idempotency key handling for settlement requests.
- [ ] Add failure-path tests.

**Acceptance Criteria**
- Transient failures recover automatically.
- Repeated hard failures degrade gracefully without duplicate settlements.

---

## Issue 8 — Observability: Structured Logging, Metrics, and Tracing

**GitHub:** Missing

**Priority:** P2  
**Why:** Production operation requires diagnosable traces across agent steps.

**Scope**
- Add correlation IDs and structured logs.
- Publish latency/error metrics and distributed traces.

**Implementation Tasks**
- [ ] Add request correlation ID middleware.
- [ ] Add structured log schema for each pipeline stage.
- [ ] Export metrics (success/failure, stage latency, tool errors).
- [ ] Add tracing instrumentation and dashboards.

**Acceptance Criteria**
- A single request can be traced across Architect, Scout, Sentinel, and Closer.
- SLO-oriented metrics are visible for operations.

---

## Issue 9 — Testing: End-to-End and Contract Test Coverage

**GitHub:** #2, #3, #4, #5, #6 (partial)

**Priority:** P2  
**Why:** Current tests mainly validate tool functions, not runtime orchestration/API contracts.

**Scope**
- Add API-level and pipeline-level tests.
- Add contract tests for external provider adapters.

**Implementation Tasks**
- [ ] Add FastAPI endpoint tests (`/run`, `/run/stream`, `/health`).
- [ ] Add end-to-end happy and blocked flows with deterministic fixtures.
- [ ] Add contract tests for UCP/BMS/AP2 clients.
- [ ] Add CI workflow to run lint, type-check, and tests.

**Acceptance Criteria**
- CI blocks merges on failing tests.
- Critical procurement/compliance behavior is covered end to end.

---

## Issue 10 — Production Hardening: Config, Secrets, and Release Process

**GitHub:** #7, #8 (partial)

**Priority:** P3  
**Why:** Operational readiness needs secure config and repeatable releases.

**Scope**
- Standardize environment profiles and secret handling.
- Add release/versioning and rollback runbook.

**Implementation Tasks**
- [ ] Add environment profiles (local/dev/staging/prod).
- [ ] Move sensitive config to secret manager/Kubernetes secrets.
- [ ] Add image tagging strategy and release notes template.
- [ ] Add rollback playbook and on-call runbook.

**Acceptance Criteria**
- Deployments are repeatable and reversible.
- No credentials are stored in repo or plain env files.

---

## Recommended Execution Order

1. Issue 1
2. Issue 2
3. Issue 3
4. Issue 4
5. Issue 5
6. Issue 6
7. Issue 7
8. Issue 8
9. Issue 9
10. Issue 10

## Definition of Done (Project-Level)

- Real (non-mock) integration mode validated in staging.
- Compliance block is deterministic and test-covered.
- Authenticated API and durable sessions are enabled.
- Kagent deployment succeeds with all agents healthy.
- CI/CD and observability are in place for safe releases.