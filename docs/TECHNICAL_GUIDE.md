# Aura — Technical Guide

> For engineers, DevOps, and solution architects building on or deploying Aura.

---

## Table of Contents

1. [Tech Stack](#1-tech-stack)
2. [Local Environment Setup](#2-local-environment-setup)
3. [Project Structure](#3-project-structure)
4. [Agent Architecture Deep-Dive](#4-agent-architecture-deep-dive)
5. [Tool Layer](#5-tool-layer)
6. [ADK Runner & Session Management](#6-adk-runner--session-management)
7. [Environment Variables](#7-environment-variables)
8. [Extending Aura](#8-extending-aura)
9. [Security Considerations](#9-security-considerations)
10. [Production Readiness Checklist](#10-production-readiness-checklist)

---

## 1. Tech Stack

| Layer | Technology | Version |
| :--- | :--- | :--- |
| Agent framework | `google-adk` | ≥ 1.0.0 |
| LLM | Gemini 2.5 Flash via Vertex AI | — |
| API server | FastAPI + Uvicorn | ≥ 0.115.0 / 0.34.0 |
| Dashboard | Streamlit | ≥ 1.40.0 |
| Runtime | Python | 3.12 |
| Container | Docker multi-stage (`python:3.12-slim`) | — |
| Kubernetes orchestration | Kagent `kagent.dev/v1alpha2` | latest |
| Cloud | GCP `europe-north1` | — |
| Auth | Pydantic + `python-jose` | ≥ 2.10.0 / 3.3.0 |
| Testing | pytest + pytest-asyncio | ≥ 8.3.0 / 0.25.0 |

---

## 2. Local Environment Setup

### Prerequisites

- Python 3.12+
- `gcloud` CLI with Application Default Credentials
- GCP project `ai-agent-labs-oslo-26-team-6` with Vertex AI enabled

### Installation

```bash
git clone https://github.com/shailwx/aura && cd aura

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # adjust if needed
gcloud auth application-default login
```

### Running

```bash
# ADK dev UI — full multi-agent browser playground
adk web

# FastAPI server
uvicorn main:app --reload --port 8080

# Streamlit dashboard (no GCP required — demo mode)
streamlit run ui/dashboard.py

# Tests
pytest tests/ -v
```

---

## 3. Project Structure

```
aura/
├── main.py                   # FastAPI app + ADK Runner entry point
├── agents/
│   ├── __init__.py
│   ├── architect.py          # Root LlmAgent + SequentialAgent wiring
│   ├── scout.py              # UCP vendor discovery agent
│   ├── sentinel.py           # KYC/AML compliance gate agent
│   └── closer.py             # AP2 payment settlement agent
├── tools/
│   ├── __init__.py
│   ├── ucp_tools.py          # discover_vendors() — UCP mock
│   ├── compliance_tools.py   # verify_vendor_compliance() — BMS mock
│   └── ap2_tools.py          # generate_intent_mandate(), settle_cart_mandate() — AP2 mock
├── ui/
│   └── dashboard.py          # Streamlit procurement dashboard
├── docs/                     # All documentation
├── tests/
│   ├── test_compliance_tool.py
│   └── test_flow.py
├── Dockerfile                # Multi-stage production container
├── kagent.yaml               # Kagent v1alpha2 CRD manifests
├── requirements.txt
└── AURA_PRD.md
```

---

## 4. Agent Architecture Deep-Dive

### Agent Hierarchy

```
architect  (LlmAgent — root)
└── AuraPipeline  (SequentialAgent)
    ├── scout     (LlmAgent)
    ├── sentinel  (LlmAgent)
    └── closer    (LlmAgent)
```

### Architect (`agents/architect.py`)

```python
architect = LlmAgent(
    name="Architect",
    model="gemini-2.5-flash",
    instruction="...",   # system prompt — intent parsing + outcome summary
    # No tools — delegates entirely to AuraPipeline sub-agent
)

_pipeline = SequentialAgent(
    name="AuraPipeline",
    sub_agents=[scout, sentinel, closer],
)
```

- **Type:** `LlmAgent` (root)
- **Tools:** None — acts purely as orchestrator
- **Delegates to:** `AuraPipeline` (SequentialAgent)
- **ADK registration:** The `architect` object is passed directly to `Runner`. It is also exposed as `root_agent` for `adk web` auto-discovery.

### Scout (`agents/scout.py`)

- **Type:** `LlmAgent`
- **Tools:** `discover_vendors(query: str) → list[dict]`
- **Output key:** `scout_results` (written to ADK session state)
- **Instruction:** Present all vendors including ShadowHardware — **never filter**

### Sentinel (`agents/sentinel.py`)

- **Type:** `LlmAgent`
- **Tools:** `verify_vendor_compliance(vendor_name: str) → dict`
- **Output key:** `sentinel_results`
- **Instruction:** Call compliance check for **every** vendor. Output `COMPLIANCE_BLOCKED` if any are REJECTED; `SENTINEL_APPROVED` if all pass.

### Closer (`agents/closer.py`)

- **Type:** `LlmAgent`
- **Tools:** `generate_intent_mandate(...)`, `settle_cart_mandate(mandate)`
- **Output key:** `closer_results`
- **Instruction:** Read `sentinel_results` first. If `COMPLIANCE_BLOCKED` is present → output `PAYMENT_ABORTED`, call **no payment tools**.

### Session State Handoff

ADK passes data between agents via `session_state` using each agent's `output_key`:

```
scout_results     → list of VendorEndpoint dicts
sentinel_results  → {approved: [{vendor_name, compliance_hash}], rejected: [{vendor_name, reason}]}
closer_results    → {settlement_id, status, amount} | "PAYMENT_ABORTED"
```

The `output_key` on each `LlmAgent` writes the agent's final text response into that session state key automatically.

---

## 5. Tool Layer

All tools are plain Python functions (`def`, not `async`). ADK wraps them as callable tools for the LLM.

### `tools/ucp_tools.py`

```python
def discover_vendors(query: str) -> list[dict[str, Any]]:
```

Returns a list of `VendorEndpoint` dicts sorted by `unit_price_usd` ascending. Currently backed by a 4-vendor in-memory mock including ShadowHardware (country `XX`, suspiciously low price).

**To replace with real UCP:** See [Protocols](PROTOCOLS.md#universal-commerce-protocol-ucp).

---

### `tools/compliance_tools.py`

```python
def verify_vendor_compliance(vendor_name: str) -> dict[str, Any]:
```

Returns `{"status": "APPROVED", "compliance_hash": "<64-hex>", ...}` or `{"status": "REJECTED", "reason": "AML_BLACKLIST", ...}`.

Key behaviours:
- Blacklist check is **case-insensitive** — `shadowhardware`, `SHADOWHARDWARE`, etc. all match
- `compliance_hash` is a SHA-256 of `COMPLIANCE:{vendor_name}:{hour}` — deterministic within the hour
- A `REJECTED` result **never** contains a `compliance_hash` field

**To replace with real BMS:** See [Protocols](PROTOCOLS.md#core-banking-system-bms-compliance-interface).

---

### `tools/ap2_tools.py`

```python
def generate_intent_mandate(
    vendor_id: str,
    vendor_name: str,
    amount: float,
    currency: str = "USD",
    compliance_hash: str = "",
) -> dict[str, Any]:

def settle_cart_mandate(mandate: dict[str, Any]) -> dict[str, Any]:
```

`generate_intent_mandate` raises `ValueError` if `amount > 5000.00`.

`settle_cart_mandate` validates:
- `mandate["type"] == "IntentMandate"`
- `mandate["constraints"]["compliance_hash"]` is non-empty
- `mandate["proof"]["value"]` is non-empty

Returns a settlement result with `settlement_id` prefixed `AP2-`.

**To replace with real AP2:** See [Protocols](PROTOCOLS.md#agent-payments-protocol-v2-ap2).

---

## 6. ADK Runner & Session Management

`main.py` wires the ADK stack:

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

_session_service = InMemorySessionService()

_runner = Runner(
    app_name="aura",
    agent=architect,         # root agent
    session_service=_session_service,
)
```

### Session lifecycle

1. `POST /run` receives `user_id` + optional `session_id`
2. If `session_id` is absent or the session doesn't exist → `create_session()`
3. `_runner.run_async(user_id, session_id, new_message)` streams `Event` objects
4. Events with `event.content.parts` containing `part.text` are collected and joined

**Note:** `InMemorySessionService` does not persist across restarts. For production, replace with a persistent session backend (Cloud Firestore, Redis, etc.) once the ADK provides one.

### Streaming endpoint

`POST /run/stream` uses the same runner but returns a `StreamingResponse` that yields text chunks as they arrive, suitable for SSE (Server-Sent Events) or chunked HTTP clients.

---

## 7. Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GOOGLE_CLOUD_PROJECT` | `ai-agent-labs-oslo-26-team-6` | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | `europe-north1` | Vertex AI region |
| `GOOGLE_GENAI_USE_VERTEXAI` | `1` | Set to `1` to route LLM calls via Vertex AI |
| `APP_NAME` | `aura` | ADK app name (scopes sessions) |
| `PORT` | `8080` | FastAPI listen port |

Set via `.env` (loaded by `python-dotenv`) or Kubernetes `ConfigMap`/`Secret`.

---

## 8. Extending Aura

### Adding a new tool

1. Create a plain Python function in `tools/`:

```python
# tools/inventory_tools.py
def check_inventory(vendor_id: str, product_id: str) -> dict:
    """Check real-time stock levels."""
    ...
```

2. Import and register it on the relevant agent:

```python
# agents/scout.py
from tools.inventory_tools import check_inventory

scout = LlmAgent(
    ...
    tools=[discover_vendors, check_inventory],
)
```

3. Add a test in `tests/test_inventory_tools.py` following the existing pattern.

---

### Adding a new agent

1. Create `agents/my_agent.py`:

```python
from google.adk.agents import LlmAgent
from tools.my_tools import my_tool

my_agent = LlmAgent(
    name="MyAgent",
    model="gemini-2.5-flash",
    description="...",
    instruction="...",
    tools=[my_tool],
    output_key="my_agent_results",
)
```

2. Add it to the pipeline in `agents/architect.py`:

```python
from agents.my_agent import my_agent

_pipeline = SequentialAgent(
    name="AuraPipeline",
    sub_agents=[scout, sentinel, my_agent, closer],
)
```

3. Add a Kagent CRD block in `kagent.yaml` mirroring the existing agent entries.

---

### Swapping the LLM model

Each `LlmAgent` accepts a `model` string. To use a different model:

```python
# Default model (confirmed working on the hackathon project)
scout = LlmAgent(model="gemini-2.5-flash", ...)

# Or set via env var and read at init time
import os
MODEL = os.getenv("AURA_MODEL", "gemini-2.5-flash")
scout = LlmAgent(model=MODEL, ...)
```

For a full cloud swap (AWS Bedrock, Azure OpenAI, Ollama), update the `ModelConfig` in `kagent.yaml` — see [Deployment Guide](DEPLOYMENT.md#cloud-agnostic-model-swap).

---

### Replacing mock tools with real integrations

All three tool files are designed as **drop-in replacements**. The agent logic and session state handoff does not change when real integrations are substituted:

| Tool file | Replace function | Real target |
| :--- | :--- | :--- |
| `ucp_tools.py` | `discover_vendors()` | UCP registry + `/.well-known/ucp` endpoints |
| `compliance_tools.py` | `verify_vendor_compliance()` | Internal BMS REST/gRPC compliance API |
| `ap2_tools.py` | `generate_intent_mandate()` + `settle_cart_mandate()` | AP2 settlement network with HSM signing |

See [Protocols](PROTOCOLS.md) for each real integration path.

---

## 9. Security Considerations

### Authentication & authorisation

- The current FastAPI server has no authentication layer — add OAuth2/JWT or API key middleware before any production exposure.
- `python-jose[cryptography]` is already in `requirements.txt` for JWT handling.

### Secrets management

- Never commit `.env` to version control.
- In Kubernetes, use `Secret` resources (not `ConfigMap`) for GCP credentials.
- The Dockerfile runs as a **non-root user** (`aura`) to limit container privilege.

### Compliance integrity

- The `compliance_hash` is currently SHA-256 (mock). In production, this must be returned by the authoritative BMS API — do not allow client-generated hashes.
- The AP2 `settle_cart_mandate()` function validates that `compliance_hash` is non-empty before settling. This **must** be preserved in any real AP2 integration.

### Input validation

- `RunRequest.message` is an arbitrary string passed to the LLM — validate length and sanitise if embedding in structured prompts.
- `generate_intent_mandate()` enforces a hard `amount > 5000` guard; this is a financial control and must not be removed.

### SSRF

- The real UCP integration will make outbound HTTP requests to vendor-supplied URLs. Always validate URLs against an allowlist before following redirects.

---

## 10. Production Readiness Checklist

| Item | Status | Notes |
| :--- | :--- | :--- |
| Replace `InMemorySessionService` | ⬜ | Use persistent session store for multi-instance deployment |
| Add API authentication | ⬜ | JWT / API key middleware on `/run` and `/run/stream` |
| Replace UCP mock | ⬜ | Implement real `/.well-known/ucp` discovery |
| Replace BMS compliance mock | ⬜ | Wire to internal compliance API with credentials |
| Replace AP2 mock | ⬜ | Implement ECDSA-P256 signing with HSM + real AP2 gateway |
| Multi-currency support | ⬜ | ISO 4217 currency field already in data model |
| Structured logging | ⬜ | Add `structlog` or Cloud Logging for audit trail |
| Metrics / tracing | ⬜ | OpenTelemetry instrumentation for agent latency + pipeline health |
| Rate limiting | ⬜ | Add per-user rate limiting on `/run` |
| Persistent session store | ⬜ | Replace `InMemorySessionService` with Firestore / Redis backend |
| CI/CD pipeline | ⬜ | GitHub Actions: test → build → push → `kubectl apply` |
| Compliance audit log | ⬜ | Record every `verify_vendor_compliance` call with timestamp + result |

---

## Related Documentation

| Document | Audience |
| :--- | :--- |
| [Architecture](ARCHITECTURE.md) | Diagrams and component overview |
| [Agent Flow](AGENT_FLOW.md) | Sequence diagrams (happy + blocked path) |
| [Data Model](DATA_MODEL.md) | Full schema reference |
| [API Reference](API_REFERENCE.md) | REST endpoint reference |
| [Protocols](PROTOCOLS.md) | UCP, AP2, BMS design rationale + real integration paths |
| [Deployment](DEPLOYMENT.md) | Kagent Kubernetes deployment |
| [Testing](TESTING.md) | Test suite and coverage |
