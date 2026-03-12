# Aura — Technical Specification

**Version:** 1.0.0  
**Status:** Baseline  
**Updated:** 2026-03-11

---

## 1. Scope

This document provides the formal technical specification for the **Aura** autonomous B2B procurement system. It covers:

- Agent contracts and invocation interfaces  
- Tool function signatures and behaviour guarantees  
- Data schemas (inputs, outputs, session state)  
- Non-functional requirements (NFRs)  
- Security and trust model  
- External integration specifications  

---

## 2. Agent Contracts

### 2.1 Architect

| Property | Value |
|---|---|
| ADK Type | `LlmAgent` (root) |
| Model | `gemini-2.5-flash` via Vertex AI |
| Tools | None |
| Input | Free-text procurement request string |
| Output | Final prose summary written to ADK session state |
| Sub-agents | `AuraPipeline` (SequentialAgent) |

**Invariants:**
- Must not call any payment or compliance tool directly.
- Must always delegate to `AuraPipeline` for structured processing.
- Output must summarise the final pipeline outcome to the user.

---

### 2.2 Governor

| Property | Value |
|---|---|
| ADK Type | `LlmAgent` |
| Model | `gemini-2.5-flash` via Vertex AI |
| Tools | `evaluate_procurement_policy`, `evaluate_vendor_policy`, `evaluate_payment_policy` |
| Input | `governor_input` key from session state (structured procurement request) |
| Output key | `governor_results` |

**Invariants:**
- Must call `evaluate_procurement_policy` before delegating to Scout.
- Must emit `POLICY_BLOCKED` if decision is `BLOCK`; otherwise emit `GOVERNOR_APPROVED`.
- Policy evaluation result must include `snapshot_hash` for auditability.

---

### 2.3 Scout

| Property | Value |
|---|---|
| ADK Type | `LlmAgent` |
| Model | `gemini-2.5-flash` via Vertex AI |
| Tools | `discover_vendors` |
| Input | `governor_results` key (must be `GOVERNOR_APPROVED`) |
| Output key | `scout_results` |

**Invariants:**
- Must never filter or omit vendors from discovery results.
- Must present all vendors — including `ShadowHardware` — to Sentinel for compliance gating.
- Discovery list must contain at least one `VendorEndpoint` to proceed.

---

### 2.4 Sentinel

| Property | Value |
|---|---|
| ADK Type | `LlmAgent` |
| Model | `gemini-2.5-flash` via Vertex AI |
| Tools | `verify_vendor_compliance` |
| Input | `scout_results` vendor list |
| Output key | `sentinel_results` |

**Invariants:**
- Must call `verify_vendor_compliance` for **every** vendor in `scout_results`.
- Must emit `COMPLIANCE_BLOCKED` if **any** vendor status is `REJECTED`.
- Must emit `SENTINEL_APPROVED` only when all vendors pass KYC/AML.
- The compliance hash for each approved vendor must be forwarded to Closer.

---

### 2.5 Closer

| Property | Value |
|---|---|
| ADK Type | `LlmAgent` |
| Model | `gemini-2.5-flash` via Vertex AI |
| Tools | `generate_intent_mandate`, `settle_cart_mandate` |
| Input | `sentinel_results` key |
| Output key | `closer_results` |

**Invariants:**
- Must check `sentinel_results` for `COMPLIANCE_BLOCKED` before any payment tool call.
- If blocked, must emit `PAYMENT_ABORTED` and call **no** payment tools.
- `generate_intent_mandate` must use the compliance hash returned by Sentinel.
- Settlement must only proceed with verified `AP2-*` settlement IDs.

---

## 3. Tool Function Signatures

### 3.1 `discover_vendors(query: str) -> list[dict]`

**Module:** `tools.ucp_tools`

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `query` | `str` | Free-text procurement intent from Scout |

**Returns:** List of serialised `VendorEndpoint` dicts with keys:

| Key | Type | Notes |
|---|---|---|
| `id` | `str` | e.g. `"v-001"` |
| `name` | `str` | Vendor display name |
| `capability` | `str` | UCP capability string, e.g. `"dev.ucp.shopping"` |
| `product` | `str` | Product name |
| `unit_price_usd` | `float` | Tier-1 base unit price |
| `available_units` | `int` | Current stock level |
| `ucp_endpoint` | `str` | `/.well-known/ucp` URL |
| `country` | `str` | ISO 3166-1 alpha-2 country code |
| `pricing_tiers` | `list[dict]` | Volume pricing tiers (see §5.1) |

