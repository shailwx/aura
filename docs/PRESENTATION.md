# AURA — Hackathon Pitch Deck

> Autonomous Reliable Agentic Commerce — AI-powered B2B procurement with built-in compliance.

---

## 📋 At a Glance

| Property | Value |
|----------|-------|
| **Event** | Google AI Agent Labs Oslo 2026 |
| **Team** | Team 6 |
| **Date** | March 11, 2026 |
| **Format** | 12-slide pitch deck — 5 min pitch + 3 min live demo + 2 min Q&A |
| **Status** | Ready |
| **Related** | [Demo Script](DEMO_SCRIPT.md) · [Architecture](ARCHITECTURE.md) · [Agent Flow](AGENT_FLOW.md) |

---

<!-- ============================================================
     SLIDE 1 — TITLE
     ============================================================ -->

# Slide 1 — Title

---

## AURA

### Autonomous Reliable Agentic Commerce

> AI-powered B2B procurement with built-in compliance — vendor discovery, KYC/AML screening, and payment settlement from a single natural language request.

**Google AI Agent Labs Oslo 2026 · Team 6 · March 11, 2026**

---

> **Speaker note:**
> Open with energy. Let the tagline land before moving on.
> *"We're Team 6, and we built Aura — Autonomous Reliable Agentic Commerce."*

---

<!-- ============================================================
     SLIDE 2 — THE PROBLEM
     ============================================================ -->

# Slide 2 — The Problem

---

## B2B Procurement is Broken

### Today's reality:

- **Manual, slow, fragmented** — vendor sourcing, compliance checks, and payments live in three separate silos
- **Days to weeks** to complete a single procurement cycle
- **AI bots skip compliance** — they find a vendor and pay. That's a financial crime risk
- **AML/KYC pressure is real** — banks and enterprises face increasing regulatory scrutiny
- **No cryptographic proof** — no tamper-evident audit trail on vendor vetting decisions

---

### The consequence:

> *"ShadowHardware looks cheap. But it's on the AML blacklist. Traditional bots would pay them. Aura blocks them — automatically, every time."*

---

> **Speaker note:**
> Build tension here. Make judges feel the pain.
> Pause after the ShadowHardware quote — let it sink in.
> Transition: *"That's the gap we're closing."*

---

<!-- ============================================================
     SLIDE 3 — THE SOLUTION
     ============================================================ -->

# Slide 3 — The Solution

---

## Meet Aura

> A multi-agent AI system that automates the **entire B2B procurement lifecycle** — all from a single natural language request.

### What makes Aura different:

| # | Differentiator | What it means |
|---|----------------|---------------|
| 1 | **Compliance-first, not compliance-after** | Every vendor is checked against the compliance database *before* a payment mandate is generated — not after |
| 2 | **Verifiable payment mandates** | W3C Verifiable Credential with ECDSA-P256 cryptographic proof on every transaction |
| 3 | **Cloud-agnostic, Kubernetes-native** | Runs on GCP, AWS, Azure, or on-premise — swap models with two lines of YAML |

### The promise:

- Vendor discovery → KYC/AML compliance → payment settlement
- **Seconds to minutes**, not days to weeks
- No human in the loop. No compliance gaps.

---

> **Speaker note:**
> Deliver the three differentiators crisply — one breath each.
> End with: *"Let me show you how it works under the hood."*

---

<!-- ============================================================
     SLIDE 4 — ARCHITECTURE OVERVIEW
     ============================================================ -->

# Slide 4 — Architecture Overview

---

## The Aura Pipeline

```
User (natural language request)
        │
        ▼
┌───────────────────┐
│   🏛️  Architect   │  ← Root orchestrator (Google ADK)
│   (Gemini 2.5)    │    Parses intent, owns the pipeline
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   ⚖️  Governor    │  ← Pre-flight policy gatekeeper
│                   │    Spend caps, category allowlist, geo-restrictions
└────────┬──────────┘
         │
         ▼
┌───────────────────┐        ┌─────────────────┐
│   🔭  Scout       │ ──────▶│  UCP Vendor Net │  (vendor discovery)
│                   │        └─────────────────┘
└────────┬──────────┘
         │
         ▼
┌───────────────────┐        ┌─────────────────┐
│   🛡️  Sentinel    │ ──────▶│  BMS Compliance │  (KYC/AML screening)
│                   │        └─────────────────┘
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
 APPROVED  BLOCKED ──────▶ PAYMENT_ABORTED (nothing moves)
    │
    ▼
┌───────────────────┐        ┌─────────────────┐
│   💳  Closer      │ ──────▶│  AP2 Gateway    │  (payment settlement)
│                   │        └─────────────────┘
└───────────────────┘
         │
         ▼
  Settlement Confirmed
  W3C Verifiable Credential
  ECDSA-P256 signed
```

