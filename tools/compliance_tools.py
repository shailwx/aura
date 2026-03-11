"""
Compliance Tools — Core Banking System (BMS) KYC/AML mock implementation.

In production this would call the internal BMS compliance API.
For the hackathon prototype we maintain an in-process blacklist and
return a deterministic ComplianceHash for approved vendors.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from typing import Any, Protocol

import httpx

# AML blacklist — sourced from BMS compliance database
_BLACKLISTED_VENDORS = frozenset({"ShadowHardware", "shadowhardware"})
_COMPLIANCE_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ComplianceProvider(Protocol):
    def verify_vendor_compliance(self, vendor_name: str) -> dict[str, Any]:
        ...


class MockComplianceProvider:
    def verify_vendor_compliance(self, vendor_name: str) -> dict[str, Any]:
        normalised = vendor_name.strip().lower()
        blacklisted_normalised = {v.lower() for v in _BLACKLISTED_VENDORS}

        if normalised in blacklisted_normalised:
            return {
                "vendor_name": vendor_name,
                "status": "REJECTED",
                "reason": "AML_BLACKLIST",
                "message": (
                    f"Vendor '{vendor_name}' is on the AML blacklist. "
                    "Transaction blocked. Refer to compliance team."
                ),
            }

        raw = f"COMPLIANCE:{vendor_name}:{int(time.time() // 3600)}"
        compliance_hash = hashlib.sha256(raw.encode()).hexdigest()

        return {
            "vendor_name": vendor_name,
            "status": "APPROVED",
            "compliance_hash": compliance_hash,
            "message": f"Vendor '{vendor_name}' passed KYC/AML checks.",
        }


class BmsComplianceProvider:
    def __init__(self, endpoint: str, api_token: str | None = None, timeout_seconds: float = 10.0) -> None:
        self.endpoint = endpoint
        self.api_token = api_token
        self.timeout_seconds = timeout_seconds

    def verify_vendor_compliance(self, vendor_name: str) -> dict[str, Any]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    self.endpoint,
                    json={"vendor_name": vendor_name},
                    headers=headers,
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                "BMS compliance request failed. Verify BMS_COMPLIANCE_URL and credentials."
            ) from exc

        if not isinstance(payload, dict) or "status" not in payload:
            raise RuntimeError("BMS compliance response is invalid: expected object with 'status'.")

        status = str(payload.get("status", "")).upper()
        if status == "APPROVED":
            compliance_hash = str(payload.get("compliance_hash", ""))
            if not _COMPLIANCE_HASH_PATTERN.fullmatch(compliance_hash):
                raise RuntimeError(
                    "BMS compliance response is invalid: approved result missing valid compliance_hash."
                )

            return {
                "vendor_name": payload.get("vendor_name", vendor_name),
                "status": "APPROVED",
                "compliance_hash": compliance_hash,
                "message": payload.get("message", "Vendor approved by BMS compliance API."),
            }

        return {
            "vendor_name": payload.get("vendor_name", vendor_name),
            "status": "REJECTED",
            "reason": payload.get("reason", "UNKNOWN"),
            "message": payload.get("message", "Vendor rejected by BMS compliance API."),
        }


def _get_compliance_provider() -> ComplianceProvider:
    mode = os.getenv("AURA_PROVIDER_MODE", "mock").strip().lower()
    if mode == "mock":
        return MockComplianceProvider()

    if mode == "real":
        endpoint = os.getenv("BMS_COMPLIANCE_URL", "").strip()
        if not endpoint:
            raise RuntimeError(
                "AURA_PROVIDER_MODE=real requires BMS_COMPLIANCE_URL to be set."
            )

        token = os.getenv("BMS_COMPLIANCE_TOKEN", "").strip() or None
        return BmsComplianceProvider(endpoint=endpoint, api_token=token)

    raise RuntimeError(
        f"Unsupported AURA_PROVIDER_MODE='{mode}'. Expected 'mock' or 'real'."
    )


def evaluate_vendors_compliance(vendors: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate a full vendor list and return a structured compliance decision.

    Args:
        vendors: Vendor dicts containing at least a ``name`` field.

    Returns:
        Structured decision payload:
          - blocked: bool
          - approved_vendors: list[dict]
          - rejected_vendors: list[dict]
          - reason_codes: list[str]
    """
    approved_vendors: list[dict[str, Any]] = []
    rejected_vendors: list[dict[str, Any]] = []

    for vendor in vendors:
        vendor_name = str(vendor.get("name", "")).strip()
        if not vendor_name:
            rejected_vendors.append(
                {
                    "vendor_name": "<unknown>",
                    "reason": "INVALID_VENDOR_NAME",
                    "message": "Vendor entry missing required 'name' field.",
                }
            )
            continue

        result = verify_vendor_compliance(vendor_name)
        if result["status"] == "APPROVED":
            approved_vendors.append(
                {
                    "vendor_name": result["vendor_name"],
                    "compliance_hash": result["compliance_hash"],
                }
            )
            continue

        rejected_vendors.append(
            {
                "vendor_name": result["vendor_name"],
                "reason": result.get("reason", "UNKNOWN"),
                "message": result.get("message", "Vendor rejected by compliance."),
            }
        )

    reason_codes = sorted({entry["reason"] for entry in rejected_vendors if "reason" in entry})

    return {
        "blocked": len(rejected_vendors) > 0,
        "approved_vendors": approved_vendors,
        "rejected_vendors": rejected_vendors,
        "reason_codes": reason_codes,
    }


def verify_vendor_compliance(vendor_name: str) -> dict[str, Any]:
    """Verify a vendor against the Core Banking System (BMS) KYC/AML database.

    Performs a compliance check against the internal BMS compliance registry.
    Returns a ComplianceHash for approved vendors, or REJECTED status with
    reason code for blacklisted entities.

    This is a compliance gate — the procurement pipeline MUST NOT proceed
    to payment if this function returns status "REJECTED".

    Args:
        vendor_name: The vendor's registered trading name.

    Returns:
        dict with keys:
          - vendor_name: str
          - status: "APPROVED" | "REJECTED"
          - compliance_hash: 64-char hex string (only present if APPROVED)
          - reason: AML reason code (only present if REJECTED)
    """
    provider = _get_compliance_provider()
    return provider.verify_vendor_compliance(vendor_name)
