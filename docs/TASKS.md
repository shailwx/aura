# Aura — Task Board

**Updated:** 2026-03-13  
**Linked roadmap:** [ROADMAP.md](ROADMAP.md)  
**GitHub:** `shailwx/aura`

---

## How to Use This Board

Tasks are grouped by milestone and priority. Each task maps to a GitHub issue where one exists.
Sub-tasks are immediately actionable engineering steps.

Priority: **P0** (blocking) → **P1** (high) → **P2** (medium) → **P3** (low)

---

## Milestone 1 — Safety & Deployment Foundation

### Task 1.1 — Kagent Tool Server Resources `P0` · GitHub #1

**Goal:** `kubectl apply -f deploy/kagent.yaml` deploys cleanly with no unresolved references.

| # | Sub-task | Owner | Status |
|---|---|---|---|
| 1.1.1 | Audit `deploy/kagent.yaml` for all `toolRef` / `mcpServer` references | — | 🔲 |
| 1.1.2 | Add `ToolServer` CRD resource for `aura-tool-server` | — | 🔲 |
| 1.1.3 | Wire `discover_vendors`, `verify_vendor_compliance`, `generate_intent_mandate`, `settle_cart_mandate` to MCP endpoints | — | 🔲 |
| 1.1.4 | Add `ServiceAccount`, `ClusterRoleBinding`, namespace RBAC | — | 🔲 |
| 1.1.5 | Run `kubectl apply --dry-run=server -f deploy/kagent.yaml` — zero errors | — | 🔲 |
| 1.1.6 | Smoke test: `kubectl get agents -n aura` all show `READY=True` | — | 🔲 |

**Acceptance criteria:** All agents reach ready state; no unresolved resource references.

---

### Task 1.2 — Deterministic Compliance Gate `P0` · GitHub (new)

**Goal:** Payment settlement is impossible if any vendor fails KYC/AML — enforced in code, not in the LLM prompt.

| # | Sub-task | Owner | Status |
|---|---|---|---|
| 1.2.1 | Define `SentinelOutput` Pydantic model: `blocked: bool`, `approved_vendors: list[str]`, `rejected_vendors: list[str]`, `compliance_hashes: dict[str, str]` | — | ✅ |
| 1.2.2 | Update `sentinel.py` to write `SentinelOutput` to session state as structured JSON | — | ✅ |
| 1.2.3 | Add guard in `closer.py`: deserialise `SentinelOutput`; raise if `blocked=True` before any tool call | — | ✅ |
| 1.2.4 | Write regression test: assert `settle_cart_mandate` is never called when Sentinel sets `blocked=True` | — | ✅ |
| 1.2.5 | Write regression test: assert Closer proceeds normally when all vendors are approved | — | ✅ |
| 1.2.6 | Update [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) §6.1 to mark code-based gate as ✅ | — | ✅ |

**Acceptance criteria:** Compliance rejection blocks settlement in code regardless of LLM output wording.

---

## Milestone 2 — Structured Parsing & Protocol Adapters

### Task 2.1 — Structured Intent Parsing `P1` · GitHub (new)

**Goal:** Architect emits a typed `ProcurementIntent` before delegating to the pipeline.

| # | Sub-task | Owner | Status |
|---|---|---|---|
| 2.1.1 | Create `tools/intent_parser.py` with `ProcurementIntent` Pydantic model | — | ✅ |
| 2.1.2 | Fields: `product: str`, `quantity: int`, `budget_usd: float \| None`, `currency: str = "USD"`, `constraints: list[str]` | — | ✅ |
| 2.1.3 | Add `parse_procurement_intent(message: str) -> ProcurementIntent` using Gemini structured output | — | ✅ |
| 2.1.4 | Update `architect.py` system prompt to extract and write `ProcurementIntent` to session state | — | ✅ |
| 2.1.5 | Update `governor.py` to read `ProcurementIntent` from session state | — | ✅ |
| 2.1.6 | Add clarification fallback when `product` or `quantity` is missing | — | ✅ |
| 2.1.7 | Add unit tests for `parse_procurement_intent` — happy path, missing fields, edge cases | — | ✅ |

**Acceptance criteria:** Pipeline consistently derives `amount_usd = quantity × unit_price` from parsed intent.

---

### Task 2.2 — Real Protocol Adapters `P1` · GitHub (new)

**Goal:** Replace mock implementations with live HTTP adapters; retain mock fallback.

| # | Sub-task | Owner | Status |
|---|---|---|---|
| 2.2.1 | Add `AURA_MOCK_PROTOCOLS` env flag — when `true`, all tools use mock data | — | 🔲 |
| 2.2.2 | Implement `UcpClient` with live `/.well-known/ucp` endpoint calls | — | 🔲 |
| 2.2.3 | Implement `BmsClient` for real KYC/AML API or certified test sandbox | — | 🔲 |
| 2.2.4 | Implement `Ap2Client` with W3C Verifiable Credential signing and AP2 gateway submission | — | 🔲 |
| 2.2.5 | Update tool functions to delegate to client classes based on env flag | — | 🔲 |
| 2.2.6 | Add contract tests validating live adapter response shapes match existing schemas | — | 🔲 |

---

## Milestone 3 — Security & Durability

