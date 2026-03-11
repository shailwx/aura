# 📄 PRD: Project "Aura" - Autonomous Reliable Agentic Commerce

**Version:** 2026.1.0
**Stack:** Google ADK (Python), UCP, AP2, Kagent (Kubernetes), Gemini 2.5 Flash
**Status:** Hackathon Prototype (Google AI Agent Labs Oslo 2026 — Team 6)

---

## 1. Executive Summary

**Aura** is a multi-agent, cloud-agnostic procurement system designed to automate the B2B commerce lifecycle. Unlike traditional "shopping bots," Aura integrates **Real-time Compliance (KYC/AML)** and **Verifiable Intent** to allow agents to discover, negotiate, and settle transactions autonomously on behalf of an enterprise. It bridges the gap between modern AI agents and rigid Core Banking Systems (BMS).

---

## 2. System Architecture (Multi-Agent Squad)

Aura operates as a **MAS (Multi-Agent System)** using the Google ADK orchestration layer. Each agent is an independent entity that can be deployed as a Kubernetes `Agent` resource.

| Agent | Responsibility | Key Protocol/Tool |
| :--- | :--- | :--- |
| **Architect** | Root `LlmAgent`; parses user intent; manages sub-agent state. | `adk.LlmAgent` |
| **Scout** | Discovers vendors via Universal Commerce Protocol (UCP). | `ucp_tools.discover_vendors` |
| **Sentinel** | Executes KYC/AML checks against core banking (BMS) logic. | `compliance_tools.verify_vendor_compliance` |
| **Closer** | Handles secure payment via Agent Payments Protocol (AP2). | `ap2_tools.generate_intent_mandate` + `settle_cart_mandate` |

---

## 3. Functional Requirements

### FR-01: Agentic Discovery (UCP)

- **Action:** The Scout agent must query `/.well-known/ucp` endpoints of potential vendors.
- **Validation:** It must parse the `dev.ucp.shopping` capability manifest to find product pricing and availability.
- **Output:** Return a structured list of `VendorEndpoint` objects to the Architect.

### FR-02: Compliance-First Vetting (The Sentinel)

- **Action:** Before a cart is finalised, the Sentinel must cross-reference the `VendorID` against the internal BMS (Core Banking) compliance database.
- **Requirement:** Return a "Compliance Hash" for valid vendors; immediately block and flag vendors like "ShadowHardware" (mocked blacklist).

### FR-03: Verifiable Intent & Settlement (AP2)

- **Action:** The Closer agent must generate an **Intent Mandate** (W3C Verifiable Credential).
- **Execution:** Simulate a secure checkout using a `Cart Mandate` signed via the AP2 protocol, ensuring the payment is routed through a compliant banking gateway.

### FR-04: Cloud-Agnostic Kubernetes Deployment

- **Platform:** Deploy via **Kagent** (Cloud Native Agentic AI framework).
- **Resiliency:** Agents must be defined as `Agent` Custom Resources (CRDs) to allow for cross-cloud portability (GCP/AWS/On-prem).

---

## 4. Technical Specifications

### Data Model: The AP2 Intent Mandate

```json
{
  "type": "IntentMandate",
  "id": "<uuid>",
  "issued_at": 1741694400,
  "vendor": {
    "id": "v-001",
    "name": "TechCorp Nordic"
  },
  "constraints": {
    "max_amount": 5000.00,
    "amount": 3897.00,
    "currency": "USD",
    "compliance_required": true,
    "compliance_hash": "<64-char-hex>"
  },
  "proof": {
    "type": "ecdsa-p256-signature",
    "value": "MOCK_SIGNATURE_HASH",
    "created": 1741694400
  }
}
```

### Infrastructure Target

- **Runtime:** Python 3.12 (FastAPI for A2A comms, port 8080)
- **Orchestration:** `google-adk` with `SequentialAgent` for the main flow
- **Model:** Vertex AI Gemini 2.5 Flash (`gemini-2.5-flash`)
- **GCP Project:** `ai-agent-labs-oslo-26-team-6`
- **Region:** `us-central1`
- **Deployment:** `kagent` YAML with `ModelConfig` targeting Vertex AI

---

## 5. Implementation Prompts (Copilot Agent Mode)

1. **Project Init:** Scaffold with `agent-starter-pack`, `requirements.txt`, `.env`, `agents/` and `tools/` folders.
2. **The Sentinel Logic:** Implement `verify_vendor_compliance(vendor_name)` — reject "ShadowHardware", return 64-char `ComplianceHash` for others.
3. **The Orchestrator:** Chain Scout → Sentinel → Closer via `SequentialAgent`. Flow proceeds to Closer only if Sentinel passes.
4. **K8s Containerisation:** Multi-stage `Dockerfile` + `kagent.yaml` following `kagent.dev/v1alpha2` spec.
