# GitHub Issue Drafts (Ready to Paste)

Repository: `shailwx/aura`  
Date: 2026-03-11  
Purpose: New issue drafts for uncovered backlog items (Implementation Issues 2-8).

---

## Draft A — Compliance Safety Runtime Gate (Backlog Issue 2)

**Title**  
`[Safety] Deterministic compliance gate between Sentinel and Closer`

**Suggested labels**  
`compliance`, `agent`, `testing`

**Suggested milestone**  
`v0.1 Post-Hackathon`

**Suggested branch**  
`feat/compliance-runtime-gate`

**Body (paste as-is)**

```markdown
## Summary
Enforce compliance blocking in code (not only prompt text): if Sentinel rejects any vendor, Closer must not execute payment tool calls under any condition.

## Why
Current behavior is largely instruction-driven. Payment safety must be deterministic at runtime.

## Scope
- Define structured Sentinel output payload
- Make Closer consume structured payload only
- Block payment path when `blocked=true` or compliance hash is missing

## Acceptance Criteria
- [ ] Sentinel emits structured result: `{blocked, approved_vendors, rejected_vendors, reason_codes}`
- [ ] Closer checks Sentinel payload before any AP2 tool invocation
- [ ] If `blocked=true`, Closer returns `PAYMENT_ABORTED` and does not call settlement tools
- [ ] If vendor lacks `compliance_hash`, Closer hard-fails with safe error
- [ ] Tests verify no payment path executes after compliance rejection

## Dependencies
- None (can start now)

## References
- docs/IMPLEMENTATION_ISSUES.md — Issue 2
- agents/sentinel.py
- agents/closer.py
```

---

## Draft B — Structured Intent Parsing (Backlog Issue 3)

**Title**  
`[Agent] Structured procurement intent extraction and validation`

**Suggested labels**  
`agent`, `enhancement`, `testing`

**Suggested milestone**  
`v0.1 Post-Hackathon`

**Suggested branch**  
`feat/structured-intent-parser`

**Body (paste as-is)**

```markdown
## Summary
Add typed procurement intent parsing so pipeline logic uses structured fields (`product`, `quantity`, `budget`, `currency`) instead of freeform assumptions.

## Why
Reliable amount calculation and vendor selection require deterministic inputs.

## Scope
- Add Pydantic procurement intent model
- Parse/validate user requests into structured fields
- Add clear correction prompts when required fields are missing

## Acceptance Criteria
- [ ] New intent schema model exists and is validated before pipeline execution
- [ ] Message parsing outputs typed fields consumed by Scout/Sentinel/Closer
- [ ] Missing/invalid fields return actionable response (no silent defaults)
- [ ] Amount calculations use parsed `quantity` and selected vendor price
- [ ] Unit tests cover valid and invalid parsing scenarios

## Dependencies
- Recommended after Safety gate issue

## References
- docs/IMPLEMENTATION_ISSUES.md — Issue 3
- main.py
- agents/architect.py
```

---

## Draft C — Real Integration Adapters (Backlog Issue 4)

**Title**  
`[Integration] Replace mock tools with pluggable UCP/BMS/AP2 adapters`

**Suggested labels**  
`integration`, `infra`, `enhancement`

**Suggested milestone**  
`v0.1 Post-Hackathon`

**Suggested branch**  
`feat/provider-adapters`

**Body (paste as-is)**

```markdown
## Summary
Refactor mock protocol tools into provider adapters with `mock` and `real` modes for UCP discovery, BMS compliance, and AP2 settlement.

## Why
Prototype mocks are useful for demoing, but production rollout requires real API clients.

## Scope
- Define adapter interfaces and typed contracts
- Keep mock implementations for local/dev
- Add real HTTP clients (auth-enabled) behind a config flag

## Acceptance Criteria
- [ ] Provider interfaces for UCP/BMS/AP2 are defined and used by agents/tools
- [ ] `mock` mode behavior remains backward-compatible with existing tests
- [ ] `real` mode can be enabled via env/config
- [ ] Network/auth/config failures return actionable errors
- [ ] Contract tests exist for response schema and error mapping

## Dependencies
- Should follow structured intent and compliance gate work

## References
- docs/IMPLEMENTATION_ISSUES.md — Issue 4
- tools/ucp_tools.py
- tools/compliance_tools.py
- tools/ap2_tools.py
```