### Task 3.1 — API Authentication / Authorisation `P1` · GitHub (new)

**Goal:** All portal and pipeline endpoints require a valid JWT with an appropriate role claim.

| # | Sub-task | Owner | Status |
|---|---|---|---|
| 3.1.1 | Add `python-jose` or `authlib` dependency | — | ✅ |
| 3.1.2 | Implement `verify_jwt(token)` FastAPI dependency | — | ✅ |
| 3.1.3 | Define roles: `procurement_user`, `finance_approver`, `compliance_officer`, `admin` | — | ✅ |
| 3.1.4 | Apply role guards to all `/api/portal/*` routes | — | 🔲 |
| 3.1.5 | Protect `/run` and `/run/stream` with `procurement_user` minimum | — | ✅ |
| 3.1.6 | Write auth integration tests (valid token, expired token, wrong role) | — | ✅ |
| 3.1.7 | Document auth flow in [API_REFERENCE.md](API_REFERENCE.md) | — | 🔲 |

---

### Task 3.2 — Durable Session State `P2` · GitHub (new)

**Goal:** ADK session state persists across container restarts and scales horizontally.

| # | Sub-task | Owner | Status |
|---|---|---|---|
| 3.2.1 | Evaluate Redis vs Cloud Firestore as `SessionService` backend | — | ✅ |
| 3.2.2 | Implement custom `SessionService` adapter for chosen backend | — | ✅ |
| 3.2.3 | Update `main.py` to inject session service from env config | — | ✅ |
| 3.2.4 | Add session TTL configuration (default: 1 hour) | — | 🔲 |
| 3.2.5 | Load-test with 10 concurrent pipeline invocations | — | 🔲 |

---

## Milestone 4 — Observability & Resilience

### Task 4.1 — Retries, Timeouts, and Circuit Breakers `P2` · GitHub (new)

**Goal:** All external tool calls are wrapped with retry + timeout + circuit-breaker.

| # | Sub-task | Owner | Status |
|---|---|---|---|
| 4.1.1 | Apply `execute_with_retries` to `discover_vendors` UCP HTTP call | — | ✅ |
| 4.1.2 | Apply to `verify_vendor_compliance` BMS call | — | ✅ |
| 4.1.3 | Apply to `settle_cart_mandate` AP2 call | — | ✅ |
| 4.1.4 | Set per-tool timeout budgets: UCP=3s, BMS=2s, AP2=5s | — | ✅ |
| 4.1.5 | Expose circuit-breaker status (`open`/`closed`) in `/health` response | — | 🔲 |

---

### Task 4.2 — Observability `P2` · GitHub (new)

**Goal:** Structured logs, distributed traces, and Prometheus metrics are emitted from every agent and tool.

| # | Sub-task | Owner | Status |
|---|---|---|---|
| 4.2.1 | Replace `print` / bare `logging` calls with structlog structured logger | — | ✅ |
| 4.2.2 | Add OpenTelemetry SDK; trace spans for each agent invocation | — | 🔲 |
| 4.2.3 | Add trace spans for each tool function call | — | 🔲 |
| 4.2.4 | Expose Prometheus metrics: `aura_requests_total`, `aura_latency_seconds`, `aura_circuit_breaker_trips_total` | — | ✅ |
| 4.2.5 | Create Grafana dashboard JSON template | — | 🔲 |

---

## Milestone 5 — Production Hardening & CI/CD

### Task 5.1 — E2E and Contract Tests `P1` · GitHub #2–6

**Goal:** Automated test suite covers happy path, blocked path, all API endpoints, and protocol schemas.

| # | Sub-task | Owner | Status |
|---|---|---|---|
| 5.1.1 | Write E2E test: full pipeline run via real ADK `Runner` (happy path) | — | ✅ |
| 5.1.2 | Write E2E test: ShadowHardware blocked path — assert no settlement ID returned | — | ✅ |
| 5.1.3 | Write API integration tests for all 16 portal endpoints | — | ✅ |
| 5.1.4 | Write contract tests: verify `discover_vendors` output matches `VendorEndpoint` schema | — | ✅ |
| 5.1.5 | Write contract tests: verify AP2 mandate structure matches `IntentMandate` schema | — | ✅ |
| 5.1.6 | Set coverage gate ≥ 90% in CI | — | 🔲 |

---

### Task 5.2 — Production Hardening `P2` · GitHub #7, #8

**Goal:** Automated CD pipeline, secrets management, and documented runbook.

| # | Sub-task | Owner | Status |
|---|---|---|---|
| 5.2.1 | Migrate all GCP credentials to Kubernetes Secrets + Workload Identity | — | 🔲 |
| 5.2.2 | Create Helm chart wrapping `deploy/kagent.yaml` | — | 🔲 |
| 5.2.3 | Add CD workflow: auto-deploy to staging on merge to `main` (requires 5.1 + 1.1 + 1.2) | — | 🔲 |
| 5.2.4 | Test `helm rollback` in staging | — | 🔲 |
| 5.2.5 | Write on-call runbook: restart procedures, circuit-breaker reset, session drain | — | 🔲 |

---

## Status Legend

| Symbol | Meaning |
|---|---|
| ✅ | Done |
| 🔲 | Not started |
| 🔄 | In progress |
| ⛔ | Blocked |
