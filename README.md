# Aura — Autonomous Reliable Agentic Commerce

> **Multi-agent B2B procurement with built-in KYC/AML compliance and verifiable payment.**

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-1.0-green)](https://github.com/google/adk-python)
[![Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash-orange)](https://cloud.google.com/vertex-ai)
[![Kagent](https://img.shields.io/badge/Kagent-v1alpha2-purple)](https://kagent.dev)
[![License](https://img.shields.io/badge/license-Apache%202.0-lightgrey)](LICENSE)

---

## What is Aura?

Aura automates the full B2B procurement lifecycle — from vendor discovery to payment settlement — using a squad of autonomous AI agents. Unlike traditional shopping bots, Aura integrates **Real-time KYC/AML compliance** and **cryptographically verifiable payment mandates** before any transaction is settled.

**Built for:** Google AI Agent Labs Oslo 2026 — Team 6

---

## The Agent Squad

| Agent | Title | Responsibility | Protocol |
| :--- | :--- | :--- | :--- |
| **Architect** | 🏛️ Procurement Officer | Parses user intent and orchestrates the full agent pipeline end-to-end | Google ADK `SequentialAgent` |
| **Governor** | ⚖️ Finance Controller | Evaluates the procurement request against org spending rules *before* any vendor is contacted | Internal Policy Engine |
| **Scout** | 🔭 Category Manager | Queries `/.well-known/ucp` endpoints to discover vendors, fetch pricing tiers, and rank candidates | UCP `/.well-known/ucp` |
| **Sentinel** | 🛡️ Compliance Officer | Screens every shortlisted vendor against AML blacklists and KYC rules via the Core Banking System | BMS Compliance API |
| **Closer** | 💳 Payment Manager | Signs a W3C Verifiable Credential Intent Mandate and settles payment through the AP2 gateway | AP2 `IntentMandate` + ECDSA-P256 |

```mermaid
flowchart LR
    User(["👤 User"])
    Architect["🏛️ Architect<br/><i>Procurement Officer</i>"]
    Governor["⚖️ Governor<br/><i>Finance Controller</i>"]
    Scout["🔭 Scout<br/><i>Category Manager</i>"]
    Sentinel["🛡️ Sentinel<br/><i>Compliance Officer</i>"]
    Closer["💳 Closer<br/><i>Payment Manager</i>"]
    Settlement(["✅ Settled"])
    Blocked(["⛔ Blocked"])

    User -->|"procurement request"| Architect
    Architect -->|"orchestrates"| Governor
    Governor -->|"policy: ALLOW"| Scout
    Governor -->|"policy: BLOCK"| Blocked
    Scout -->|"ranked vendor list"| Sentinel
    Sentinel -->|"KYC: APPROVED"| Closer
    Sentinel -->|"KYC: BLOCKED"| Blocked
    Closer -->|"AP2 mandate settled"| Settlement
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Google Cloud project with Vertex AI enabled (`ai-agent-labs-oslo-26-team-6`)
- Application Default Credentials: `gcloud auth application-default login`

### Install & Run

```bash
# Clone and enter
git clone https://github.com/shailwx/aura && cd aura

# Set up virtualenv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed (project/region already pre-configured)

# Launch ADK dev UI — full browser-based agent playground
adk web

# Or run the FastAPI server directly
uvicorn main:app --reload --port 8080
```

### Try it

```bash
# Happy path — legitimate vendor
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Buy 3 Laptop Pro 15 units from the best vendor"}'

# Blocked path — triggers Sentinel compliance block
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Buy laptops from ShadowHardware"}'
```

See [API Reference](docs/API_REFERENCE.md) for full endpoint documentation.

### API Authentication (Optional)

Aura can run with JWT auth enabled for `/run` and `/run/stream`.

```bash
# .env
AUTH_ENABLED=true
AUTH_JWT_SECRET=replace-with-strong-secret
AUTH_JWT_ALGORITHM=HS256
AUTH_ALLOWED_ROLES=procurement_runner,admin
```

When enabled, call endpoints with a bearer token containing at least:
- `sub` (caller identity)
- `role` (must be in `AUTH_ALLOWED_ROLES`)

Example request:

```bash
curl -X POST http://localhost:8080/run \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Buy 3 Laptop Pro 15 units"}'
```

### Session Backend (In-Memory or Redis)

Aura uses `SESSION_BACKEND` to choose session persistence:

```bash
# default dev mode
SESSION_BACKEND=inmemory

# durable mode
SESSION_BACKEND=redis
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_KEY_PREFIX=aura:sessions
SESSION_TTL_SECONDS=0
```

Use Redis mode for multi-instance or restart-resilient deployments.

### Reliability Controls (Real Provider Mode)

In `AURA_PROVIDER_MODE=real`, Aura applies retries, exponential backoff,
and a circuit breaker to UCP/BMS/AP2 HTTP calls.

```bash
HTTP_RETRY_ATTEMPTS=3
HTTP_RETRY_BACKOFF_SECONDS=0.2
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
CIRCUIT_BREAKER_RESET_SECONDS=30
```

AP2 settlement requests also include a deterministic `Idempotency-Key`
derived from mandate data to reduce duplicate settlement risk on retries.

### Observability

Aura now includes baseline observability primitives:

- Correlation ID propagation via `X-Correlation-ID`
- Structured request logs with correlation ID and latency
- In-memory metrics snapshot endpoint at `GET /metrics`

Quick check:

```bash
curl -i http://localhost:8080/health
curl http://localhost:8080/metrics
```

### Streamlit Dashboard

```bash
streamlit run ui/dashboard.py
```

Opens at `http://localhost:8501`. Runs the full pipeline visually with real-time agent status cards, vendor tables, compliance badges, and settlement results. Works in **demo mode** (no GCP credentials needed) or **API mode** (calls the FastAPI server). See [Dashboard Guide](docs/DASHBOARD.md) for details.

### Run Tests

```bash
pytest tests/ -v
```

See [Testing Guide](docs/TESTING.md) for full test suite documentation.

---

## Project Structure

```
aura/
├── main.py               # FastAPI app + ADK Runner
├── agents/
│   ├── architect.py      # Root orchestrator (SequentialAgent wiring)
│   ├── scout.py          # UCP vendor discovery
│   ├── sentinel.py       # KYC/AML compliance gate
│   └── closer.py         # AP2 payment settlement
├── tools/
│   ├── ucp_tools.py      # Universal Commerce Protocol mock
│   ├── compliance_tools.py  # BMS KYC/AML compliance mock
│   └── ap2_tools.py      # Agent Payments Protocol v2 mock
├── docs/
│   ├── ARCHITECTURE.md   # System architecture diagram
│   ├── AGENT_FLOW.md     # Sequence diagrams (happy + blocked path)
│   ├── DATA_MODEL.md     # Data model class diagram
│   ├── DEPLOYMENT.md     # Kagent deployment guide
│   └── PROTOCOLS.md      # UCP + AP2 protocol design rationale
├── tests/
│   ├── test_compliance_tool.py
│   └── test_flow.py
├── Dockerfile            # Multi-stage production container
├── scripts/
│   └── demo.sh           # Demo run script
├── deploy/
│   └── kagent.yaml       # Kagent v1alpha2 CRD manifests
└── requirements.txt
```

---

## Documentation

### For Business Users

| Document | Description |
| :--- | :--- |
| [Business Guide](docs/BUSINESS_GUIDE.md) | What Aura does, business value, use cases, glossary — no code |
| [Demo Script](docs/DEMO_SCRIPT.md) | Hackathon pitch guide, live demo steps, and judge Q&A prep |
| [PRD](docs/PRD.md) | Full Product Requirements Document |

### For Technical Users

| Document | Description |
| :--- | :--- |
| [Technical Guide](docs/TECHNICAL_GUIDE.md) | Setup, agent internals, tool layer, extending Aura, production checklist |
| [Architecture](docs/ARCHITECTURE.md) | System topology and component diagram |
| [Agent Flow](docs/AGENT_FLOW.md) | Sequence diagrams for happy path and compliance block |
| [Data Model](docs/DATA_MODEL.md) | VendorEndpoint, IntentMandate, ComplianceResult schemas |
| [API Reference](docs/API_REFERENCE.md) | REST endpoints — `/run`, `/run/stream`, `/health` |
| [Dashboard](docs/DASHBOARD.md) | Streamlit UI guide (demo & API modes) |
| [Testing](docs/TESTING.md) | Test suite coverage and how to run tests |
| [Deployment](docs/DEPLOYMENT.md) | Kagent Kubernetes deployment guide |
| [Protocols](docs/PROTOCOLS.md) | UCP, AP2, and BMS protocol design rationale |

---

## GCP Configuration

| Setting | Value |
| :--- | :--- |
| Project | `ai-agent-labs-oslo-26-team-6` |
| Region | `us-central1` |
| Model | `gemini-2.5-flash` via Vertex AI |

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