**Error behaviour:** Raises `CircuitOpenError` if the circuit breaker is open. Retries up to 3 times with exponential back-off (base 0.5 s) on `httpx.RequestError`.

---

### 3.2 `verify_vendor_compliance(vendor_name: str) -> dict`

**Module:** `tools.compliance_tools`

**Returns:**

| Key | Type | Values |
|---|---|---|
| `status` | `str` | `APPROVED` \| `REJECTED` |
| `compliance_hash` | `str` | 64-char hex string (SHA-256 mock) |
| `reason` | `str` | Human-readable explanation |
| `kyc_passed` | `bool` | KYC outcome |
| `aml_passed` | `bool` | AML outcome |

---

### 3.3 `generate_intent_mandate(vendor_id, vendor_name, amount, compliance_hash) -> dict`

**Module:** `tools.ap2_tools`

**Parameters:**

| Name | Type | Constraint |
|---|---|---|
| `vendor_id` | `str` | Must match a `VendorEndpoint.id` |
| `vendor_name` | `str` | Display name |
| `amount` | `float` | USD, > 0 |
| `compliance_hash` | `str` | Must be a 64-char hex string from Sentinel |

**Returns:** Serialised `IntentMandate` dict with W3C Verifiable Credential envelope.

---

### 3.4 `settle_cart_mandate(mandate: dict) -> dict`

**Module:** `tools.ap2_tools`

**Returns:**

| Key | Type | Notes |
|---|---|---|
| `settlement_id` | `str` | e.g. `"AP2-3X7K9F2A1B4C"` |
| `status` | `str` | `SETTLED` |
| `amount_usd` | `float` | Settled amount |
| `vendor` | `str` | Vendor name |
| `timestamp` | `str` | ISO-8601 UTC |

---

### 3.5 Policy Tools

| Function | Consumed by | Return type |
|---|---|---|
| `evaluate_procurement_policy(request)` | Governor | `PolicyDecision` dict |
| `evaluate_vendor_policy(vendor, amount)` | Sentinel | `PolicyDecision` dict |
| `evaluate_payment_policy(mandate, user_id)` | Closer | `PolicyDecision` dict |

All policy tools return a dict with keys: `decision` (`ALLOW`\|`WARN`\|`REVIEW`\|`BLOCK`), `violations`, `evaluated_rules`, `snapshot_hash`.

---

## 4. Data Schemas

### 4.1 `PricingTier`

```python
@dataclass
class PricingTier:
    min_qty: int
    max_qty: int | None
    unit_price_usd: float
    discount_pct: float
```

### 4.2 `VendorEndpoint`

```python
@dataclass
class VendorEndpoint:
    id: str
    name: str
    capability: str
    product: str
    unit_price_usd: float          # Tier-1 base price
    available_units: int
    ucp_endpoint: str
    country: str
    pricing_tiers: list[PricingTier]
    org_number: str | None         # Norwegian Brønnøysund registry ID
```

### 4.3 `IntentMandate`

```json
{
  "type": "IntentMandate",
  "id": "<uuid>",
  "vendor_id": "<str>",
  "vendor_name": "<str>",
  "amount_usd": "<float>",
  "compliance_hash": "<64-char hex>",
  "created_at": "<ISO-8601 UTC>",
  "credential": {
    "@context": ["https://www.w3.org/2018/credentials/v1"],
    "type": ["VerifiableCredential", "IntentMandate"],
    "issuer": "aura-agent",
    "issuanceDate": "<ISO-8601 UTC>"
  }
}
```

### 4.4 ADK Session State Keys

| Key | Set by | Consumed by | Type |
|---|---|---|---|
| `governor_results` | Governor | Scout | `str` (`GOVERNOR_APPROVED` \| `POLICY_BLOCKED:…`) |
| `scout_results` | Scout | Sentinel | JSON string — list of vendor dicts |
| `sentinel_results` | Sentinel | Closer | `str` (`SENTINEL_APPROVED` \| `COMPLIANCE_BLOCKED:…`) |
| `closer_results` | Closer | Architect | JSON string — settlement result |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Target | Measured at |
|---|---|---|
| End-to-end pipeline latency (happy path) | < 8 s (p95) | FastAPI `/run` endpoint |
| Scout UCP discovery | < 3 s (p95) | `discover_vendors()` |
| Compliance check per vendor | < 1 s (p95) | `verify_vendor_compliance()` |
| FastAPI `/health` response time | < 100 ms | Health check endpoint |