---

## Draft D — API Authentication/Authorization (Backlog Issue 5)

**Title**  
`[Security] Add authn/authz for /run and /run/stream endpoints`

**Suggested labels**  
`security`, `api`, `compliance`

**Suggested milestone**  
`v0.1 Post-Hackathon`

**Suggested branch**  
`feat/api-authn-authz`

**Body (paste as-is)**

```markdown
## Summary
Protect FastAPI execution endpoints with JWT/OIDC auth and role-based authorization.

## Why
Current API endpoints are unauthenticated and not suitable for enterprise deployment.

## Scope
- Add token validation dependency/middleware
- Enforce role checks (e.g., runner/admin)
- Propagate caller identity into request context and logs

## Acceptance Criteria
- [ ] `/run` and `/run/stream` reject unauthenticated requests (`401`)
- [ ] Authenticated but unauthorized role gets `403`
- [ ] Authorized caller metadata is available in execution context
- [ ] Tests cover auth success/failure/forbidden scenarios
- [ ] `README.md` documents local auth configuration

## Dependencies
- None strict, but pairs well with observability issue

## References
- docs/IMPLEMENTATION_ISSUES.md — Issue 5
- main.py
```

---

## Draft E — Durable Session Store (Backlog Issue 6)

**Title**  
`[State] Replace in-memory ADK session service with durable backend`

**Suggested labels**  
`infra`, `enhancement`, `reliability`

**Suggested milestone**  
`v0.1 Post-Hackathon`

**Suggested branch**  
`feat/durable-session-store`

**Body (paste as-is)**

```markdown
## Summary
Replace `InMemorySessionService` with a durable session backend to support restart recovery and horizontal scaling.

## Why
In-memory state is lost on restart and cannot be shared across replicas.

## Scope
- Add session service abstraction
- Implement durable backend (Redis recommended)
- Add TTL/cleanup policy and config for local + cloud

## Acceptance Criteria
- [ ] Sessions persist across app restarts
- [ ] Multiple app instances can access the same session state
- [ ] TTL/expiration policy is configurable
- [ ] Local dev fallback remains available
- [ ] Tests verify persistence and multi-instance correctness

## Dependencies
- Recommended before full CD rollout

## References
- docs/IMPLEMENTATION_ISSUES.md — Issue 6
- main.py
```

---

## Draft F — Resilience Controls (Backlog Issue 7)

**Title**  
`[Reliability] Add timeout/retry/circuit-breaker and idempotency controls`

**Suggested labels**  
`reliability`, `integration`, `testing`

**Suggested milestone**  
`v0.1 Post-Hackathon`

**Suggested branch**  
`feat/reliability-controls`

**Body (paste as-is)**

```markdown
## Summary
Add resilience safeguards around external provider calls (timeouts, retries with backoff, circuit breaker, and settlement idempotency).

## Why
Real integrations will fail transiently; without safeguards we risk duplicate settlements or poor user experience.

## Scope
- HTTP client defaults (timeouts/retries/backoff)
- Circuit breaker for repeated downstream failures
- Idempotency key strategy for payment settlement requests

## Acceptance Criteria
- [ ] Configurable timeout/retry policies for UCP/BMS/AP2 clients
- [ ] Circuit breaker opens after threshold and auto-recovers
- [ ] Settlement requests include idempotency key
- [ ] Duplicate settlement attempts are prevented
- [ ] Failure-path tests cover retry exhaustion and circuit-open behavior

## Dependencies
- Depends on adapter integration issue

## References
- docs/IMPLEMENTATION_ISSUES.md — Issue 7
```

---

## Draft G — Observability and Tracing (Backlog Issue 8)

**Title**  
`[Observability] Correlation IDs, structured logs, metrics, and tracing`

**Suggested labels**  
`observability`, `infra`, `enhancement`

**Suggested milestone**  
`v0.1 Post-Hackathon`

**Suggested branch**  
`feat/observability-foundation`

**Body (paste as-is)**

