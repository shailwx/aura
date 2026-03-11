"""
Compliance Tools — Core Banking System (BMS) KYC/AML mock implementation.

In production this would call the internal BMS compliance API.
For the hackathon prototype we maintain an in-process blacklist and
return a deterministic ComplianceHash for approved vendors.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

# AML blacklist — sourced from BMS compliance database
_BLACKLISTED_VENDORS = frozenset({"ShadowHardware", "shadowhardware"})


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

    # Generate a deterministic 64-char ComplianceHash.
    # In production: returned by the BMS compliance API after KYC verification.
    raw = f"COMPLIANCE:{vendor_name}:{int(time.time() // 3600)}"
    compliance_hash = hashlib.sha256(raw.encode()).hexdigest()  # 64 hex chars

    return {
        "vendor_name": vendor_name,
        "status": "APPROVED",
        "compliance_hash": compliance_hash,
        "message": f"Vendor '{vendor_name}' passed KYC/AML checks.",
    }
