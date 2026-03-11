# Aura — Hackathon Demo Script

**Event:** Google AI Agent Labs Oslo 2026  
**Team:** Team 6  
**Total time:** ~5 minutes pitch + 3 minutes live demo + 2 minutes Q&A

---

## Elevator Pitch (30 seconds)

> "We built Aura — Autonomous Reliable Agentic Commerce. It's a multi-agent AI system that automates the entire B2B procurement lifecycle: vendor discovery, KYC/AML compliance, and payment settlement — all from a single natural language request. What makes Aura unique is **compliance-first design**: we check every vendor against the compliance database *before* generating a payment mandate, not after. No human in the loop, no compliance gaps."

---

## Part 1 — Problem (60 seconds)

**Talking points:**

- B2B procurement today is **manual, slow, and fragmented** — sourcing, compliance, and payments are three separate silos
- Most AI "shopping bots" skip compliance entirely — they find a vendor and pay. That's a **financial crime risk**
- Banks and enterprises are under increasing AML/KYC regulatory pressure
- The gap we're closing: **AI agents that can transact autonomously, with built-in compliance proof on every single transaction**

**One-liner to drop:**
> "ShadowHardware looks cheap. But it's on the AML blacklist. Traditional bots would pay them. Aura blocks them — automatically, every time."

---

## Part 2 — Architecture Walkthrough (60 seconds)

Point to the architecture diagram (`docs/ARCHITECTURE.md`) or draw the flow on the whiteboard:

```
User → Architect → Scout → Sentinel → Closer → Settlement
                              ↓ BLOCKED
                         No payment ever made
```

**Key points per agent:**

| Agent | One sentence |
| :--- | :--- |
| **Architect** | Root orchestrator — parses your intent, manages the squad, summarises the outcome |
| **Scout** | Queries the UCP vendor network — finds ALL vendors, flags risky ones, never filters |
| **Sentinel** | Compliance gate — KYC/AML check on EVERY vendor via the Core Banking system. One REJECTED = full block |
| **Closer** | Generates a signed W3C Verifiable Credential (Intent Mandate) and submits to AP2 gateway — only if Sentinel approved |

**Tech stack drop:**
> "Built on Google ADK with Gemini 3.1 Flash via Vertex AI. Deployed as Kubernetes agents using Kagent v1alpha2 CRDs — so it's cloud-agnostic. Swap Gemini for Bedrock or Azure OpenAI by changing two lines of YAML."

---

## Part 3 — Live Demo (3 minutes)

### Setup (before presenting — run these in advance)

```bash
# Terminal 1 — start the dashboard
cd /path/to/aura
source .venv/bin/activate
streamlit run ui/dashboard.py
# Opens at http://localhost:8501

# Terminal 2 — optionally start the API server too
uvicorn main:app --reload --port 8080
```

---

### Demo Step 1 — Happy Path (90 seconds)

Open the dashboard at `http://localhost:8501`.

1. Type in the input box:
   ```
   Buy 3 Laptop Pro 15 units from the best available vendor
   ```
2. Click **Launch Procurement**
3. **Narrate as each agent card activates:**
   - 🏛️ Architect: *"Intent parsed — delegating to pipeline"*
   - 🔭 Scout: *"Discovers 4 vendors — including ShadowHardware at $899, suspicious but included, that's the Scout's job"*
   - 🛡️ Sentinel: *"Runs KYC/AML on all 4 — watch ShadowHardware get flagged. The other three pass with Compliance Hashes"*
   - 💳 Closer: *"Selects NordHardware at $1,280 — cheapest approved vendor. Generates an Intent Mandate, signs it, settles via AP2"*
4. **Point to the settlement card:**
   > "Settlement confirmed — $3,840, Settlement ID AP2-XXXX. And you can see ShadowHardware was excluded automatically. No one had to make a judgment call."

---

### Demo Step 2 — Compliance Block (60 seconds)

1. Clear the input and type:
   ```
   Buy laptops from ShadowHardware
   ```
