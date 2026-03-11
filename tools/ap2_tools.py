"""
AP2 Tools — Agent Payments Protocol v2 mock implementation.

In production these would call the AP2 settlement network with real
W3C Verifiable Credentials. For the hackathon prototype we generate
a correctly-structured IntentMandate and simulate settlement.

AP2 spec reference: https://agent-payments-protocol.dev (emerging standard)
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import uuid
from typing import Any, Protocol

import httpx

from tools.reliability_tools import CircuitBreaker, CircuitOpenError, execute_with_retries


_COMPLIANCE_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class Ap2Provider(Protocol):
    def generate_intent_mandate(
        self,
        vendor_id: str,
        vendor_name: str,
        amount: float,
        currency: str,
        compliance_hash: str,
    ) -> dict[str, Any]:
        ...

    def settle_cart_mandate(self, mandate: dict[str, Any]) -> dict[str, Any]:
        ...


class MockAp2Provider:
    def generate_intent_mandate(
        self,
        vendor_id: str,
        vendor_name: str,
        amount: float,
        currency: str,
        compliance_hash: str,
    ) -> dict[str, Any]:
        mandate_id = str(uuid.uuid4())
        issued_at = int(time.time())

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

    def settle_cart_mandate(self, mandate: dict[str, Any]) -> dict[str, Any]:
        constraints = mandate["constraints"]
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


class HttpAp2Provider:
    def __init__(
        self,
        mandate_endpoint: str,
        settlement_endpoint: str,
        api_token: str | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.mandate_endpoint = mandate_endpoint
        self.settlement_endpoint = settlement_endpoint
        self.api_token = api_token
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = int(os.getenv("HTTP_RETRY_ATTEMPTS", "3"))
        self.retry_backoff_seconds = float(os.getenv("HTTP_RETRY_BACKOFF_SECONDS", "0.2"))
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "3")),
            reset_timeout_seconds=float(os.getenv("CIRCUIT_BREAKER_RESET_SECONDS", "30")),
        )

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def generate_intent_mandate(
        self,
        vendor_id: str,
        vendor_name: str,
        amount: float,
        currency: str,
        compliance_hash: str,
    ) -> dict[str, Any]:
        payload = {
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "amount": amount,
            "currency": currency,
            "compliance_hash": compliance_hash,
        }

        def _request() -> Any:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    self.mandate_endpoint,
                    json=payload,
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()

        try:
            mandate = execute_with_retries(
                _request,
                attempts=self.retry_attempts,
                base_backoff_seconds=self.retry_backoff_seconds,
                circuit_breaker=self._circuit_breaker,
                retryable_exceptions=(httpx.HTTPError,),
            )
        except CircuitOpenError as exc:
            raise RuntimeError(
                "AP2 circuit is open due to repeated failures. Try again later."
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                "AP2 mandate generation failed. Verify AP2_MANDATE_URL and credentials."
            ) from exc

        if not isinstance(mandate, dict) or mandate.get("type") != "IntentMandate":
            raise RuntimeError("AP2 mandate response invalid: expected IntentMandate object.")
        return mandate

    def settle_cart_mandate(self, mandate: dict[str, Any]) -> dict[str, Any]:
        headers = self._headers()
        headers["Idempotency-Key"] = build_settlement_idempotency_key(mandate)

        def _request() -> Any:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    self.settlement_endpoint,
                    json={"mandate": mandate},
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()

        try:
            result = execute_with_retries(
                _request,
                attempts=self.retry_attempts,
                base_backoff_seconds=self.retry_backoff_seconds,
                circuit_breaker=self._circuit_breaker,
                retryable_exceptions=(httpx.HTTPError,),
            )
        except CircuitOpenError as exc:
            raise RuntimeError(
                "AP2 circuit is open due to repeated failures. Try again later."
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                "AP2 settlement request failed. Verify AP2_SETTLEMENT_URL and credentials."
            ) from exc

        if not isinstance(result, dict) or "status" not in result:
            raise RuntimeError("AP2 settlement response invalid: expected object with status.")
        return result


def _get_ap2_provider() -> Ap2Provider:
    mode = os.getenv("AURA_PROVIDER_MODE", "mock").strip().lower()
    if mode == "mock":
        return MockAp2Provider()

    if mode == "real":
        mandate_endpoint = os.getenv("AP2_MANDATE_URL", "").strip()
        settlement_endpoint = os.getenv("AP2_SETTLEMENT_URL", "").strip()
        if not mandate_endpoint or not settlement_endpoint:
            raise RuntimeError(
                "AURA_PROVIDER_MODE=real requires AP2_MANDATE_URL and AP2_SETTLEMENT_URL."
            )

        token = os.getenv("AP2_API_TOKEN", "").strip() or None
        return HttpAp2Provider(
            mandate_endpoint=mandate_endpoint,
            settlement_endpoint=settlement_endpoint,
            api_token=token,
        )

    raise RuntimeError(
        f"Unsupported AURA_PROVIDER_MODE='{mode}'. Expected 'mock' or 'real'."
    )


def build_settlement_idempotency_key(mandate: dict[str, Any]) -> str:
    """Build a deterministic idempotency key for settlement requests."""
    mandate_id = str(mandate.get("id", ""))
    constraints = mandate.get("constraints", {}) if isinstance(mandate, dict) else {}
    compliance_hash = str(constraints.get("compliance_hash", ""))
    raw = f"{mandate_id}:{compliance_hash}".encode()
    return hashlib.sha256(raw).hexdigest()


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

    provider = _get_ap2_provider()
    return provider.generate_intent_mandate(
        vendor_id=vendor_id,
        vendor_name=vendor_name,
        amount=amount,
        currency=currency,
        compliance_hash=compliance_hash,
    )


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

    provider = _get_ap2_provider()
    return provider.settle_cart_mandate(mandate)
