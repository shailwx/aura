# Use Cases — AURA Procurement Agent

> Real-world procurement scenarios demonstrating the full agent pipeline — from natural language request to cryptographically signed settlement.

---

## 📋 At a Glance

| Property | Value |
|----------|-------|
| **Created** | 2026-03-11 |
| **Updated** | 2026-03-11 |
| **Status** | Complete |
| **Tags** | use-cases, procurement, compliance, SSA, demo |
| **Category** | business |
| **Related** | [AGENT_FLOW.md](AGENT_FLOW.md), [ARCHITECTURE.md](ARCHITECTURE.md), [PROTOCOLS.md](PROTOCOLS.md), [DATA_MODEL.md](DATA_MODEL.md) |

---

## Table of Contents

- [Core Demo Scenarios](#core-demo-scenarios)
  - [UC-01: Happy Path — Compliant Procurement with Settlement](#uc-01-happy-path--compliant-procurement-with-settlement)
  - [UC-02: Policy Block — Governor Halts Pre-flight](#uc-02-policy-block--governor-halts-pre-flight)
  - [UC-03: Compliance Block — Sentinel Rejects, Closer Aborts](#uc-03-compliance-block--sentinel-rejects-closer-aborts)
- [SSA Contract Type Scenarios](#ssa-contract-type-scenarios)
  - [UC-04: SSA-K (Kjøp / Purchase) — Bulk Hardware](#uc-04-ssa-k-kjøp--purchase--bulk-hardware)
  - [UC-05: SSA-L (Lisens / License) — SaaS Subscription](#uc-05-ssa-l-lisens--license--saas-subscription)
  - [UC-06: SSA-D (Drift / Operations) — Managed Hosting](#uc-06-ssa-d-drift--operations--managed-hosting)
  - [UC-07: SSA-B (Bistand / Assistance) — Consulting Engagement](#uc-07-ssa-b-bistand--assistance--consulting-engagement)
  - [UC-08: SSA-T (Tjenestekjøp / Service) — Fixed-Outcome Delivery](#uc-08-ssa-t-tjenestekjøp--service--fixed-outcome-delivery)
  - [UC-09: SSA-S (Smidig / Agile) — Agile Software Sprint](#uc-09-ssa-s-smidig--agile--agile-software-sprint)
  - [UC-10: SSA-V (Vedlikehold / Maintenance) — Hardware Service Contract](#uc-10-ssa-v-vedlikehold--maintenance--hardware-service-contract)
  - [UC-11: SSA-sky (Cloud) — Government Cloud Services](#uc-11-ssa-sky-cloud--government-cloud-services)
- [Extended Real-World Scenarios](#extended-real-world-scenarios)
  - [UC-12: Volume Discount Optimization — Stacked Savings](#uc-12-volume-discount-optimization--stacked-savings)
  - [UC-13: Multi-Mandate Split — Exceeding the $5,000 Cap](#uc-13-multi-mandate-split--exceeding-the-5000-cap)
  - [UC-14: Geo-Restricted Vendor — Sanctioned Country Block](#uc-14-geo-restricted-vendor--sanctioned-country-block)
  - [UC-15: Payment Threshold Review — Manager Approval Required](#uc-15-payment-threshold-review--manager-approval-required)
  - [UC-16: Audit Trail — Compliance Hash Verification](#uc-16-audit-trail--compliance-hash-verification)
- [Scenario Matrix](#scenario-matrix)

---

## How to Read These Use Cases

Each use case follows a consistent structure:

| Section | Purpose |
|---------|---------|
| **Trigger** | The natural language request that starts the flow |
| **Agent Pipeline** | Step-by-step walkthrough of which agents execute and what they do |
| **Outcome** | The final result returned to the user |
| **Why It Matters** | The business value this scenario demonstrates |

Agent pipeline steps are marked with the agent responsible:

```
🏛️ Architect   →  ⚖️ Governor   →  🔭 Scout   →  🛡️ Sentinel   →  💳 Closer
  (parse)          (policy)        (discover)     (compliance)      (settle)
```

---

## Core Demo Scenarios

These three scenarios form the backbone of the Aura demo — they exercise every agent in the pipeline and demonstrate the compliance-first architecture that differentiates Aura from traditional procurement systems.

---

### UC-01: Happy Path — Compliant Procurement with Settlement

**Trigger**

```
"Buy 3 Laptop Pro 15 units from the best vendor"
```

**Agent Pipeline**

```
🏛️ Architect  →  ⚖️ Governor  →  🔭 Scout  →  🛡️ Sentinel  →  💳 Closer
   ✅ parse       ✅ clear        ✅ 4 found    ✅ 3 approved    ✅ settled
                                                ⛔ 1 rejected
```

1. **🏛️ Architect** parses the request → product: "Laptop Pro 15", quantity: 3, budget: unspecified.

2. **⚖️ Governor** runs pre-flight checks:
   - `evaluate_procurement_policy({category: "hardware", amount_usd: 3840})` → **ALLOW** (under $5,000 cap, category approved).
   - `classify_ssa_type({category: "hardware", is_recurring: false})` → **SSA-K** (Kjøp — one-off goods purchase).
   - Sets `governor_results.status = "POLICY_CLEAR"`.

3. **🔭 Scout** discovers vendors via UCP:
   - `discover_vendors("Laptop Pro 15")` returns 4 vendors sorted by price:

     | Vendor | Unit Price | Country | Stock |
     |--------|-----------|---------|-------|
     | ShadowHardware | $899.00 | XX | 999 |
     | NordHardware AS | $1,280.00 | NO | 30 |
     | TechCorp Nordic | $1,299.00 | NO | 50 |
     | EuroTech Supplies | $1,349.00 | DE | 120 |

   - Scout flags ShadowHardware: suspiciously low price, unknown country code "XX".
   - All 4 vendors are passed to Sentinel (no filtering — Scout discovers, Sentinel decides).

4. **🛡️ Sentinel** runs KYC/AML compliance on every vendor:
   - TechCorp Nordic → **APPROVED** (compliance hash: `SHA-256`)
   - EuroTech Supplies → **APPROVED** (compliance hash: `SHA-256`)
   - NordHardware AS → **APPROVED** (compliance hash: `SHA-256`)
   - ShadowHardware → **REJECTED** (reason: `AML_BLACKLIST`)
   - `blocked: false` — approved vendors exist, pipeline continues.

5. **💳 Closer** selects the best approved vendor and settles:
   - Picks NordHardware AS ($1,280/unit — cheapest approved vendor).
   - `calculate_bulk_price("v-003", 3)` → $1,280 × 3 = **$3,840.00** (no volume tier at qty 3, no platform rebate at ≤4 units).
   - `evaluate_payment_policy({amount: 3840})` → **ALLOW** (under $4,000 review threshold).
   - `generate_intent_mandate(vendor_id="v-003", amount=3840, compliance_hash="...")` → W3C Verifiable Credential with ECDSA-P256 signature.
   - `settle_cart_mandate(mandate)` → Settlement ID: `AP2-3X7K9F2A1B4C`.

**Outcome**

```
✅ SETTLEMENT_CONFIRMED

  Purchased:     3× Laptop Pro 15
  Vendor:        NordHardware AS (NO)
  Unit Price:    $1,280.00
  Total:         $3,840.00
  Discount:      0% (no volume tier at qty 3)
  SSA Type:      SSA-K (Kjøp)
  Settlement ID: AP2-3X7K9F2A1B4C
  Proof:         ECDSA-P256 signed IntentMandate

  ⚠️ Note: ShadowHardware excluded — AML blacklist match.
```

**Why It Matters**

- Demonstrates the full 5-agent pipeline end-to-end in a single request.
- Compliance vetting happens *before* payment — not retroactively.
- Blacklisted vendor is surfaced but never receives a payment mandate.
- Cryptographic settlement proof provides tamper-evident audit trail.

---

### UC-02: Policy Block — Governor Halts Pre-flight

**Trigger**

```
"Buy military-grade hardware from RusTech for $12,000"
```

**Agent Pipeline**

```
🏛️ Architect  →  ⚖️ Governor  →  🔭 Scout  →  🛡️ Sentinel  →  💳 Closer
   ✅ parse       ⛔ BLOCKED      ⏭️ skipped    ⏭️ skipped      ⏭️ skipped
```

1. **🏛️ Architect** parses the request → category: "military_hardware", amount: $12,000.

2. **⚖️ Governor** evaluates procurement policy:
   - `evaluate_procurement_policy({category: "military_hardware", amount_usd: 12000})`:
     - **Violation 1:** Category `military_hardware` is not in the approved category allowlist (hardware, electronics, saas, cloud, consulting, etc.).
     - **Violation 2:** Amount $12,000 exceeds the $5,000 per-transaction cap.
   - Decision: **BLOCK**.
   - Sets `governor_results.status = "POLICY_BLOCKED"`.

3. **🔭 Scout** — never called. Governor blocked the pipeline before vendor discovery.

4. **🛡️ Sentinel** — never called. No vendors to vet.

5. **💳 Closer** — reads `governor_results.status == "POLICY_BLOCKED"` → outputs `PAYMENT_ABORTED` without calling any payment tools.

**Outcome**

```
⛔ POLICY_BLOCKED

  Request:    military-grade hardware, $12,000
  Violations:
    • Category "military_hardware" not in approved procurement list
    • Amount $12,000.00 exceeds per-transaction cap ($5,000)

  No vendors were contacted.
  No compliance checks were performed.
  No payment was initiated.

  Action: Contact your procurement officer to request a category
          exception, or split the order to stay within limits.
```

**Why It Matters**

- Policy enforcement happens at the earliest possible stage — no wasted API calls.
- Governor acts as a circuit breaker: downstream agents (Scout, Sentinel, Closer) are never invoked.
- Dual violations are reported together so the requester can address all issues at once.
- Zero vendor exposure — no UCP queries leak information about a blocked request.

---

### UC-03: Compliance Block — Sentinel Rejects, Closer Aborts

**Trigger**

```
"Buy 5 laptops from ShadowHardware only"
```

**Agent Pipeline**

```
🏛️ Architect  →  ⚖️ Governor  →  🔭 Scout  →  🛡️ Sentinel  →  💳 Closer
   ✅ parse       ✅ clear        ✅ 1 found    ⛔ BLOCKED       ⛔ aborted
```

1. **🏛️ Architect** parses → product: "laptops", quantity: 5, preferred vendor: ShadowHardware.

2. **⚖️ Governor** clears pre-flight:
   - Category "hardware" is in the allowlist.
   - Estimated amount $4,495 ($899 × 5) is under the $5,000 cap.
   - `classify_ssa_type({category: "hardware"})` → **SSA-K**.
   - Sets `governor_results.status = "POLICY_CLEAR"`.

3. **🔭 Scout** discovers ShadowHardware via UCP:
   - Returns ShadowHardware: $899/unit, country "XX", 999 units available.
   - Flags: suspiciously low price, unknown country code.

4. **🛡️ Sentinel** runs compliance on ShadowHardware:
   - `evaluate_vendors_compliance(["ShadowHardware"])`:
     - ShadowHardware → **REJECTED** (reason: `AML_BLACKLIST`).
     - Country "XX" also fails geo-restriction policy → `GEO_RESTRICTION`.
   - `blocked: true` — no approved vendors remain.
   - `reason_codes: ["AML_BLACKLIST", "GEO_RESTRICTION"]`.

5. **💳 Closer** reads `sentinel_results.blocked == true`:
   - Calls **zero** payment tools.
   - Outputs `PAYMENT_ABORTED`.

**Outcome**

```
⛔ COMPLIANCE_BLOCKED / PAYMENT_ABORTED

  Vendor:      ShadowHardware
  Rejections:
    • AML_BLACKLIST — vendor appears on the anti-money-laundering blacklist
    • GEO_RESTRICTION — country "XX" is in the sanctioned territory list

  No payment mandate was generated.
  No settlement was initiated.
  Compliance audit record created with rejection reason codes.

  Action: Contact the compliance team if you believe this is an error.
          Select a different vendor and resubmit your request.
```

**Why It Matters**

- Sentinel is a hard compliance gate — if all vendors fail, the entire pipeline stops.
- Closer reads state instead of guessing — it checks `sentinel_results.blocked` before touching any payment tools.
- Multiple rejection reasons are captured (AML + geo) for complete audit trail.
- The system surfaces *why* a vendor was rejected so the requester can take informed action.

---

## SSA Contract Type Scenarios

Norway's **Statens standardavtaler** (State Standard Agreements) define the legal framework for public procurement. Aura's Governor agent automatically classifies each request into the correct SSA type, ensuring the right contract template and annexes apply.

Reference: [anskaffelser.no — Statens standardavtaler](https://www.anskaffelser.no/verktoy/statens-standardavtaler-ssa)

---

### UC-04: SSA-K (Kjøp / Purchase) — Bulk Hardware

**Trigger**

```
"Procure 10 Laptop Pro 15 for the development team"
```

**Governor Classification**

```
classify_ssa_type({
  category: "hardware",
  is_recurring: false,
  is_cloud: false,
  is_development: false,
  is_agile: false,
  is_complex: false
})
```

| Field | Value |
|-------|-------|
| **SSA Type** | SSA-K Kjøp |
| **Use Case** | One-off procurement of hardware, goods, and physical products |
| **Companion** | SSA-V (for post-purchase maintenance) |
| **Annexes** | A: Procurement requirements · B: Vendor response & pricing · C: Delivery & acceptance |
| **Reference** | [SSA-K on anskaffelser.no](https://www.anskaffelser.no/verktoy/statens-standardavtaler-ssa/ssa-k-kjop) |

**Pipeline Highlights**

- Governor selects SSA-K because the category is `hardware` and `is_recurring: false`.
- Scout discovers vendors and Scout calculates volume pricing: 10 units from NordHardware → vendor tier kicks in at qty 10+ ($1,180/unit, 7.8% off base), plus 1% platform rebate (qty 5–19) → final $1,168.20/unit.
- Total: $11,682.00 — exceeds $5,000 mandate cap → Closer issues first mandate at $5,000, notes $6,682 balance.

**Why It Matters**

SSA-K is the most common agreement for goods procurement. Automatic classification means no manual contract template selection.

---

### UC-05: SSA-L (Lisens / License) — SaaS Subscription

**Trigger**

```
"Annual subscription to CloudIDE Pro for the platform team — $4,800/year"
```

**Governor Classification**

```
classify_ssa_type({
  category: "saas",
  is_recurring: true,
  is_cloud: false,
  is_development: false,
  is_agile: false,
  is_complex: false
})
```

| Field | Value |
|-------|-------|
| **SSA Type** | SSA-L Lisens og vedlikehold |
| **Use Case** | Software licensing and recurring maintenance / SaaS subscriptions |
| **Companion** | — |
| **Annexes** | A: License scope & version · B: Maintenance & support levels · C: Pricing & fee schedule |
| **Reference** | [SSA-L on anskaffelser.no](https://www.anskaffelser.no/verktoy/statens-standardavtaler-ssa/ssa-l-lisens-og-vedlikehold) |

**Pipeline Highlights**

- Governor selects SSA-L because the category is `saas` with `is_recurring: true`.
- At $4,800, the payment policy returns **REVIEW** (≥$4,000 threshold) — manager approval required before settlement.
- Closer pauses with `PAYMENT_PENDING_REVIEW` until approval is granted.

**Why It Matters**

Recurring SaaS subscriptions need the SSA-L framework to cover license scope, support tiers, and renewal terms. Governor's automatic classification prevents accidental use of a one-off purchase agreement (SSA-K) for ongoing commitments.

---

### UC-06: SSA-D (Drift / Operations) — Managed Hosting

**Trigger**

```
"Outsource production database hosting to a managed service provider — ongoing"
```

**Governor Classification**

```
classify_ssa_type({
  category: "managed_services",
  is_recurring: true,
  is_cloud: true,
  is_development: false,
  is_agile: false,
  is_complex: false
})
```

| Field | Value |
|-------|-------|
| **SSA Type** | SSA-D Drift |
| **Use Case** | Managed operations and hosting services |
| **Companion** | SSA-L (if software licensing is bundled) |
| **Annexes** | A: Service description & SLA · B: Security & compliance requirements · C: Pricing & invoicing |
| **Reference** | [SSA-D on anskaffelser.no](https://www.anskaffelser.no/verktoy/statens-standardavtaler-ssa/ssa-d-drift) |

**Pipeline Highlights**

- Governor selects SSA-D because `managed_services` + `is_recurring: true` + `is_cloud: true`.
- Annex B (Security & compliance) is automatically flagged — Sentinel's compliance check is especially critical for hosting providers who will handle production data.

**Why It Matters**

Managed hosting agreements require SLA definitions and security specifications. SSA-D's structure ensures service levels, uptime guarantees, and data handling requirements are contractually defined before any payment flows.

---

### UC-07: SSA-B (Bistand / Assistance) — Consulting Engagement

**Trigger**

```
"Engage a senior cloud architect for 3 months, time-and-materials"
```

**Governor Classification**

```
classify_ssa_type({
  category: "consulting",
  is_recurring: false,
  is_cloud: false,
  is_development: false,
  is_agile: false,
  is_complex: false
})
```

| Field | Value |
|-------|-------|
| **SSA Type** | SSA-B Bistand |
| **Use Case** | Consulting and professional time-and-materials services |
| **Companion** | — |
| **Annexes** | A: Scope of services · B: Personnel & qualifications · C: Rates & invoicing |
| **Reference** | [SSA-B on anskaffelser.no](https://www.anskaffelser.no/verktoy/statens-standardavtaler-ssa/ssa-b-bistand) |

**Pipeline Highlights**

- Governor selects SSA-B because the category is `consulting` and the engagement is time-and-materials (not fixed-outcome).
- Annex B enforces that personnel qualifications and CV requirements are part of the contract.
- Since consulting is people-based, Sentinel's vendor compliance check validates the consulting firm's corporate registration and geo-policy status.

**Why It Matters**

Time-and-materials engagements carry cost overrun risk. SSA-B's structure defines rate cards, maximum hours, and invoicing cadence — preventing open-ended spending in a procurement-governed environment.

---

### UC-08: SSA-T (Tjenestekjøp / Service) — Fixed-Outcome Delivery

**Trigger**

```
"Build a compliance reporting dashboard — fixed price, defined deliverables"
```

**Governor Classification**

```
classify_ssa_type({
  category: "services",
  is_recurring: true,
  is_cloud: false,
  is_development: false,
  is_agile: false,
  is_complex: false
})
```

| Field | Value |
|-------|-------|
| **SSA Type** | SSA-T Tjenestekjøp |
| **Use Case** | Defined-outcome service delivery (fixed scope, fixed price) |
| **Companion** | — |
| **Annexes** | A: Service specification · B: Acceptance criteria · C: Pricing |
| **Reference** | [SSA-T on anskaffelser.no](https://www.anskaffelser.no/verktoy/statens-standardavtaler-ssa/ssa-t-tjenestekjop) |

**Pipeline Highlights**

- Governor selects SSA-T because the request describes a defined-outcome service with fixed deliverables.
- Annex B (Acceptance criteria) is critical — it defines what "done" means for fixed-price work.
- Payment is tied to deliverable acceptance, not hours worked.

**Why It Matters**

SSA-T protects the buyer by linking payment to verified deliverables. Unlike SSA-B (time-and-materials), the vendor bears the risk of scope underestimation — the price is fixed.

---

### UC-09: SSA-S (Smidig / Agile) — Agile Software Sprint

**Trigger**

```
"3-sprint agile engagement to build a customer portal — iterative delivery"
```

**Governor Classification**

```
classify_ssa_type({
  category: "agile_development",
  is_recurring: true,
  is_cloud: false,
  is_development: true,
  is_agile: true,
  is_complex: false
})
```

| Field | Value |
|-------|-------|
| **SSA Type** | SSA-S Smidig |
| **Use Case** | Agile software development with iterative delivery |
| **Companion** | — |
| **Annexes** | A: Product vision & backlog · B: Sprint cadence & definition of done · C: Team composition & rates |
| **Reference** | [SSA-S on anskaffelser.no](https://www.anskaffelser.no/verktoy/statens-standardavtaler-ssa/ssa-s-smidig) |

**Pipeline Highlights**

- Governor selects SSA-S because `is_development: true` and `is_agile: true` — the defining flags for this agreement.
- Annex A includes the product backlog, making it a living document that evolves with sprints.
- Sprint cadence and definition of done (Annex B) align with standard agile ceremony structures.

**Why It Matters**

Traditional fixed-price agreements (SSA-T) don't fit agile workflows. SSA-S was specifically created by DFØ for iterative software development, supporting sprint-based delivery, backlog reprioritization, and team composition changes — all within a government procurement framework.

---

### UC-10: SSA-V (Vedlikehold / Maintenance) — Hardware Service Contract

**Trigger**

```
"Annual maintenance contract for 50 Laptop Pro 15 units — next-business-day repair"
```

**Governor Classification**

```
classify_ssa_type({
  category: "maintenance",
  is_recurring: true,
  is_cloud: false,
  is_development: false,
  is_agile: false,
  is_complex: false
})
```

| Field | Value |
|-------|-------|
| **SSA Type** | SSA-V Vedlikehold og service |
| **Use Case** | Hardware maintenance, repair, and service agreements |
| **Companion** | SSA-K (the original purchase agreement) |
| **Annexes** | A: Equipment & asset list · B: Service levels & response times · C: Pricing |
| **Reference** | [SSA-V on anskaffelser.no](https://www.anskaffelser.no/verktoy/statens-standardavtaler-ssa/ssa-v-vedlikehold-og-service) |

**Pipeline Highlights**

- Governor selects SSA-V because the category is `maintenance` with `is_recurring: true`.
- SSA-V is the natural companion to SSA-K — if the laptops were purchased under SSA-K, the maintenance contract follows under SSA-V.
- Annex B defines SLA tiers (next-business-day, 4-hour, etc.) — critical for uptime-sensitive equipment.

**Why It Matters**

Post-purchase maintenance often falls outside the original procurement agreement. SSA-V ensures maintenance terms (response times, parts coverage, service windows) are contractually defined, not just assumed.

---

### UC-11: SSA-sky (Cloud) — Government Cloud Services

**Trigger**

```
"Provision a data warehouse platform for sensitive government datasets — full data sovereignty required"
```

**Governor Classification — Simple vs. Complex**

Aura distinguishes between two cloud agreement tiers based on data sensitivity:

| Variant | Category | `is_complex` | When to Use |
|---------|----------|--------------|-------------|
| **SSA-sky (liten)** | `cloud_infrastructure` | `false` | Standard public cloud, low data sensitivity |
| **SSA-sky (stor)** | `government_cloud` | `true` | Sensitive data, sovereignty requirements, government-grade security |

For this trigger (sensitive government data, sovereignty required), Governor selects **SSA-sky (stor)**:

```
classify_ssa_type({
  category: "government_cloud",
  is_recurring: true,
  is_cloud: true,
  is_development: false,
  is_agile: false,
  is_complex: true
})
```

| Field | Value |
|-------|-------|
| **SSA Type** | SSA-sky (stor) Skytjenester |
| **Use Case** | Complex public cloud services with sensitive government data |
| **Companion** | SSA-D (if managed operations are bundled) |
| **Annexes** | A: Cloud service description · B: Security classification & data sovereignty · C: Data processing agreement (GDPR / Norwegian data act) · D: Pricing & scaling |
| **Reference** | [SSA-sky on anskaffelser.no](https://www.anskaffelser.no/verktoy/statens-standardavtaler-ssa/ssa-sky-skytjenester) |

**Pipeline Highlights**

- Governor selects SSA-sky (stor) because `government_cloud` + `is_cloud: true` + `is_complex: true`.
- Annex B covers security classification — the cloud provider must demonstrate data sovereignty compliance.
- Annex C is a full Data Processing Agreement (DPA) required under GDPR and Norwegian data protection law.
- Sentinel's compliance check is critical: the cloud vendor's country of incorporation and data center locations must pass geo-restriction policy.

**Why It Matters**

Government data has strict sovereignty requirements. SSA-sky (stor) adds Annex B (security classification) and Annex C (DPA) that the simpler SSA-sky (liten) doesn't require. Governor's automatic detection of `is_complex: true` ensures sensitive workloads get the full contractual protection.

---

## Extended Real-World Scenarios

These scenarios demonstrate advanced capabilities beyond the core demo — volume pricing, mandate splitting, geo-restrictions, approval workflows, and audit trails.

---

### UC-12: Volume Discount Optimization — Stacked Savings

**Trigger**

```
"Buy 25 Laptop Pro 15 units for the new office buildout"
```

**Pricing Breakdown**

Aura's pricing engine applies two discount layers in sequence:

**Layer 1 — Vendor Volume Tier** (NordHardware AS, qty 25):

| Tier | Qty Range | Unit Price | Discount |
|------|-----------|-----------|----------|
| Tier 1 | 1–9 | $1,280.00 | 0% |
| **Tier 2** | **10–49** | **$1,180.00** | **7.8%** |
| Tier 3 | 50+ | $980.00 | 23.4% |

At 25 units → Tier 2 applies: **$1,180.00/unit** (7.8% off base).

**Layer 2 — AURA Platform Rebate** (qty 25):

| Tier | Qty Range | Rebate |
|------|-----------|--------|
| Standard | 0–4 | 0% |
| Volume | 5–19 | 1% |
| **Bulk** | **20+** | **2%** |

At 25 units → 2% platform rebate stacks on vendor-tier price:

```
Vendor tier price:   $1,180.00
Platform rebate:     -$23.60 (2% of $1,180.00)
Final unit price:    $1,156.40
```

**Total Savings**

```
Base total (no discounts):  25 × $1,280.00 = $32,000.00
Final total (stacked):      25 × $1,156.40 = $28,910.00
Total savings:              $3,090.00 (9.7%)
```

**Agent Pipeline**

- Governor: `POLICY_CLEAR`, SSA-K (hardware, not recurring).
- Scout: discovers all vendors, `calculate_bulk_price("v-003", 25)` shows NordHardware as best value after stacking.
- Sentinel: approves NordHardware (passes KYC/AML + geo-policy for Norway).
- Closer: total $28,910 exceeds $5,000 mandate cap → issues first mandate at $5,000, notes $23,910 balance requires additional mandates.

**Why It Matters**

Most procurement systems show a single vendor price. Aura surfaces stacked savings — vendor tier **plus** platform rebate — giving buyers a clear picture of the total cost optimization and incentivizing volume consolidation.

---

### UC-13: Multi-Mandate Split — Exceeding the $5,000 Cap

**Trigger**

```
"Buy 4 Laptop Pro 15 from NordHardware"
```

**Pricing**

- 4 units × $1,280.00/unit (Tier 1, no volume discount at qty 1–9)
- Platform rebate: 0% (qty ≤4)
- Total: **$5,120.00** — exceeds the $5,000 AP2 IntentMandate cap by $120.

**Agent Pipeline**

```
🏛️ Architect  →  ⚖️ Governor  →  🔭 Scout  →  🛡️ Sentinel  →  💳 Closer
   ✅ parse       ⚠️ WARN         ✅ found      ✅ approved      ⚠️ split
```

1. **Governor**: `evaluate_procurement_policy({amount_usd: 5120})` returns **BLOCK** — amount exceeds the $5,000 per-transaction cap. Governor instructs the user to split the order.

2. **Alternative flow**: If the order were $4,999 or less, Closer would issue a single mandate. At $5,120, the buyer must split into:
   - **Mandate 1:** 3 units × $1,280 = $3,840 (within cap)
   - **Mandate 2:** 1 unit × $1,280 = $1,280 (within cap)

**Outcome**

```
⛔ POLICY_BLOCKED

  Total amount $5,120.00 exceeds per-transaction cap ($5,000).
  Split the order or request a limit increase.

  Suggested split:
    • Order 1: 3× Laptop Pro 15 = $3,840.00
    • Order 2: 1× Laptop Pro 15 = $1,280.00
```

**Why It Matters**

The $5,000 AP2 IntentMandate cap is enforced at both the Governor level (pre-flight) and the Closer level (mandate generation). This dual enforcement prevents amount-overflow attacks where a modified request bypasses the first gate and hits the payment layer.

---

### UC-14: Geo-Restricted Vendor — Sanctioned Country Block

**Trigger**

```
"Find the cheapest server hardware — any vendor worldwide"
```

**Setup**: A vendor from a sanctioned country (e.g., RU, KP, IR, SY, or the mock country "XX") appears in UCP discovery results.

**Agent Pipeline**

```
🏛️ Architect  →  ⚖️ Governor  →  🔭 Scout  →  🛡️ Sentinel  →  💳 Closer
   ✅ parse       ✅ clear        ✅ found      ⚠️ partial      ✅/⛔
```

1. **Governor**: Clears pre-flight (category and amount within policy).

2. **Scout**: Discovers vendors from multiple countries, including one headquartered in a sanctioned territory.

3. **Sentinel** runs two checks on each vendor:
   - **KYC/AML blacklist** — checks vendor name against AML database.
   - **Geo-restriction policy** — `evaluate_vendor_policy({country: "XX"})`:
     - Country "XX" is in the sanctioned list: `{IR, KP, RU, SY, XX}`.
     - Decision: **BLOCK** — `GEO_RESTRICTION`.
   - If approved vendors remain → `blocked: false`, pipeline continues with approved vendors only.
   - If no approved vendors remain → `blocked: true`, Closer aborts.

4. **Closer**: Settles with the cheapest *approved* vendor, or aborts if none passed.

**Sanctioned Country Codes**

| Code | Country | Basis |
|------|---------|-------|
| IR | Iran | OFAC / EU sanctions |
| KP | North Korea | OFAC / UN sanctions |
| RU | Russia | OFAC / EU sanctions |
| SY | Syria | OFAC / EU sanctions |
| XX | Unknown / test | Aura mock blacklist |

**Why It Matters**

Geo-restriction is enforced at the Sentinel level independently of AML blacklisting. A vendor can have a clean AML record but still be blocked if headquartered in a sanctioned territory. This dual-layer check mirrors real-world compliance requirements under OFAC and EU sanctions regulations.

---

### UC-15: Payment Threshold Review — Manager Approval Required

**Trigger**

```
"Purchase a SaaS analytics platform license — $4,200 annual subscription"
```

**Agent Pipeline**

```
🏛️ Architect  →  ⚖️ Governor  →  🔭 Scout  →  🛡️ Sentinel  →  💳 Closer
   ✅ parse       ⚠️ REVIEW       ✅ found      ✅ approved      ⏸️ pending
```

1. **Governor**: `evaluate_procurement_policy({category: "saas", amount_usd: 4200})`:
   - Category "saas" is in the allowlist ✅
   - Amount $4,200 is under the $5,000 cap ✅
   - But $4,200 ≥ $4,000 (review threshold) → Decision: **REVIEW**
   - `governor_results.status = "POLICY_WARNINGS"` — pipeline continues with a flag.

2. **Scout** & **Sentinel**: Proceed normally — discover and vet vendors.

3. **Closer**: `evaluate_payment_policy({amount: 4200})` → **REVIEW**:
   - Payment is paused — requires manager approval before settlement.
   - Status: `PAYMENT_PENDING_REVIEW`.

**Payment Policy Thresholds**

| Amount | Decision | Action |
|--------|----------|--------|
| < $2,000 | **ALLOW** | Automatic settlement |
| $2,000–$3,999 | **WARN** | Settlement proceeds with advisory note |
| $4,000–$5,000 | **REVIEW** | Settlement paused — manager approval required |
| > $5,000 | **BLOCK** | Settlement rejected — split order |

**Outcome**

```
⏸️ PAYMENT_PENDING_REVIEW

  Vendor:     [Selected vendor]
  Amount:     $4,200.00
  SSA Type:   SSA-L (Lisens)
  Reason:     High-value procurement requires manager approval
              (threshold: $4,000.00)

  Awaiting approval to proceed with AP2 settlement.
```

**Why It Matters**

Not every procurement should auto-settle. The three-tier threshold system (WARN / REVIEW / BLOCK) provides graduated oversight — routine purchases flow through automatically while high-value transactions pause for human review, maintaining the speed advantage of automation without sacrificing control.

---

### UC-16: Audit Trail — Compliance Hash Verification

**Trigger**: A compliance officer reviews a completed procurement to verify its legitimacy.

**What's In The Audit Trail**

Every successful settlement produces a chain of cryptographic evidence:

```
1. Compliance Hash (Sentinel)
   ├─ Algorithm: SHA-256
   ├─ Input:     "COMPLIANCE:{vendor_name}:{hour_timestamp}"
   ├─ Output:    64-character hex digest
   └─ Purpose:   Proves vendor passed KYC/AML at a specific time

2. Intent Mandate (Closer)
   ├─ Type:      W3C Verifiable Credential
   ├─ Proof:     ECDSA-P256 digital signature
   ├─ Fields:
   │   ├─ vendor:           {id, name}
   │   ├─ amount:           USD value
   │   ├─ compliance_hash:  links back to Sentinel's check
   │   ├─ quantity:          units purchased
   │   └─ discount_applied: savings amount
   └─ Purpose:   Cryptographically binds payment intent to compliance proof

3. Settlement Record (AP2 Gateway)
   ├─ Settlement ID:  "AP2-{unique_id}"
   ├─ Mandate ID:     links to the IntentMandate
   ├─ Amount:         settled USD value
   ├─ Status:         "SETTLED"
   └─ Timestamp:      ISO 8601 settlement time
```

**Verification Flow**

```
Compliance Officer
       │
       ├── 1. Look up Settlement ID → retrieve mandate_id + amount
       │
       ├── 2. Look up Mandate ID → retrieve compliance_hash + vendor + proof
       │
       ├── 3. Verify ECDSA-P256 signature on the IntentMandate
       │
       ├── 4. Verify compliance_hash matches SHA-256("COMPLIANCE:{vendor}:{hour}")
       │
       └── 5. Confirm vendor passed KYC/AML at the hour the mandate was created
```

**Why It Matters**

Traditional procurement audits rely on email trails, PDF approvals, and spreadsheet logs — all of which can be altered retroactively. Aura's audit chain links settlement → mandate → compliance hash with cryptographic proofs at every step:

- **Tamper evidence**: Any modification to the mandate invalidates the ECDSA signature.
- **Temporal proof**: The compliance hash encodes the hour of the check — proving the vendor was vetted *before* payment, not after.
- **Regulatory compliance**: The W3C Verifiable Credential format aligns with emerging digital identity standards, future-proofing for regulatory requirements.

---

## Scenario Matrix

Quick reference: which agents fire, what SSA type applies, and what the outcome is for each use case.

| # | Scenario | Governor | Scout | Sentinel | Closer | SSA Type | Outcome |
|---|----------|----------|-------|----------|--------|----------|---------|
| UC-01 | Happy path (3 laptops) | ✅ CLEAR | ✅ 4 vendors | ✅ 3 approved | ✅ SETTLED | SSA-K | `SETTLEMENT_CONFIRMED` |
| UC-02 | Policy block (military, $12K) | ⛔ BLOCKED | ⏭️ skip | ⏭️ skip | ⏭️ skip | — | `POLICY_BLOCKED` |
| UC-03 | Compliance block (ShadowHW) | ✅ CLEAR | ✅ 1 vendor | ⛔ BLOCKED | ⛔ ABORTED | SSA-K | `PAYMENT_ABORTED` |
| UC-04 | Bulk hardware (10 laptops) | ✅ CLEAR | ✅ vendors | ✅ approved | ⚠️ split | SSA-K | Multi-mandate |
| UC-05 | SaaS subscription ($4,800) | ✅ CLEAR | ✅ vendors | ✅ approved | ⏸️ REVIEW | SSA-L | `PENDING_REVIEW` |
| UC-06 | Managed hosting | ✅ CLEAR | ✅ vendors | ✅ approved | ✅ SETTLED | SSA-D | `SETTLEMENT_CONFIRMED` |
| UC-07 | Consulting engagement | ✅ CLEAR | ✅ vendors | ✅ approved | ✅ SETTLED | SSA-B | `SETTLEMENT_CONFIRMED` |
| UC-08 | Fixed-outcome service | ✅ CLEAR | ✅ vendors | ✅ approved | ✅ SETTLED | SSA-T | `SETTLEMENT_CONFIRMED` |
| UC-09 | Agile sprint | ✅ CLEAR | ✅ vendors | ✅ approved | ✅ SETTLED | SSA-S | `SETTLEMENT_CONFIRMED` |
| UC-10 | Maintenance contract | ✅ CLEAR | ✅ vendors | ✅ approved | ✅ SETTLED | SSA-V | `SETTLEMENT_CONFIRMED` |
| UC-11 | Government cloud | ✅ CLEAR | ✅ vendors | ✅ approved | ✅ SETTLED | SSA-sky (stor) | `SETTLEMENT_CONFIRMED` |
| UC-12 | Volume discount (25 units) | ✅ CLEAR | ✅ vendors | ✅ approved | ⚠️ split | SSA-K | Multi-mandate |
| UC-13 | Multi-mandate split ($5,120) | ⛔ BLOCKED | ⏭️ skip | ⏭️ skip | ⏭️ skip | SSA-K | `POLICY_BLOCKED` |
| UC-14 | Geo-restricted vendor | ✅ CLEAR | ✅ vendors | ⚠️ partial | ✅/⛔ | varies | Depends on remaining |
| UC-15 | Payment threshold ($4,200) | ⚠️ REVIEW | ✅ vendors | ✅ approved | ⏸️ REVIEW | SSA-L | `PENDING_REVIEW` |
| UC-16 | Audit trail verification | — | — | — | — | — | Post-settlement |

**Legend**: ✅ pass · ⛔ blocked · ⚠️ warning/partial · ⏸️ paused · ⏭️ skipped

---

## Related Documentation

| Document | What It Covers |
|----------|---------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, agent topology, component relationships |
| [AGENT_FLOW.md](AGENT_FLOW.md) | Sequence diagrams for happy path and compliance-blocked flows |
| [DATA_MODEL.md](DATA_MODEL.md) | VendorEndpoint, IntentMandate, ComplianceReport, and SettlementRecord schemas |
| [PROTOCOLS.md](PROTOCOLS.md) | UCP (vendor discovery), AP2 (payment settlement), BMS (compliance) protocol specs |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Live demo walkthrough with timing and talking points |
| [BUSINESS_GUIDE.md](BUSINESS_GUIDE.md) | Non-technical overview, ROI, and stakeholder benefits |