---

> **Speaker note:**
> Walk the pipeline left-to-right (or top-to-bottom if drawing on whiteboard).
> Emphasise the fork after Sentinel — the blocked path means *zero* payment tools are invoked.
> *"If Sentinel says no, the Closer never even receives a request. It's architectural."*

---

<!-- ============================================================
     SLIDE 5 — THE 5-AGENT SQUAD
     ============================================================ -->

# Slide 5 — The 5-Agent Squad

---

## Each Agent, One Job

| Agent | Role |
|-------|------|
| 🏛️ **Architect** | Root orchestrator — parses your intent, manages the squad, summarises the outcome |
| ⚖️ **Governor** | Pre-flight policy gate — blocks requests that violate spend caps, category allowlist, or geo-restrictions *before* vendor search |
| 🔭 **Scout** | Vendor pathfinder — queries the UCP network, finds ALL candidates, flags suspicious ones, **never filters** |
| 🛡️ **Sentinel** | Compliance guardian — runs KYC/AML on every vendor via BMS; one REJECTED = full pipeline block |
| 💳 **Closer** | Deal executor — generates a signed W3C Intent Mandate, submits to AP2; **no-ops if blocked** |

---

### Session state handoff

```
Architect → governor_results → scout_results → sentinel_results → closer_results
```

> *Each agent writes to its `output_key`. The next agent reads the full accumulated context — automatic, via Google ADK `SequentialAgent`.*

---

> **Speaker note:**
> Keep this slide punchy — one line per agent. The audience doesn't need every detail here.
> Highlight the Scout's "never filters" rule — it's intentional. The Sentinel is the filter, not the Scout.

---

<!-- ============================================================
     SLIDE 6 — DEMO: HAPPY PATH
     ============================================================ -->

# Slide 6 — Live Demo: Happy Path

---

## "Buy 3 Laptop Pro 15 units from the best available vendor"

### What you'll see:

**Step 1 — Intent parsed**
- 🏛️ Architect: *"Delegating to pipeline"*

**Step 2 — Governor passes**
- ⚖️ Governor: *"Request approved — within spend policy"*

**Step 3 — Scout discovers 4 vendors**

| Vendor | Price/unit | Flag |
|--------|-----------|------|
| NordHardware | $1,280 | ✅ Clean |
| TechSupply Co | $1,350 | ✅ Clean |
| GlobalIT | $1,490 | ✅ Clean |
| **ShadowHardware** | **$899** | ⚠️ Suspicious — flagged |

**Step 4 — Sentinel screens all 4**
- 🛡️ ShadowHardware → `AML_BLACKLIST`: **REJECTED**
- All others → Compliance Hash assigned: **APPROVED**

**Step 5 — Closer settles**
- 💳 NordHardware selected — cheapest approved vendor
- Settlement: **$3,840** (3 units × $1,280)
- Intent Mandate signed with ECDSA-P256
- Settlement ID: `AP2-XXXX`

---

> **Speaker note:**
> Narrate each agent card as it activates.
> End with a beat on the result card:
> *"Settlement confirmed — $3,840. ShadowHardware excluded automatically. No one had to make a judgment call."*

---

<!-- ============================================================
     SLIDE 7 — DEMO: COMPLIANCE BLOCK
     ============================================================ -->

# Slide 7 — Live Demo: Compliance Block

---

## "Buy laptops from ShadowHardware"

### What you'll see:

**Step 1** — Scout finds ShadowHardware

**Step 2** — Sentinel hits BMS compliance check:

```
Vendor:  ShadowHardware
Status:  REJECTED
Reason:  AML_BLACKLIST
```

**Step 3** — Closer card turns **red**:

```
COMPLIANCE_BLOCKED detected in session state
→ Output: PAYMENT_ABORTED
→ Tools called: ZERO
```

---

### The key line:

> *"The Closer never even saw a payment request. The Compliance Hash was never generated. There is no way for money to move to a blacklisted vendor — it's architectural."*

---

### Two layers of safety

| Layer | Mechanism |
|-------|-----------|
| **LLM prompt override** | Closer system prompt: if `COMPLIANCE_BLOCKED` in session state → `PAYMENT_ABORTED`, no tools |
| **Tool validation** | `settle_cart_mandate()` validates `compliance_hash` field — missing hash raises an exception |