2. Click **Launch Procurement** (or use the **Blocked Path** quick button)
3. **Narrate:**
   - Scout finds ShadowHardware
   - Sentinel hits the BMS compliance check — **REJECTED: AML_BLACKLIST**
   - Closer card turns red: **PAYMENT_ABORTED** — zero payment tools called
4. **Key line:**
   > "The Closer never even saw a payment request. The Compliance Hash was never generated. There is no way for money to move to a blacklisted vendor — it's architectural."

---

### Optional Demo — API (30 seconds, if time permits)

```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Buy 3 Laptop Pro 15 units from best vendor"}'
```

> "It's also a REST API — so any enterprise system can plug in. Multi-turn sessions, streaming responses, Kubernetes-native."

---

## Part 4 — Key Differentiators (30 seconds)

> Three things that make Aura different:
>
> 1. **Compliance-first, not compliance-after** — the Compliance Hash is embedded in the payment mandate. The gateway verifies it independently. No compliance, no payment — architecturally enforced.
>
> 2. **Verifiable payment mandates** — W3C Verifiable Credential structure with ECDSA-P256 proof. Every transaction is cryptographically auditable.
>
> 3. **Cloud-agnostic, Kubernetes-native** — Kagent CRDs means each agent scales independently and runs on GCP, AWS, Azure, or on-premise.

---

## Anticipated Judge Questions

**Q: This is a mock — how close is it to production?**
> "The agent logic, pipeline, session state handoff, and data structures are all production-grade. The three integrations that are mocked — UCP vendor discovery, BMS compliance API, and AP2 settlement — are all designed as drop-in replacements. The `tools/` layer is fully decoupled from the agent reasoning layer. Replacing mock with real is a single function swap per tool."

**Q: What's to stop the LLM from ignoring the Sentinel's output?**
> "Two layers of safety. First, the Closer's system prompt has an explicit hard override: if `COMPLIANCE_BLOCKED` appears anywhere in session state, output `PAYMENT_ABORTED` and call no tools. Second, `settle_cart_mandate()` validates the `compliance_hash` field before processing — no hash means an exception is raised. The LLM can't accidentally bypass it."

**Q: How does session state pass between agents?**
> "Google ADK's `SequentialAgent` passes session state automatically. Each agent writes to its `output_key` — `scout_results`, `sentinel_results`, `closer_results`. The next agent reads the full accumulated context including those keys in its prompt window."

**Q: Can it handle multiple procurement requests concurrently?**
> "Yes — each `/run` call gets its own `session_id` and ADK session. The `InMemorySessionService` handles concurrent sessions. For production scale, we'd swap in a persistent session store like Firestore."

**Q: Why Kagent?**
> "Kagent gives us cloud-agnostic Kubernetes-native agent deployment. Each agent is a CRD, scales independently, and can run on any CNCF-conformant cluster. Swapping the model backend is two lines of YAML — we support Vertex AI, AWS Bedrock, Azure OpenAI, and Ollama out of the box."

**Q: What's the $5,000 transaction cap?**
> "That's a deliberate financial control built into `generate_intent_mandate()`. The Intent Mandate's constraints field enforces `max_amount: 5000.00`. This mirrors how real AP2 mandates work — the mandate embeds the constraint, and the gateway validates it before processing."

---

## Closing Line

> "Aura is what B2B commerce looks like when agents are first-class participants — not just bots that scrape prices, but autonomous actors that discover, vet, and pay with cryptographic proof at every step. Thank you."

---

## Quick Reference Links

| What | Where |
| :--- | :--- |
| Dashboard | `http://localhost:8501` |
| API Swagger UI | `http://localhost:8080/docs` |
| Architecture diagram | `docs/ARCHITECTURE.md` |
| Agent flow diagrams | `docs/AGENT_FLOW.md` |
| Business Guide | `docs/BUSINESS_GUIDE.md` |
| Technical Guide | `docs/TECHNICAL_GUIDE.md` |
