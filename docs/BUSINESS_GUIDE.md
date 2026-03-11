# Aura — Business User Guide

> **Autonomous Reliable Agentic Commerce** — AI-powered B2B procurement with built-in compliance.

---

## What is Aura?

Aura is an AI system that handles your entire B2B procurement process — from finding the right supplier to completing the payment — automatically, and with compliance checks built in at every step.

Instead of manually searching for vendors, raising purchase orders, calling the compliance team, and processing payments, you simply tell Aura what you need in plain English. It does the rest.

**Example:** *"Buy 5 Laptop Pro 15 units from the best available vendor within a $7,000 budget."*  
Aura finds vendors, checks every one against your compliance database, selects the best approved supplier, and settles the payment — all without any manual intervention.

---

## The Problem Aura Solves

Traditional B2B procurement is slow and fragmented:

| Pain Point | Reality Today | Aura's Approach |
| :--- | :--- | :--- |
| Vendor sourcing | Manual research, email RFQs | Automated discovery via UCP protocol |
| Compliance vetting | Done *after* purchase intent | Checked *before* any payment is initiated |
| Payment processing | Human approval chains, payment portals | Automated via AP2 with a signed payment mandate |
| Audit trail | Spreadsheets, emails | Cryptographic proof embedded in every transaction |
| Speed | Days to weeks | Seconds to minutes |

---

## How It Works — In Plain English

Aura runs a squad of four AI agents, each with a dedicated job:

### 1. The Architect — Your Procurement Manager
Reads your request, understands what you need, and coordinates the rest of the team. It's the single point of contact you interact with.

### 2. The Scout — Your Vendor Sourcing Specialist
Searches the vendor network for suppliers who carry your product. Returns a full list with pricing and availability — including any suspicious vendors, so nothing is hidden.

### 3. The Sentinel — Your Compliance Officer
Runs every vendor through your company's compliance database (KYC/AML checks). Any vendor on the blacklist is **blocked immediately** — the pipeline stops and no money moves.

### 4. The Closer — Your Payments Team
Only activates once the Sentinel has cleared the vendors. Generates a legally-structured payment document (an *Intent Mandate*) and settles the transaction through the approved banking gateway.

```
You → Architect → Scout (find vendors) → Sentinel (compliance check) → Closer (pay)
                                               ↓ if blocked
                                          Transaction stopped. No payment made.
```

---

## What Compliance-First Means For Your Business

Most procurement tools check compliance as an afterthought — or not at all. Aura checks compliance **before the payment intent is even generated**.

This means:
- A blacklisted vendor can never receive payment, even by accident
- Every completed transaction carries a **Compliance Hash** — cryptographic proof that it was vetted
- The payment gateway independently verifies the compliance hash before processing
- You have a complete, tamper-evident audit trail for every purchase

---

## Example Scenarios

### ✅ Successful Purchase

**Your request:** "Order 3 Laptop Pro 15 units from the best vendor"

**What Aura does:**
1. Discovers 4 vendors: TechCorp Nordic ($1,299), EuroTech Supplies ($1,349), NordHardware AS ($1,280), ShadowHardware ($899)
2. Runs compliance checks on all 4 — ShadowHardware fails (AML blacklist)
3. Selects NordHardware AS (cheapest approved vendor at $1,280/unit)
4. Settles payment of $3,840 via AP2

**Result you receive:**
```
✅ Purchased 3× Laptop Pro 15 from NordHardware AS
   Amount: $3,840.00 USD
   Settlement ID: AP2-3X7K9F2A1B4C
   Note: ShadowHardware was excluded (AML blacklist)
```

---

### ⛔ Blocked Transaction

**Your request:** "Buy laptops from ShadowHardware"

**What Aura does:**
1. Discovers ShadowHardware
2. Sentinel check returns: **REJECTED — AML_BLACKLIST**
3. Pipeline halts immediately. The Closer is notified but makes zero payment calls.

**Result you receive:**
```
⛔ Transaction blocked
   Vendor: ShadowHardware
   Reason: AML_BLACKLIST
   No payment was initiated.
   Please contact the compliance team.
```

---

## Business Value Summary

| Benefit | Detail |
| :--- | :--- |
| **Speed** | Full procurement cycle in seconds instead of days |
| **Compliance** | KYC/AML checks on every vendor, every time — non-negotiable |
| **Auditability** | Every transaction has a cryptographically signed settlement record |
| **Cost efficiency** | Aura selects the cheapest compliant vendor automatically |
| **Risk reduction** | Blacklisted vendors are blocked before any financial exposure |
| **Scalability** | Handles many concurrent procurement requests without additional headcount |

---

## Current Limitations

| Limitation | Notes |
| :--- | :--- |
| **Transaction cap** | Individual transactions are capped at **$5,000 USD** per mandate |
| **Product catalogue** | Currently sourcing *Laptop Pro 15* from a mock vendor network; real UCP integration needed for production |
| **Compliance database** | Connects to your internal BMS via an internal API (real credentials required in production) |
| **Currency** | USD only in the current prototype; multi-currency via ISO 4217 codes is supported in the data model |
| **Negotiation** | Aura selects by lowest price; RFQ-style negotiation is a planned enhancement |

---

## Glossary

| Term | Plain English Meaning |
| :--- | :--- |
| **KYC** | Know Your Customer — verifying a vendor's identity and legitimacy |
| **AML** | Anti-Money Laundering — checking vendors aren't involved in financial crime |
| **UCP** | Universal Commerce Protocol — the standard vendors use to advertise products to AI agents |
| **AP2** | Agent Payments Protocol v2 — the secure payment standard for AI-to-AI commerce |
| **Intent Mandate** | A signed digital document that authorises a specific payment — replaces the human "approve payment" click |
| **Compliance Hash** | A unique code proving a vendor passed KYC/AML checks; embedded in every payment |
| **Settlement ID** | Your transaction reference number (e.g. `AP2-3X7K9F2A1B4C`) |
| **BMS** | Business Banking System — your company's internal compliance and banking infrastructure |

---

## How to Interact With Aura

Aura understands natural language. You can say things like:

- `"Buy 10 units of Laptop Pro 15 from the most reliable vendor"`
- `"Procure office furniture under $3,000 total"`
- `"Order from TechCorp Nordic if they pass compliance"`
- `"What vendors are available for Laptop Pro 15?"`
- `"Explain why ShadowHardware was blocked"`

If Aura needs more information (quantity, budget, product name), it will ask before proceeding.

---

## Accessing the Dashboard

The visual Procurement Dashboard shows the pipeline running step-by-step:

```
streamlit run ui/dashboard.py
→ Open http://localhost:8501
```

You can watch each agent (Architect, Scout, Sentinel, Closer) activate in real time, see the vendor table, compliance results, and settlement confirmation — all in one view.

See the [Dashboard Guide](DASHBOARD.md) for full details.