---

> **Speaker note:**
> Let the empty "Tools called: ZERO" land. That's the punchline.
> *"It's not just policy — it's enforced by the architecture itself. The LLM cannot accidentally bypass it."*

---

<!-- ============================================================
     SLIDE 8 — COMPLIANCE-FIRST DESIGN
     ============================================================ -->

# Slide 8 — Compliance-First Design

---

## Why "Compliance-First" is Different

### The problem with compliance-after:

```
Traditional AI agent:
  Find vendor → Pay → (maybe) log for compliance audit

Aura:
  Find vendor → KYC/AML screen → Generate mandate WITH hash → Pay
                      ↓ BLOCKED?
                 No mandate. No payment. Ever.
```

---

### The Intent Mandate — a W3C Verifiable Credential

```json
{
  "type": "IntentMandate",
  "vendor_id": "VENDOR-001",
  "amount": 3840.00,
  "constraint": { "max_amount": 5000.00 },
  "compliance_hash": "sha256:abc123...",
  "proof": {
    "type": "EcdsaSecp256k1Signature2019",
    "algorithm": "ECDSA-P256",
    "signature": "..."
  }
}
```

- **Compliance Hash** embedded in the mandate — gateway verifies independently
- **$5,000 transaction cap** enforced in the mandate itself, not just policy
- **Tamper-evident** — any modification breaks the ECDSA-P256 signature

---

> **Speaker note:**
> You don't need to read the JSON — just point to the `compliance_hash` and `proof` fields.
> *"The gateway verifies the compliance hash independently of Aura. Even if the pipeline was compromised, the gateway won't process a mandate without a valid hash."*

---

<!-- ============================================================
     SLIDE 9 — TECHNICAL STACK
     ============================================================ -->

# Slide 9 — Technical Stack

---

## Built With

| Layer | Technology |
|-------|-----------|
| **Agent Framework** | Google ADK (`google-adk`) — `SequentialAgent` + `LlmAgent` |
| **LLM** | Gemini 2.5 Flash via Vertex AI |
| **API Server** | FastAPI + Uvicorn |
| **UI** | Streamlit dashboard |
| **Container** | Docker (multi-stage, `python:3.12-slim`) |
| **Orchestration** | Kagent `kagent.dev/v1alpha2` Kubernetes CRDs |
| **Cloud** | GCP `us-central1` (cloud-agnostic by design) |
| **Protocols** | UCP · AP2 · BMS |
| **Credentials** | ECDSA-P256 · W3C Verifiable Credentials |
| **Tests** | pytest — 91 tests, all green ✅ |

---

### Cloud-agnostic model swap — two lines of YAML

```yaml
# kagent.yaml — swap model backend
model: gemini-2.5-flash          # or: bedrock/claude-3, azure/gpt-4o
region: us-central1              # or: eu-west-1, westeurope
```

---

> **Speaker note:**
> Drop the Kagent line naturally:
> *"Built on Google ADK with Gemini 2.5 Flash via Vertex AI. Deployed as Kubernetes agents using Kagent CRDs — cloud-agnostic. Swap Gemini for Bedrock or Azure OpenAI by changing two lines of YAML."*

---

<!-- ============================================================
     SLIDE 10 — IMPACT & METRICS
     ============================================================ -->

# Slide 10 — Impact & Metrics

---

## What Aura Delivers

### Speed

| Step | Traditional | Aura |
|------|------------|------|
| Vendor sourcing | Hours–days | Seconds |
| KYC/AML screening | Days | Seconds |
| Payment settlement | Days | Seconds |
| **Full cycle** | **Days–weeks** | **< 60 seconds** |

---

### Compliance

- **Zero false payments** — architecturally guaranteed, not just policy-enforced
- **100% vendor coverage** — every vendor screened, every time
- **Cryptographic audit trail** — every transaction carries a W3C VC with ECDSA-P256 proof
- **$5,000 transaction cap** — embedded in mandate constraints, validated by gateway

---

### Engineering quality

- **91 tests, all passing** — unit + integration coverage across all 5 agents and all tool layers
- **3 decoupled integrations** — UCP, BMS, AP2 are drop-in replacements; real APIs = one function swap per tool
- **Production-grade patterns** — session state, concurrent requests, persistent session store (Firestore-ready)

---

> **Speaker note:**
> Land on the "< 60 seconds vs days-weeks" contrast — that's the headline metric.
> The 91-test line is credibility — say it once and move on.

