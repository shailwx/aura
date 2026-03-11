# Aura — Agent Flow Diagrams

## Overview

This document shows the detailed message flow through the Aura multi-agent pipeline for two key scenarios:
1. **Happy Path** — legitimate vendor, compliance approved, payment settled
2. **Blocked Path** — blacklisted vendor detected, pipeline halted before payment

---

## Happy Path — Successful Procurement

```mermaid
sequenceDiagram
    actor User as 👤 Enterprise User
    participant Architect as 🏛️ Architect
    participant Scout as 🔭 Scout
    participant UCP as 🌐 UCP Network
    participant Sentinel as 🛡️ Sentinel
    participant BMS as 🏦 BMS Compliance DB
    participant Closer as 💳 Closer
    participant AP2 as 🔐 AP2 Gateway

    User->>Architect: "Buy 3 Laptop Pro 15 units from best vendor"

    Architect->>Scout: delegate: discover vendors for "Laptop Pro 15"
    Scout->>UCP: GET /.well-known/ucp (×4 vendors)
    UCP-->>Scout: VendorEndpoint list (TechCorp, EuroTech, NordHardware, ShadowHardware)
    Scout-->>Architect: session_state["scout_results"] = [4 vendors, sorted by price]

    Architect->>Sentinel: delegate: verify all 4 vendors
    Sentinel->>BMS: verify_vendor_compliance("TechCorp Nordic")
    BMS-->>Sentinel: {status: APPROVED, compliance_hash: "a3f9..."}
    Sentinel->>BMS: verify_vendor_compliance("EuroTech Supplies")
    BMS-->>Sentinel: {status: APPROVED, compliance_hash: "b72c..."}
    Sentinel->>BMS: verify_vendor_compliance("NordHardware AS")
    BMS-->>Sentinel: {status: APPROVED, compliance_hash: "c18d..."}
    Sentinel->>BMS: verify_vendor_compliance("ShadowHardware")
    BMS-->>Sentinel: {status: REJECTED, reason: AML_BLACKLIST}

    Note over Sentinel: ShadowHardware REJECTED<br/>but other vendors approved<br/>Sentinel flags and excludes it

    Sentinel-->>Architect: session_state["sentinel_results"] = SENTINEL_APPROVED (3 of 4)

    Architect->>Closer: delegate: settle with cheapest approved vendor (NordHardware, $1280)
    Closer->>AP2: generate_intent_mandate(vendor_id="v-003", amount=3840.00, compliance_hash="c18d...")
    AP2-->>Closer: IntentMandate {id: uuid, proof: {ecdsa-p256, signature}}
    Closer->>AP2: settle_cart_mandate(mandate)
    AP2-->>Closer: {settlement_id: "AP2-3X7K...", status: SETTLED}
    Closer-->>Architect: session_state["closer_results"] = SETTLEMENT_CONFIRMED

    Architect-->>User: ✅ Purchased 3× Laptop Pro 15 from NordHardware AS\n   Amount: $3,840.00 USD\n   Settlement ID: AP2-3X7K...\n   Note: ShadowHardware was excluded (AML blacklist)
```

---

## Blocked Path — Full Compliance Block

```mermaid
sequenceDiagram
    actor User as 👤 Enterprise User
    participant Architect as 🏛️ Architect
    participant Scout as 🔭 Scout
    participant UCP as 🌐 UCP Network
    participant Sentinel as 🛡️ Sentinel
    participant BMS as 🏦 BMS Compliance DB
    participant Closer as 💳 Closer

    User->>Architect: "Buy laptops from ShadowHardware only"

    Architect->>Scout: delegate: discover for "ShadowHardware laptops"
    Scout->>UCP: GET /.well-known/ucp
    UCP-->>Scout: [ShadowHardware only — vendor ID v-999]
    Scout-->>Architect: session_state["scout_results"] = [ShadowHardware]

    Architect->>Sentinel: delegate: verify ShadowHardware
    Sentinel->>BMS: verify_vendor_compliance("ShadowHardware")
    BMS-->>Sentinel: {status: REJECTED, reason: AML_BLACKLIST}

    Note over Sentinel: ⛔ COMPLIANCE_BLOCKED<br/>AML blacklist hit — pipeline halted

    Sentinel-->>Architect: session_state["sentinel_results"] = COMPLIANCE_BLOCKED

    Architect->>Closer: delegate (pipeline continues to Closer)
    Note over Closer: Reads COMPLIANCE_BLOCKED from session state
    Closer-->>Architect: PAYMENT_ABORTED — no payment tools called

    Architect-->>User: ⛔ Transaction blocked\n   Vendor: ShadowHardware\n   Reason: AML_BLACKLIST\n   No payment was initiated.\n   Please contact the compliance team.
```

---

## Session State Handoff

ADK passes data between agents via `session_state`. Here is the key state written at each step:

| Agent | Key Written | Value |
| :--- | :--- | :--- |
| Scout | `scout_results` | List of `VendorEndpoint` dicts |
| Sentinel | `sentinel_results` | Compliance summary (approved list + rejected list) |
| Closer | `closer_results` | Settlement result or PAYMENT_ABORTED |
