"""
AP2 Tools — Agent Payments Protocol v2 mock implementation.

In production these would call the AP2 settlement network with real
W3C Verifiable Credentials. For the hackathon prototype we generate
a correctly-structured IntentMandate and simulate settlement.

AP2 spec reference: https://agent-payments-protocol.dev (emerging standard)
"""

from __future__ import annotations

import hashlib
import re
import time
import uuid
from typing import Any


_COMPLIANCE_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def generate_intent_mandate(
    vendor_id: str,
    vendor_name: str,
    amount: float,
    currency: str = "USD",
    compliance_hash: str = "",
) -> dict[str, Any]:
    """Generate an AP2 Intent Mandate — a W3C Verifiable Credential authorising payment.

    The Intent Mandate is the cryptographic instrument that authorises the
    Closer agent to settle a transaction. It embeds the compliance hash from
    the Sentinel to prove the transaction passed KYC/AML checks.

    Args:
        vendor_id: UCP vendor identifier.
        vendor_name: Vendor trading name.
        amount: Transaction amount (must be <= max_amount constraint).
        currency: ISO 4217 currency code. Defaults to "USD".
        compliance_hash: ComplianceHash from the Sentinel agent.

    Returns:
        IntentMandate dict matching the AP2 / PRD data model.
    """
    if amount > 5000.00:
        raise ValueError(
            f"Amount {amount} exceeds IntentMandate max_amount constraint of 5000.00"
        )

    if not compliance_hash:
        raise ValueError(
            "Mandate missing compliance_hash. Cannot generate mandate without Sentinel approval."
        )

    if not _COMPLIANCE_HASH_PATTERN.fullmatch(compliance_hash):
        raise ValueError(
            "Invalid compliance_hash format. Expected 64 lowercase hex characters."
        )

    mandate_id = str(uuid.uuid4())
    issued_at = int(time.time())

    # ECDSA-P256 mock proof — in production: signed with enterprise private key
    proof_input = f"{mandate_id}:{vendor_id}:{amount}:{compliance_hash}"
    mock_signature = hashlib.sha256(proof_input.encode()).hexdigest().upper()

    return {
        "type": "IntentMandate",
        "id": mandate_id,
        "issued_at": issued_at,
        "vendor": {
            "id": vendor_id,
            "name": vendor_name,
        },
        "constraints": {
            "max_amount": 5000.00,
            "amount": amount,
            "currency": currency,
            "compliance_required": True,
            "compliance_hash": compliance_hash,
        },
        "proof": {
            "type": "ecdsa-p256-signature",
            "value": mock_signature,
            "created": issued_at,
        },
    }


def settle_cart_mandate(mandate: dict[str, Any]) -> dict[str, Any]:
    """Submit a signed Cart Mandate to the AP2 settlement network.

    Validates the mandate structure, routes payment through the compliant
    banking gateway, and returns a settlement confirmation.

    Args:
        mandate: A valid IntentMandate dict (from generate_intent_mandate).

    Returns:
        Settlement result dict with settlement_id, status, and timestamp.

    Raises:
        ValueError: If the mandate is malformed or compliance hash is missing.
    """
    if mandate.get("type") != "IntentMandate":
        raise ValueError("Invalid mandate type. Expected 'IntentMandate'.")

    constraints = mandate.get("constraints", {})
    if not constraints.get("compliance_hash"):
        raise ValueError(
            "Mandate missing compliance_hash. Cannot settle without Sentinel approval."
        )

    compliance_hash = str(constraints.get("compliance_hash"))
    if not _COMPLIANCE_HASH_PATTERN.fullmatch(compliance_hash):
        raise ValueError(
            "Invalid compliance_hash format. Cannot settle mandate."
        )

    proof = mandate.get("proof", {})
    if not proof.get("value"):
        raise ValueError("Mandate missing proof signature. Cannot settle.")

    # Simulate AP2 gateway processing
    settlement_id = f"AP2-{str(uuid.uuid4()).upper()[:12]}"

    return {
        "settlement_id": settlement_id,
        "mandate_id": mandate["id"],
        "vendor": mandate["vendor"]["name"],
        "amount": constraints["amount"],
        "currency": constraints["currency"],
        "status": "SETTLED",
        "gateway": "AP2_COMPLIANT_BANKING_GATEWAY",
        "settled_at": int(time.time()),
        "message": (
            f"Payment of {constraints['amount']} {constraints['currency']} "
            f"to {mandate['vendor']['name']} settled successfully via AP2."
        ),
    }
