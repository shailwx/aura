# Changelog

All notable changes to **Project Aura** are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) — `Added`, `Changed`, `Fixed`, `Removed`
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

> Changes on feature branches not yet merged to `main`.

### Added
- `docs/USE_CASES.md` — 16 procurement use cases: 3 core demo scenarios, 8 SSA contract type scenarios, and 5 extended real-world scenarios (volume discounts, mandate splits, geo-restrictions, payment thresholds, audit trails)

### In Progress
- `test/architect-e2e` — E2E integration test for the full Scout → Sentinel → Closer pipeline (#2)
- `feat/kagent-manifest` — Kubernetes Agent CRD review and `kagent apply --dry-run` validation (#1)

---

## [feat/policy-engine] — Unreleased

> Policy Engine feature branch (#15). Adds three-stage governance rules for procurement.

### Added

#### Policy Engine (`tools/`)
- `tools/policy_store.py` — `PolicyStore` singleton with 6 default rules (SPENDING_LIMIT, GEO_RESTRICTION, CATEGORY_ALLOWLIST, APPROVAL_THRESHOLD, CERTIFICATION_REQUIRED, RATE_LIMIT); atomic JSON persistence to `tmp/policies.json`; `ReviewStore` for human-in-the-loop payment review queue
- `tools/policy_tools.py` — Three evaluation functions consumed by agents:
  - `evaluate_procurement_policy(request)` — pre-flight gate (category, spending, rate limits)
  - `evaluate_vendor_policy(vendor, amount)` — vendor gate (geo-restriction, certifications, approval thresholds)
  - `evaluate_payment_policy(mandate, user_id)` — payment gate (approval thresholds, daily spend limits)
  - `RateLimitStore` — sliding-window per-user rate limiting (in-memory)
  - `DailySpendStore` — per-user daily spend accumulation (in-memory)

#### Governor Agent (`agents/`)
- `agents/governor.py` — New pre-flight `LlmAgent`; inserted first in the pipeline before Scout; outputs POLICY_CLEAR / POLICY_WARNINGS / POLICY_REVIEW_REQUIRED / POLICY_BLOCKED

#### Pipeline Changes
- `agents/architect.py` — Updated pipeline: `Governor → Scout → Sentinel → Closer` (previously `Scout → Sentinel → Closer`)
- `agents/sentinel.py` — Added `evaluate_vendor_policy` tool; now runs both BMS compliance check AND vendor policy check per vendor
- `agents/closer.py` — Added `evaluate_payment_policy` tool; checks `governor_results` and `sentinel_results` for policy/compliance blocks before any payment settlement

#### Policy Management REST API (`main.py`)
- `GET /policies` — list all policy rules
- `POST /policies` — create rule (requires `X-Admin-Token` header)
- `GET /policies/{rule_id}` — get single rule
- `PUT /policies/{rule_id}` — partial update (requires `X-Admin-Token`)
- `DELETE /policies/{rule_id}` — delete rule, returns 204 (requires `X-Admin-Token`)
- `GET /reviews` — list pending payment reviews
- `POST /reviews/{id}/approve` — approve a review (requires `X-Admin-Token`)
- `POST /reviews/{id}/reject` — reject a review (requires `X-Admin-Token`)

#### Kubernetes (`kagent.yaml`)
- `aura-admin-token` Kubernetes Secret manifest for `AURA_ADMIN_TOKEN`
- Governor Agent CRD with `evaluate_procurement_policy` MCP tool
- All agents (Scout, Sentinel, Closer, Architect) updated with `AURA_ADMIN_TOKEN` env var
- Sentinel and Closer updated with new policy tool registrations

#### Tests (`tests/`)
- `tests/test_policy_tools.py` — 27 new unit tests covering all 6 rule types, rate limiting, daily spend, snapshot hashing, and disabled-rule bypass

#### Documentation
- `docs/AGENT_FLOW.md` — Rewritten with three Mermaid sequence diagrams: Happy Path, Policy Block (Governor halts pre-flight), Compliance Block (Sentinel → Closer aborts)

---

## [0.1.0-hackathon] — 2026-03-11

> Hackathon prototype delivered at **Google AI Agent Labs Oslo 2026 — Team 6**.
> All core agent logic, tooling, infrastructure, and documentation complete.

### Added

#### Agents (`agents/`)
- `architect.py` — Root `LlmAgent` orchestrator; parses procurement intent, chains Scout → Sentinel → Closer via `SequentialAgent`
- `scout.py` — UCP vendor discovery agent; calls `discover_vendors()`, flags risky vendors (country `XX`, suspicious pricing), writes `scout_results` to session state
- `sentinel.py` — KYC/AML compliance gate; runs every vendor through `verify_vendor_compliance()`, outputs `COMPLIANCE_BLOCKED` on any rejection
- `closer.py` — AP2 payment settlement agent; generates `IntentMandate` (W3C VC), settles via `settle_cart_mandate()`, aborts if Sentinel blocked

#### Tools (`tools/`)
- `ucp_tools.py` — `discover_vendors(query)` — mock UCP vendor database of 4 vendors (including deliberately blacklisted `ShadowHardware`), sorted by unit price
- `compliance_tools.py` — `verify_vendor_compliance(vendor_name)` — BMS KYC/AML mock; deterministic 64-char `ComplianceHash` for approved vendors; `AML_BLACKLIST` rejection for ShadowHardware
- `ap2_tools.py` — `generate_intent_mandate()` + `settle_cart_mandate()` — AP2 mock with W3C VC `IntentMandate` structure, ECDSA-P256 proof, 5000 USD cap, `AP2-*` settlement IDs

#### API Server
- `main.py` — FastAPI server (port 8080) with Google ADK `Runner`; `POST /run` (sync) + `POST /run/stream` (SSE); `GET /health` liveness probe; `InMemorySessionService` for session state

#### Infrastructure
- `Dockerfile` — Multi-stage Python 3.12 build; non-root `aura` user; healthcheck on `/health`
- `kagent.yaml` — `kagent.dev/v1alpha2` manifests for all 4 agents + shared `ModelConfig` (Vertex AI Gemini 2.5 Flash, `europe-north1`) + `ClusterIP` Service
- `.env` / `.env.example` — GCP project config (`ai-agent-labs-oslo-26-team-6`, `europe-north1`)

#### CI/CD (`.github/workflows/`)
- `ci.yml` — ruff lint → pytest → Docker build (runtime stage); triggers on every push and PR to `main`
- `cd.yml` — GCP Artifact Registry push + `kagent apply`; triggers on push to `main`; `workflow_dispatch` with `skip_deploy` safety input

#### Tests (`tests/`)
- `test_ucp_tools.py` — 9 tests: vendor count, sort order, ShadowHardware `XX` flag, required fields, query-agnostic behaviour
- `test_compliance_tools.py` — 17 tests: blacklist (exact + case variants + whitespace), 64-char hex hash, determinism within hour, unique hashes per vendor
- `test_ap2_tools.py` — 27 tests: mandate structure, UUID ID, amount cap, ECDSA proof, settlement ID format, missing-hash guard, wrong-type guard
- `conftest.py` — pytest asyncio mode + `integration` marker
- **Total: 91 tests, 0 failures**

#### Documentation (`docs/`)
- `ARCHITECTURE.md` — System diagram (Mermaid), component table, data flow, technology stack
- `AGENT_FLOW.md` — Sequence diagrams: happy path + compliance-blocked path
- `DATA_MODEL.md` — Class diagram + JSON examples for all 4 data structures
- `DEPLOYMENT.md` — Kagent install, GCP setup, Docker build/push, verification commands, cloud-agnostic model swap guide
- `PROTOCOLS.md` — UCP, AP2, BMS protocol explanations; mock-vs-real integration paths
- `DEMO_SCRIPT.md` — Full pitch script with timing, live demo steps, judge Q&A
- `docs/README.md` — Index of all documentation files

#### Project Hygiene
- `README.md` — Agent squad table, quick-start guide, Mermaid flowchart, docs index
- `pyproject.toml` — pytest config (`asyncio_mode=auto`, `testpaths`, `--tb=short -v`)
- `requirements.txt` — `google-adk`, `google-cloud-aiplatform`, `fastapi`, `uvicorn`, `cryptography`, `pydantic`, `pytest`, `pytest-asyncio`, `httpx`
- `LICENSE` — Apache 2.0
- `.gitignore` — Python, venv, IDE, Zone.Identifier metadata exclusions
- `.github/pull_request_template.md` — Summary, type checkboxes, compliance checklist
- `dashboard/` — Streamlit presentation dashboard for live demo

#### GitHub Project Setup
- 6 labels: `agent`, `infra`, `testing`, `ci-cd`, `compliance`, `docs`
- 2 milestones: `Demo Day — Mar 11 2026`, `v0.1 Post-Hackathon`
- 8 issues (#1–#8) covering all components, with labels, milestones, and linked branches
- 8 feature branches: `feat/kagent-manifest`, `test/architect-e2e`, `test/scout-unit`, `test/sentinel-unit`, `test/closer-unit`, `feat/ci-pipeline`, `feat/cd-pipeline`, `chore/pr-template`

---

## [0.0.1] — 2026-03-11

> Initial scaffolding commit.

### Added
- Project structure: `agents/`, `tools/`, `tests/`, `docs/`
- `__init__.py` stubs for all packages
- Initial `requirements.txt`

---

[Unreleased]: https://github.com/shailwx/aura/compare/v0.1.0-hackathon...HEAD
[0.1.0-hackathon]: https://github.com/shailwx/aura/compare/v0.0.1...v0.1.0-hackathon
[0.0.1]: https://github.com/shailwx/aura/releases/tag/v0.0.1
