# Aura — Product Roadmap

**Updated:** 2026-03-11  
**Tracks:** GitHub repo `shailwx/aura`, `main` branch

---

## Overview

This roadmap organises Aura's development from hackathon prototype to production-grade enterprise procurement agent. Milestones are driven by the backlog captured in [IMPLEMENTATION_ISSUES.md](IMPLEMENTATION_ISSUES.md) and the GitHub issue tracker.

---

## Milestone 0 — Hackathon Prototype ✅ `v0.0.1` (2026-03-11)

**Theme:** Demonstrate the end-to-end agentic procurement loop at Google AI Agent Labs Oslo 2026.

| Deliverable | Status |
|---|---|
| 5-agent pipeline: Architect → Governor → Scout → Sentinel → Closer | ✅ |
| UCP vendor discovery mock | ✅ |
| BMS KYC/AML compliance block (instruction-driven) | ✅ |
| AP2 Intent Mandate + Cart Mandate settlement mock | ✅ |
| FastAPI REST API (`/run`, `/run/stream`, `/health`) | ✅ |
| Streamlit procurement dashboard (demo + live modes) | ✅ |
| Role-based portal (Finance, Compliance, IT Manager, Admin) | ✅ |
| Policy engine (spending caps, country blocks, review thresholds) | ✅ |
| Kagent Kubernetes CRD manifests | ✅ |
| Dockerfile (multi-stage production container) | ✅ |
| 91 unit tests; ruff clean | ✅ |

---

## Milestone 1 — Safety & Deployment Foundation `v0.1.0` (Target: Q2 2026)

**Theme:** Make the prototype safe and deployable. Close the two P0 blocking issues before any further rollout.

### Issue 1 (P0) — Kagent Tool Server Resources (GitHub #1)

Define the missing `ToolServer`/MCP resource declarations so Kagent manifests deploy cleanly.

- [ ] Add `ToolServer` resource to `deploy/kagent.yaml`
- [ ] Wire Scout, Sentinel, Closer tool names to MCP server endpoints
- [ ] Add namespace, service account, and RBAC config
- [ ] Validate: `kubectl apply -f deploy/kagent.yaml` — zero unresolved references

### Issue 2 (P0) — Deterministic Compliance Gate

Replace instruction-only compliance block with a hard code-enforced runtime guard.

- [ ] Define typed `SentinelOutput` schema (`blocked: bool`, `approved_vendors`, `rejected_vendors`)
- [ ] Closer reads structured output, not free-text
- [ ] Hard-fail if `blocked=True` regardless of LLM wording
- [ ] Add regression tests: blocked path cannot reach payment tools

**Acceptance gate for v0.1.0:** Issues 1 and 2 fully resolved; `kubectl apply` passes; compliance block is code-enforced.

---

## Milestone 2 — Structured Parsing & Real Protocol Adapters `v0.2.0` (Target: Q3 2026)

**Theme:** Replace freeform text assumptions with typed schemas; begin wiring real protocol endpoints.

### Issue 3 (P1) — Structured Intent Parsing

- [ ] Pydantic model: `ProcurementIntent(product, quantity, budget, currency, constraints)`
- [ ] Architect parses raw message → `ProcurementIntent` before delegating
- [ ] Fallback clarification when required fields are missing
- [ ] Downstream agents receive typed intent, not raw string

### Issue 4 (P1) — Real UCP / BMS / AP2 Protocol Adapters

Replace mock implementations with real HTTP-based protocol adapters.

- [ ] UCP: implement live `/.well-known/ucp` endpoint discovery
- [ ] BMS: connect to real KYC/AML API (or certified test sandbox)
- [ ] AP2: implement W3C Verifiable Credential signing and AP2 gateway submission
- [ ] Retain mock fallback mode via environment flag (`AURA_MOCK_PROTOCOLS=true`)

---

## Milestone 3 — Security & Durability `v0.3.0` (Target: Q3 2026)

**Theme:** Hardening for enterprise use: authentication, sessions, and secrets.

### Issue 5 (P1) — API Authentication / Authorisation

- [ ] Add JWT/OAuth2 middleware to FastAPI
- [ ] Role-based access control: `procurement_user`, `finance_approver`, `compliance_officer`, `admin`
- [ ] Scope portal endpoints to matching roles
- [ ] Document auth flow in [API_REFERENCE.md](API_REFERENCE.md)

### Issue 6 (P2) — Durable Session State

Replace in-memory ADK session with persistent backend.

- [ ] Integrate Redis or Cloud Firestore as ADK `SessionService`
- [ ] Ensure multi-replica deployments share session state
- [ ] Add session TTL and cleanup policy

---

## Milestone 4 — Observability & Resilience `v0.4.0` (Target: Q4 2026)

**Theme:** Production-grade operations: metrics, tracing, and robust retry policies.

### Issue 7 (P2) — Retries, Timeouts, and Circuit Breakers

- [ ] Apply `execute_with_retries` + `CircuitBreaker` to all external tool HTTP calls
- [ ] Configure per-tool timeout budgets (UCP: 3 s, BMS: 2 s, AP2: 5 s)
- [ ] Expose circuit-breaker state via `/health` endpoint

### Issue 8 (P2) — Observability

- [ ] Emit structured JSON logs (structlog or standard library `logging`)
- [ ] Add OpenTelemetry tracing spans per agent and tool call
- [ ] Expose Prometheus metrics: request count, latency histogram, circuit-breaker trips
- [ ] Add Grafana dashboard template (or Vertex AI Monitoring)

---

## Milestone 5 — Production Hardening & CI/CD `v1.0.0` (Target: Q4 2026)

**Theme:** Full production readiness: test coverage, automated deploy, compliance certification.

### Issue 9 (P1) — E2E and Contract Tests

- [ ] E2E test: happy path and blocked path against real ADK Runner
- [ ] Contract tests: validate UCP, AP2, BMS mock schemas match production specs
- [ ] API integration tests: all portal endpoints
- [ ] Target: ≥ 90% line coverage

### Issue 10 (P2) — Production Hardening

- [ ] Secrets: migrate all credentials to Kubernetes Secrets + Workload Identity
- [ ] Helm chart wrapping `deploy/kagent.yaml` for parameterised releases
- [ ] CD pipeline: automated deploy on merge to `main` (dependant on Issue 9 + Issues 1 & 2)
- [ ] Rollback: `helm rollback` tested in staging
- [ ] Runbook for on-call: restart procedures, circuit-breaker reset, session drain

---

## Dependency Graph

```
v0.1.0 (Issues 1, 2)
    └── v0.2.0 (Issues 3, 4)
            └── v0.3.0 (Issues 5, 6)
                    └── v0.4.0 (Issues 7, 8)
                            └── v1.0.0 (Issues 9, 10)
```

Issues 1 and 2 are hard prerequisites for all subsequent milestones: the deployment must be clean and the compliance gate must be code-enforced before building on top.

---

## Priority Legend

| Label | Meaning |
|---|---|
| P0 | Blocking — must ship before any production use |
| P1 | High — required for enterprise readiness |
| P2 | Medium — improves operations and maintainability |
| P3 | Low — nice-to-have enhancements |