```markdown
## Summary
Introduce observability foundation across the full pipeline: request correlation IDs, structured logs, core metrics, and distributed tracing hooks.

## Why
Production debugging and compliance auditing require traceability across Architect → Scout → Sentinel → Closer.

## Scope
- Add correlation ID middleware
- Add structured event schema for each stage
- Add metrics for success/failure/latency/tool errors
- Add tracing instrumentation and export hooks

## Acceptance Criteria
- [ ] Each request has a correlation ID propagated through all stages
- [ ] Logs are structured and include stage + outcome fields
- [ ] Metrics include stage latency, error count, and settlement outcomes
- [ ] Traces can reconstruct one full request path end-to-end
- [ ] Basic dashboard/runbook docs added

## Dependencies
- None strict; best after auth and adapter work starts

## References
- docs/IMPLEMENTATION_ISSUES.md — Issue 8
```

---

## Optional Meta-Epic Draft (if you want tracking parent)

**Title**  
`[Epic] Post-hackathon production hardening track`

**Body (paste as-is)**

```markdown
## Summary
Parent tracking issue for production hardening work after hackathon prototype.

## Child Issues
- [ ] Compliance runtime gate
- [ ] Structured intent parser
- [ ] Integration adapters (mock/real)
- [ ] API authn/authz
- [ ] Durable session store
- [ ] Reliability controls
- [ ] Observability foundation

## Exit Criteria
- Non-mock staging validation complete
- Deterministic compliance gate verified
- API secured and observable
- CI/CD and deployment gates enforced
```

---

## Update Comments for Existing Issues

Use these as comments on the existing GitHub issues to align scope with the backlog.

### Issue #1 Update Comment

**Target:** https://github.com/shailwx/aura/issues/1  
**Paste as-is:**

```markdown
Alignment update from implementation backlog:

To make `kagent.yaml` actually deployable end-to-end, this issue should include ToolServer/MCP wiring in addition to Agent CRDs.

### Please extend scope with:
- Add/define `aura-tool-server` resource(s) referenced by Scout/Sentinel/Closer tools
- Validate tool name mapping (`discover_vendors`, `verify_vendor_compliance`, `generate_intent_mandate`, `settle_cart_mandate`)
- Add readiness check proving agents can resolve and invoke tools at runtime

### Acceptance criteria additions:
- [ ] `kubectl apply -f kagent.yaml` succeeds without unresolved tool server refs
- [ ] Agent tool calls succeed in a smoke run (not only CRD dry-run)

Rationale: current manifest has tool dependencies that are not covered by CRD-only validation.
```

### Issue #2 Update Comment

**Target:** https://github.com/shailwx/aura/issues/2  
**Paste as-is:**

```markdown
Alignment update from implementation backlog:

This E2E test should explicitly validate deterministic compliance gating in runtime behavior (not only textual agent output).

### Please extend test assertions with:
- Verify Closer does **not** invoke AP2 settlement when Sentinel indicates block
- Verify blocked path returns `PAYMENT_ABORTED` with no settlement ID
- Verify approved path includes valid compliance hash before mandate/settlement

### Suggested dependency note:
- Track/block on safety issue: "Deterministic compliance gate between Sentinel and Closer"

Rationale: this keeps E2E tests aligned with production safety requirements.
```

### Issue #6 Update Comment

**Target:** https://github.com/shailwx/aura/issues/6  
**Paste as-is:**

```markdown
Alignment update from implementation backlog:

Current CI scope is good, but we should add safety and API-level gates so CI protects business-critical behavior.

### Please extend CI acceptance criteria with:
- [ ] Include Architect E2E orchestration test job (`tests/test_architect_e2e.py`)
- [ ] Include API smoke tests (`/health`, `/run`) in test stage
- [ ] Fail CI if deterministic compliance gate tests fail

### Optional but recommended:
- Add type-check job (mypy/pyright) for tool contracts
- Add path filters to skip Docker build when only docs change

Rationale: CI should verify not only code quality, but also compliance safety invariants.
```

---

## Optional: Short Cross-Link Comment (paste on all three)

```markdown
Cross-linking implementation alignment doc: see `docs/IMPLEMENTATION_ISSUES.md` and `docs/GITHUB_ISSUE_DRAFTS.md` for overlap/conflict resolution and updated sequencing.
```