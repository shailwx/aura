# Aura — Agent Flow Diagrams

## Overview

This document shows the detailed message flow through the Aura multi-agent pipeline for three key scenarios:

1. **Happy Path** — request clears all policy gates, vendor approved, payment settled
2. **Policy Block** — Governor halts the pipeline at the pre-flight stage (geo-restriction)
3. **Compliance Block** — Sentinel detects AML blacklist, Closer aborts payment

The pipeline runs in strict sequence: **Governor → Scout → Sentinel → Closer**.  
The Governor is the pre-flight gate added by the Policy Engine feature (issue #15).

---

## Scenario 1 — Happy Path (Policy Clear → Settlement)

```mermaid
sequenceDiagram
    actor User as 👤 Enterprise User
    participant Architect as 🏛️ Architect
    participant Governor as ⚖️ Governor
    participant PolicyEngine as 📋 Policy Engine
    participant Scout as 🔭 Scout
    participant UCP as 🌐 UCP Network
    participant Sentinel as 🛡️ Sentinel
    participant BMS as 🏦 BMS Compliance DB
    participant Closer as 💳 Closer
    participant AP2 as 🔐 AP2 Gateway

    User->>Architect: "Buy 3 Laptop Pro 15 units from best vendor"

    Architect->>Governor: delegate: pre-flight policy check
    Governor->>PolicyEngine: evaluate_procurement_policy({category: "hardware", amount_usd: 3840, user_id: "emp-42"})
    PolicyEngine-->>Governor: {decision: ALLOW, violations: [], snapshot_hash: "a1b2c3d4e5f6g7h8"}
    Governor-->>Architect: session_state["governor_results"] = POLICY_CLEAR

    Architect->>Scout: delegate: discover vendors for "Laptop Pro 15"
    Scout->>UCP: GET /.well-known/ucp (×4 vendors)
    UCP-->>Scout: VendorEndpoint list (TechCorp, EuroTech, NordHardware, ShadowHardware)
    Scout-->>Architect: session_state["scout_results"] = [4 vendors, sorted by price]

    Architect->>Sentinel: delegate: verify all 4 vendors
    Sentinel->>BMS: verify_vendor_compliance("TechCorp Nordic")
    BMS-->>Sentinel: {status: APPROVED, compliance_hash: "a3f9..."}
    Sentinel->>PolicyEngine: evaluate_vendor_policy({name: "TechCorp Nordic", country: "US"}, 3840)
    PolicyEngine-->>Sentinel: {decision: ALLOW, violations: []}
    Sentinel->>BMS: verify_vendor_compliance("NordHardware AS")
    BMS-->>Sentinel: {status: APPROVED, compliance_hash: "c18d..."}
    Sentinel->>PolicyEngine: evaluate_vendor_policy({name: "NordHardware AS", country: "NO"}, 3840)
    PolicyEngine-->>Sentinel: {decision: ALLOW, violations: []}
    Sentinel->>BMS: verify_vendor_compliance("ShadowHardware")
    BMS-->>Sentinel: {status: REJECTED, reason: AML_BLACKLIST}

    Note over Sentinel: ShadowHardware rejected by BMS.<br/>Cheaper options (NordHardware) remain APPROVED.

    Sentinel-->>Architect: session_state["sentinel_results"] = SENTINEL_APPROVED (NordHardware selected)

    Architect->>Closer: delegate: settle with NordHardware AS ($1,280 × 3)
    Closer->>PolicyEngine: evaluate_payment_policy({amount_usd: 3840}, user_id="emp-42")
    PolicyEngine-->>Closer: {decision: ALLOW, violations: []}
    Closer->>AP2: generate_intent_mandate(vendor_id="v-003", amount=3840.00, compliance_hash="c18d...")
    AP2-->>Closer: IntentMandate {id: uuid, proof: {ecdsa-p256, signature}}
    Closer->>AP2: settle_cart_mandate(mandate)
    AP2-->>Closer: {settlement_id: "AP2-3X7K...", status: SETTLED}
    Closer-->>Architect: session_state["closer_results"] = SETTLEMENT_CONFIRMED

    Architect-->>User: ✅ Purchased 3× Laptop Pro 15 from NordHardware AS\n   Amount: $3,840.00 USD\n   Settlement ID: AP2-3X7K...\n   Note: ShadowHardware excluded (AML blacklist)
```

---

## Scenario 2 — Policy Block (Governor halts at pre-flight)

```mermaid
sequenceDiagram
    actor User as 👤 Enterprise User
    participant Architect as 🏛️ Architect
    participant Governor as ⚖️ Governor
    participant PolicyEngine as 📋 Policy Engine
    participant Scout as 🔭 Scout

    User->>Architect: "Buy military-grade hardware from RusTech vendor"

    Architect->>Governor: delegate: pre-flight policy check
    Governor->>PolicyEngine: evaluate_procurement_policy({category: "military_hardware", amount_usd: 12000, user_id: "emp-99"})
    PolicyEngine-->>Governor: {decision: BLOCK, violations: [{rule: CATEGORY_ALLOWLIST, reason: "military_hardware not in allow-list"}, {rule: SPENDING_LIMIT, reason: "$12,000 exceeds $5,000 transaction limit"}]}
    Governor-->>Architect: session_state["governor_results"] = POLICY_BLOCKED

    Note over Architect: ⛔ governor_results = POLICY_BLOCKED<br/>Pipeline halted — Scout never called

    Architect-->>User: ⛔ Request blocked by policy engine\n   Violations:\n   • Category "military_hardware" not in allow-list\n   • Amount $12,000 exceeds transaction limit ($5,000)\n   No vendors were contacted. No payment was initiated.
```

---

## Scenario 3 — Compliance Block (Sentinel → Closer aborts)

```mermaid
sequenceDiagram
    actor User as 👤 Enterprise User
    participant Architect as 🏛️ Architect
    participant Governor as ⚖️ Governor
    participant PolicyEngine as 📋 Policy Engine
    participant Scout as 🔭 Scout
    participant UCP as 🌐 UCP Network
    participant Sentinel as 🛡️ Sentinel
    participant BMS as 🏦 BMS Compliance DB
    participant Closer as 💳 Closer

    User->>Architect: "Buy laptops from ShadowHardware only"

    Architect->>Governor: delegate: pre-flight policy check
    Governor->>PolicyEngine: evaluate_procurement_policy({category: "hardware", amount_usd: 2500, user_id: "emp-77"})
    PolicyEngine-->>Governor: {decision: ALLOW, violations: []}
    Governor-->>Architect: session_state["governor_results"] = POLICY_CLEAR

    Architect->>Scout: delegate: discover for "ShadowHardware laptops"
    Scout->>UCP: GET /.well-known/ucp
    UCP-->>Scout: [ShadowHardware only — vendor ID v-999]
    Scout-->>Architect: session_state["scout_results"] = [ShadowHardware]

    Architect->>Sentinel: delegate: verify ShadowHardware
    Sentinel->>BMS: verify_vendor_compliance("ShadowHardware")
    BMS-->>Sentinel: {status: REJECTED, reason: AML_BLACKLIST}
    Sentinel->>PolicyEngine: evaluate_vendor_policy({name: "ShadowHardware", country: "KP"}, 2500)
    PolicyEngine-->>Sentinel: {decision: BLOCK, violations: [{rule: GEO_RESTRICTION, reason: "Country KP is blocked"}]}

    Note over Sentinel: ⛔ COMPLIANCE_BLOCKED + POLICY_BLOCKED<br/>AML blacklist AND geo-restriction — no approved vendors

    Sentinel-->>Architect: session_state["sentinel_results"] = COMPLIANCE_BLOCKED

    Architect->>Closer: delegate (pipeline continues to Closer)
    Note over Closer: Reads COMPLIANCE_BLOCKED from sentinel_results<br/>No payment tools called
    Closer-->>Architect: session_state["closer_results"] = PAYMENT_ABORTED

    Architect-->>User: ⛔ Transaction blocked\n   Vendor: ShadowHardware\n   Reasons: AML_BLACKLIST + GEO_RESTRICTION (KP)\n   No payment was initiated.\n   Please contact the compliance team.
```

---

## Session State Handoff

ADK passes data between agents via `session_state`. Here is the key state written at each step:

| Agent | Key Written | Possible Values |
| :--- | :--- | :--- |
| Governor | `governor_results` | `POLICY_CLEAR` / `POLICY_WARNINGS` / `POLICY_REVIEW_REQUIRED` / `POLICY_BLOCKED` |
| Scout | `scout_results` | List of `VendorEndpoint` dicts, sorted by price |
| Sentinel | `sentinel_results` | `SENTINEL_APPROVED` / `COMPLIANCE_BLOCKED` / `POLICY_BLOCKED` / `SENTINEL_REVIEW_REQUIRED` |
| Closer | `closer_results` | `SETTLEMENT_CONFIRMED` / `PAYMENT_PENDING_REVIEW` / `PAYMENT_ABORTED` |

## Pipeline Rules

- The Architect always runs all four agents in sequence (Governor → Scout → Sentinel → Closer).
- **Closer** checks `governor_results` and `sentinel_results` before calling any payment tool. If either contains `POLICY_BLOCKED` or `COMPLIANCE_BLOCKED`, it outputs `PAYMENT_ABORTED` immediately.
- Blocking at the Governor stage does not prevent Scout/Sentinel from running (ADK `SequentialAgent` executes all sub-agents), but Closer will still abort the payment.
- Policy rules are stored in `tmp/policies.json` and managed via the `/policies` REST API (`X-Admin-Token` required for mutations).