### 5.2 Reliability

| Requirement | Specification |
|---|---|
| Circuit-breaker threshold | 3 consecutive failures → open |
| Circuit-breaker reset timeout | 30 s |
| Retry attempts | 3 attempts with exponential back-off (base 0.5 s) |
| Retryable exceptions | `httpx.RequestError`, `httpx.TimeoutException` |
| Agent availability target | ≥ 99.5% (Kubernetes liveness probe every 10 s) |

### 5.3 Scalability

- Each agent runs as an independent Kubernetes `Agent` CRD, allowing independent horizontal scaling.
- Session state is in-memory per ADK `Runner` instance (stateful per container); horizontal scaling requires session externalization (see [ROADMAP.md](ROADMAP.md) — Issue 6).
- Average model inference calls per pipeline invocation: 5 (one per agent).

---

## 6. Security and Trust Model

### 6.1 Compliance Enforcement

| Layer | Mechanism | Status |
|---|---|---|
| Instruction-based | Sentinel system prompt forbids cleared-vendor bypass | ✅ Implemented |
| Code-based gate | Hard runtime check before payment tool call | ⚠️ Roadmap Issue 2 |
| Audit trail | Compliance hash logged per transaction | ✅ Implemented |

### 6.2 Policy Rules

| Rule ID | Name | Severity | Threshold |
|---|---|---|---|
| POL-001 | Spending Cap | BLOCK | $5,000 per request |
| POL-002 | High-Value Review | REVIEW | $4,000 per request |
| POL-003 | Sanctioned Countries | BLOCK | OFAC list (IR, KP, RU, SY, XX) |
| POL-004 | Category Allowlist | BLOCK | Approved categories only |
| POL-005 | Warn Large Purchase | WARN | $2,000 per request |

### 6.3 API Authentication

Current state: **unauthenticated** (prototype only). Production requirement: JWT/OAuth2 with role-based access control (see [ROADMAP.md](ROADMAP.md) — Issue 5).

### 6.4 Secrets Management

| Secret | Current | Required |
|---|---|---|
| GCP credentials | `gcloud ADC` / env | Kubernetes Secret + Workload Identity |
| API keys | Environment variable | Vault or Google Secret Manager |

---

## 7. Integration Specifications

### 7.1 FastAPI REST API

Base URL: `http://localhost:8080` (local) / service DNS (Kubernetes)

| Endpoint | Method | Description |
|---|---|---|
| `/run` | POST | Synchronous pipeline invocation |
| `/run/stream` | POST | SSE streaming pipeline invocation |
| `/health` | GET | Liveness check |
| `/api/portal/*` | GET/POST | Portal role-based data endpoints |

See [API_REFERENCE.md](API_REFERENCE.md) for full request/response schemas.

### 7.2 ADK Runner

```python
runner = Runner(
    agent=architect,
    app_name="aura",
    session_service=InMemorySessionService(),
)
```

- Session lifetime: per HTTP request (created and destroyed in `/run` handler).
- Streaming sessions: live-yielded via ADK `run_async` generator.

### 7.3 Kagent Kubernetes Deployment

- Manifests: `deploy/kagent.yaml`  
- API version: `kagent.dev/v1alpha2`  
- Namespace: `aura`  
- Each agent has an independent `Agent` CRD with `ModelConfig` pointing to Vertex AI.

See [DEPLOYMENT.md](DEPLOYMENT.md) for full deployment steps.

---

## 8. Testing Requirements

| Level | Tool | Coverage target |
|---|---|---|
| Unit | `pytest` | All public tool functions |
| Integration | `pytest` + `httpx` | All FastAPI endpoints |
| Contract | `pytest` | UCP, AP2, BMS mock schemas |
| E2E | `pytest` + real ADK Runner | Happy path + blocked path |

Run the full suite: `pytest tests/ -v`

See [TESTING.md](TESTING.md) for detailed test catalogue.
