# Aura — Protocol Design Rationale

## Overview

Aura integrates three emerging agentic commerce protocols: **UCP** (Universal Commerce Protocol), **AP2** (Agent Payments Protocol v2), and **BMS** (Core Banking System compliance interface). All three are **mocked** in this prototype. This document explains the design choices and what the real integration path looks like.

---

## Universal Commerce Protocol (UCP)

### What it is

UCP is an emerging open standard for machine-readable vendor capability discovery. It follows the same pattern as `.well-known/openid-configuration` — a vendor publishes a JSON manifest at a predictable URL that agents can query without prior coordination.

### Endpoint pattern

```
GET https://vendor.example/.well-known/ucp
```

Returns a manifest like:

```json
{
  "name": "TechCorp Nordic",
  "capabilities": ["dev.ucp.shopping", "dev.ucp.inventory"],
  "products": [
    {
      "id": "laptop-pro-15",
      "name": "Laptop Pro 15",
      "unit_price_usd": 1299.00,
      "available_units": 50,
      "currency": "USD"
    }
  ],
  "ap2_endpoint": "https://techcorp-nordic.example/ap2/checkout"
}
```

### Why mocked

The UCP SDK (`ucp-sdk-python`) is not yet publicly available. The standard is in draft at [dev.ucp.shopping](https://dev.ucp.shopping). For the hackathon, we simulate the network with 4 hardcoded vendors.

### Real integration path

Replace `tools/ucp_tools.py:discover_vendors()` with:

```python
import httpx

async def discover_vendors(query: str) -> list[dict]:
    registry_url = "https://registry.ucp.dev/api/search"
    async with httpx.AsyncClient() as client:
        r = await client.get(registry_url, params={"q": query})
        vendor_urls = r.json()["endpoints"]
    
    results = []
    for url in vendor_urls:
        manifest = await client.get(f"{url}/.well-known/ucp")
        results.append(parse_ucp_manifest(manifest.json()))
    return results
```

---

## Agent Payments Protocol v2 (AP2)

### What it is

AP2 is the payment layer for autonomous agents. It defines a **W3C Verifiable Credential** (the `IntentMandate`) that encodes:
- Who is authorised to transact
- Up to what amount
- Under what compliance conditions
- Cryptographic proof (ECDSA-P256 signature)

This allows an AI agent to initiate a payment on behalf of an enterprise without requiring a human to click "confirm" — the mandate *is* the authorisation.

### Why the signature matters

The ECDSA-P256 proof binds the mandate to a specific payment context. In production, the enterprise's HSM (Hardware Security Module) signs the mandate with the company's private key. The AP2 gateway verifies the signature before processing payment.

### Why mocked

The AP2 protocol is a hackathon-era emerging standard with no live SDK. We generate correctly-structured mandates with a SHA-256 stand-in for the ECDSA signature to demonstrate the data model and flow.

### Real integration path

Replace the mock `proof` generation in `tools/ap2_tools.py` with:

```python
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

def sign_mandate(mandate_bytes: bytes, private_key_pem: bytes) -> str:
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    signature = private_key.sign(mandate_bytes, ec.ECDSA(hashes.SHA256()))
    return signature.hex()
```

And connect `settle_cart_mandate()` to a real AP2 settlement endpoint.

---

## Core Banking System (BMS) Compliance Interface

### What it is

The BMS compliance interface is an internal enterprise API that exposes KYC (Know Your Customer) and AML (Anti-Money Laundering) check results. Before any purchase, the Sentinel queries this API with a vendor identifier to receive a compliance decision.

### Why compliance-first design matters

Traditional procurement systems check compliance *after* purchase intent is formed. Aura checks compliance *before* any payment intent is generated — this is the "Compliance-First" architecture principle that differentiates Aura from a simple shopping bot.

### The ComplianceHash

The 64-character hex `ComplianceHash` returned by an approved BMS check serves as a cryptographic receipt. It is embedded in the `IntentMandate` proof, creating an auditable chain:

```
BMS check → ComplianceHash → IntentMandate.constraints.compliance_hash → AP2 Gateway validates
```

This means the AP2 gateway can independently verify that compliance was checked before accepting the mandate.

### Why mocked

Real BMS APIs require enterprise credentials, VPN access, and regulatory agreements. For the hackathon we use a deterministic in-process SHA-256 hash of `COMPLIANCE:{vendor_name}:{hour}`.

### Real integration path

Replace `tools/compliance_tools.py:verify_vendor_compliance()` with an authenticated call to the enterprise BMS API (typically REST or gRPC behind an internal gateway).

---

## Summary

| Protocol | Standard body | Status | Aura implementation |
| :--- | :--- | :--- | :--- |
| UCP | dev.ucp.shopping | Draft | Mocked in `tools/ucp_tools.py` |
| AP2 | agent-payments-protocol.dev | Hackathon proposal | Mocked in `tools/ap2_tools.py` |
| BMS Compliance | Internal enterprise | Proprietary | Mocked in `tools/compliance_tools.py` |

All mocks are designed to be **drop-in replaceable** — the agent logic and session state handoff is unchanged when real integrations are substituted.