---

<!-- ============================================================
     SLIDE 11 — RUN IT YOURSELF
     ============================================================ -->

# Slide 11 — Run It Yourself

---

## Two Commands to Launch Aura

```bash
# Terminal 1 — UI Dashboard
cd aura
source .venv/bin/activate
streamlit run ui/dashboard.py
# → http://localhost:8501

# Terminal 2 — REST API
uvicorn main:app --reload --port 8080
# → http://localhost:8080/docs  (Swagger UI)
```

---

### Or curl it directly

```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Buy 3 Laptop Pro 15 units from best vendor"}'
```

---

### Try these prompts

| Scenario | Prompt |
|----------|--------|
| Happy path | `Buy 3 Laptop Pro 15 units from the best available vendor` |
| Compliance block | `Buy laptops from ShadowHardware` |
| Policy violation | `Buy $50,000 worth of server racks from any vendor` |

---

### Reference links

| Resource | Location |
|----------|----------|
| Dashboard | `http://localhost:8501` |
| API Swagger UI | `http://localhost:8080/docs` |
| Architecture | `docs/ARCHITECTURE.md` |
| Agent flow | `docs/AGENT_FLOW.md` |

---

> **Speaker note:**
> If time allows, do the curl demo live — it's 30 seconds and shows enterprise integration potential.
> *"It's also a REST API — any enterprise system can plug in. Multi-turn sessions, streaming responses, Kubernetes-native."*

---

<!-- ============================================================
     SLIDE 12 — CLOSING
     ============================================================ -->

# Slide 12 — Closing

---

## Aura

> *"Aura is what B2B commerce looks like when agents are first-class participants — not just bots that scrape prices, but autonomous actors that discover, vet, and pay with cryptographic proof at every step."*

---

### The three things to remember:

1. **Compliance-first** — no vendor is paid without passing KYC/AML. Architecturally enforced.
2. **Cryptographic proof** — every transaction carries a W3C Verifiable Credential, signed with ECDSA-P256.
3. **Production-grade pattern** — swap mocks for real APIs, deploy on any Kubernetes cluster, swap models with YAML.

---

### Thank you.

**Team 6 · Google AI Agent Labs Oslo 2026**

---

> **Speaker note:**
> Deliver the closing quote slowly. Then smile and say *"Thank you."*
> Leave the slide on screen during Q&A — the three bullet points are your Q&A anchors.

---

<!-- ============================================================
     ANTICIPATED Q&A
     ============================================================ -->

# Appendix — Anticipated Q&A

*Keep these answers ready. The judges will ask.*

---

**Q: This is a mock — how close is it to production?**

> "The agent logic, pipeline, session state handoff, and data structures are all production-grade. The three integrations that are mocked — UCP vendor discovery, BMS compliance API, and AP2 settlement — are all designed as drop-in replacements. The `tools/` layer is fully decoupled from the agent reasoning layer. Replacing mock with real is a single function swap per tool."

---

**Q: What's to stop the LLM from ignoring the Sentinel's output?**

> "Two safety layers. First, the Closer's system prompt has an explicit hard override: if `COMPLIANCE_BLOCKED` appears anywhere in session state, output `PAYMENT_ABORTED` and call no tools. Second, `settle_cart_mandate()` validates the `compliance_hash` field before processing — missing hash raises an exception. The LLM cannot accidentally bypass it."

---

**Q: How does session state pass between agents?**

> "Google ADK's `SequentialAgent` passes session state automatically. Each agent writes to its `output_key` — `scout_results`, `sentinel_results`, `closer_results`. The next agent reads the full accumulated context including those keys in its prompt window."

---

**Q: Can it handle multiple procurement requests concurrently?**

> "Yes — each `/run` call gets its own `session_id` and ADK session. The `InMemorySessionService` handles concurrent sessions. For production scale, swap in a persistent session store like Firestore — one config line."

---

**Q: Why Kagent?**

> "Kagent gives us cloud-agnostic Kubernetes-native agent deployment. Each agent is a CRD, scales independently, and runs on any CNCF-conformant cluster. Swapping the model backend is two lines of YAML — Vertex AI, AWS Bedrock, Azure OpenAI, and Ollama are all supported out of the box."

---

**Q: What's the $5,000 transaction cap?**

> "It's a deliberate financial control built into `generate_intent_mandate()`. The Intent Mandate's constraints field enforces `max_amount: 5000.00`. This mirrors how real AP2 mandates work — the mandate embeds the constraint, and the gateway validates it before processing."

---
