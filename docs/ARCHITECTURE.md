# Aura — System Architecture

## Overview

Aura is a Multi-Agent System (MAS) built on Google ADK. The Architect orchestrates four specialist sub-agents — Governor, Scout, Sentinel, and Closer — in a sequential pipeline. Each agent has a single responsibility and communicates via ADK session state.

---

## System Architecture Diagram

```mermaid
graph TD
    User([👤 Enterprise User]) -->|Natural language<br/>procurement request| Architect

    subgraph Aura MAS ["🤖 Aura Multi-Agent System (Google ADK)"]
        Architect["🏛️ Architect<br/><i>Pipeline Commander</i><br/>gemini-3.1-flash"]

        subgraph Pipeline ["⚙️ AuraPipeline (SequentialAgent)"]
            Governor["⚖️ Governor<br/><i>Policy Gatekeeper</i><br/>LlmAgent"]
            Scout["🔭 Scout<br/><i>Vendor Pathfinder</i><br/>LlmAgent"]
            Sentinel["🛡️ Sentinel<br/><i>Compliance Guardian</i><br/>LlmAgent"]
            Closer["💳 Closer<br/><i>Deal Executor</i><br/>LlmAgent"]
        end

        Architect -->|delegates to| Pipeline
        Governor -->|policy: ALLOW → session_state| Scout
        Governor -->|policy: BLOCK| PolicyBlocked(["⛔ Policy Blocked"])
        Scout -->|vendor list → session_state| Sentinel
        Sentinel -->|compliance results → session_state| Closer
    end

    Scout -->|GET /.well-known/ucp| UCP[("🌐 UCP Network<br/>Vendor Endpoints")]
    Sentinel -->|KYC/AML lookup| BMS[("🏦 BMS<br/>Core Banking<br/>Compliance DB")]
    Closer -->|Intent Mandate + ECDSA-P256| AP2[("🔐 AP2 Gateway<br/>Payment Settlement")]

    Closer -->|Settlement result| Architect
    Architect -->|Summary + settlement_id| User

    subgraph GCP ["☁️ Google Cloud (europe-north1)"]
        VertexAI["✨ Vertex AI<br/>Gemini 3.1 Flash"]
    end

    Architect -.->|LLM inference| VertexAI
    Governor -.->|LLM inference| VertexAI
    Scout -.->|LLM inference| VertexAI
    Sentinel -.->|LLM inference| VertexAI
    Closer -.->|LLM inference| VertexAI

    style Aura MAS fill:#e8f4f8,stroke:#1a73e8,stroke-width:2px
    style Pipeline fill:#f0f8e8,stroke:#34a853,stroke-width:1px
    style GCP fill:#fef9e7,stroke:#fbbc04,stroke-width:1px
```

---

## Component Responsibilities

| Component | Type | Responsibility |
| :--- | :--- | :--- |
| **Architect** | `LlmAgent` (root) | Parses user intent, owns the pipeline, summarises outcome |
| **AuraPipeline** | `SequentialAgent` | Chains Governor → Scout → Sentinel → Closer in order |
| **Governor** | `LlmAgent` | Calls `evaluate_procurement_policy()`; halts pipeline on policy violation |
| **Scout** | `LlmAgent` | Calls `discover_vendors()`, writes vendor list to session state |
| **Sentinel** | `LlmAgent` | Calls `verify_vendor_compliance()` for every vendor; blocks on REJECTED |
| **Closer** | `LlmAgent` | Calls `generate_intent_mandate()` + `settle_cart_mandate()`; no-ops if blocked |

---

## Data Flow

```
User message
    ↓
Architect (parse intent)
    ↓
Governor → session_state["governor_results"] = POLICY_CLEAR | POLICY_WARNINGS | POLICY_BLOCKED
    ↓ (only if POLICY_CLEAR or POLICY_WARNINGS)
Scout → session_state["scout_results"] = [VendorEndpoint, ...]
    ↓
Sentinel → session_state["sentinel_results"] = {approved: [...], rejected: [...]}
    ↓ (only if no rejections)
Closer → session_state["closer_results"] = {settlement_id, status, amount}
    ↓
Architect (summarise)
    ↓
User response
```

---

## Block Flows

### Policy Block (Governor)

If the request violates procurement policy:

```
Governor evaluates evaluate_procurement_policy()
    ↓
Returns POLICY_BLOCKED (category denied / spend cap exceeded / rate limit hit)
    ↓
Pipeline halts — Scout, Sentinel, and Closer never run
    ↓
Architect reports policy violation to user
    ↓
No vendor discovery or payment tools are ever called
```

### Compliance Block (Sentinel)

If any vendor fails the KYC/AML check:

```
Sentinel detects REJECTED vendor
    ↓
Outputs COMPLIANCE_BLOCKED to session state
    ↓
Closer reads COMPLIANCE_BLOCKED → outputs PAYMENT_ABORTED
    ↓
Architect reports blocked transaction to user
    ↓
No payment tools are ever called
```

---

## Technology Stack

| Layer | Technology |
| :--- | :--- |
| Agent Framework | Google ADK (`google-adk`) |
| LLM | Gemini 3.1 Flash via Vertex AI |
| API Server | FastAPI + Uvicorn |
| Container | Docker (multi-stage, python:3.12-slim) |
| Orchestration | Kagent `kagent.dev/v1alpha2` |
| Cloud | GCP `europe-north1` |
| Protocols | UCP (mocked), AP2 (mocked), BMS (mocked) |
