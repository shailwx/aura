"""Integration tests for the AP2 tools — Intent Mandate generation and settlement."""

from __future__ import annotations

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.ap2_tools import generate_intent_mandate, settle_cart_mandate
from tools.compliance_tools import verify_vendor_compliance
from tools.ucp_tools import discover_vendors


class TestDiscoverVendors:

    def test_returns_list(self):
        vendors = discover_vendors("laptops")
        assert isinstance(vendors, list)
        assert len(vendors) > 0

    def test_shadow_hardware_present_in_results(self):
        """Scout must expose ShadowHardware — Sentinel decides, not Scout."""
        vendors = discover_vendors("laptops")
        names = [v["name"] for v in vendors]
        assert "ShadowHardware" in names

    def test_vendors_sorted_by_price(self):
        vendors = discover_vendors("laptops")
        prices = [v["unit_price_usd"] for v in vendors]
        assert prices == sorted(prices)

    def test_vendor_has_required_fields(self):
        vendors = discover_vendors("laptops")
        required = {"id", "name", "product", "unit_price_usd", "available_units", "country"}
        for v in vendors:
            assert required.issubset(v.keys()), f"Vendor missing fields: {v}"


class TestGenerateIntentMandate:

    def test_mandate_has_correct_type(self):
        mandate = generate_intent_mandate("v-001", "TechCorp Nordic", 1299.00, compliance_hash="a" * 64)
        assert mandate["type"] == "IntentMandate"

    def test_mandate_has_id(self):
        mandate = generate_intent_mandate("v-001", "TechCorp Nordic", 1299.00, compliance_hash="a" * 64)
        assert "id" in mandate
        assert len(mandate["id"]) > 0

    def test_mandate_amount_in_constraints(self):
        mandate = generate_intent_mandate("v-001", "TechCorp Nordic", 2500.00, compliance_hash="a" * 64)
        assert mandate["constraints"]["amount"] == 2500.00
        assert mandate["constraints"]["max_amount"] == 5000.00

    def test_mandate_embeds_compliance_hash(self):
        test_hash = "b" * 64
        mandate = generate_intent_mandate("v-001", "TechCorp Nordic", 1299.00, compliance_hash=test_hash)
        assert mandate["constraints"]["compliance_hash"] == test_hash

    def test_mandate_has_ecdsa_proof(self):
        mandate = generate_intent_mandate("v-001", "TechCorp Nordic", 1299.00, compliance_hash="c" * 64)
        proof = mandate["proof"]
        assert proof["type"] == "ecdsa-p256-signature"
        assert len(proof["value"]) > 0

    def test_mandate_exceeds_max_amount_raises(self):
        with pytest.raises(ValueError, match="max_amount"):
            generate_intent_mandate("v-001", "TechCorp Nordic", 5001.00, compliance_hash="a" * 64)

    def test_mandate_missing_compliance_hash_raises(self):
        with pytest.raises(ValueError, match="compliance_hash"):
            generate_intent_mandate("v-001", "TechCorp Nordic", 1200.00, compliance_hash="")

    def test_mandate_invalid_compliance_hash_raises(self):
        with pytest.raises(ValueError, match="format"):
            generate_intent_mandate("v-001", "TechCorp Nordic", 1200.00, compliance_hash="ABC")

    def test_mandate_vendor_info_correct(self):
        mandate = generate_intent_mandate("v-001", "TechCorp Nordic", 1299.00, compliance_hash="a" * 64)
        assert mandate["vendor"]["id"] == "v-001"
        assert mandate["vendor"]["name"] == "TechCorp Nordic"


class TestSettleCartMandate:

    def _valid_mandate(self) -> dict:
        compliance = verify_vendor_compliance("TechCorp Nordic")
        return generate_intent_mandate(
            "v-001", "TechCorp Nordic", 1299.00,
            compliance_hash=compliance["compliance_hash"]
        )

    def test_settlement_returns_settled_status(self):
        mandate = self._valid_mandate()
        result = settle_cart_mandate(mandate)
        assert result["status"] == "SETTLED"

    def test_settlement_has_settlement_id(self):
        mandate = self._valid_mandate()
        result = settle_cart_mandate(mandate)
        assert "settlement_id" in result
        assert result["settlement_id"].startswith("AP2-")

    def test_settlement_amount_matches_mandate(self):
        mandate = self._valid_mandate()
        result = settle_cart_mandate(mandate)
        assert result["amount"] == 1299.00

    def test_settlement_rejects_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid mandate type"):
            settle_cart_mandate({"type": "NotAMandate"})

    def test_settlement_rejects_missing_compliance_hash(self):
        mandate = self._valid_mandate()
        mandate["constraints"]["compliance_hash"] = ""
        with pytest.raises(ValueError, match="compliance_hash"):
            settle_cart_mandate(mandate)

    def test_settlement_rejects_invalid_compliance_hash_format(self):
        mandate = self._valid_mandate()
        mandate["constraints"]["compliance_hash"] = "INVALID_HASH"
        with pytest.raises(ValueError, match="format"):
            settle_cart_mandate(mandate)

    def test_settlement_rejects_missing_proof(self):
        mandate = self._valid_mandate()
        mandate["proof"]["value"] = ""
        with pytest.raises(ValueError, match="proof"):
            settle_cart_mandate(mandate)


class TestFullPipelineTools:
    """Simulate the Scout → Sentinel → Closer tool chain without ADK."""

    def test_happy_path_no_shadow_hardware(self):
        """Full tool chain with no blacklisted vendor selected."""
        vendors = discover_vendors("laptops")
        # Pick cheapest non-ShadowHardware vendor
        approved_vendor = next(
            v for v in vendors if v["name"] != "ShadowHardware"
        )

        compliance = verify_vendor_compliance(approved_vendor["name"])
        assert compliance["status"] == "APPROVED"

        mandate = generate_intent_mandate(
            approved_vendor["id"],
            approved_vendor["name"],
            approved_vendor["unit_price_usd"],
            compliance_hash=compliance["compliance_hash"],
        )

        result = settle_cart_mandate(mandate)
        assert result["status"] == "SETTLED"
        assert result["settlement_id"].startswith("AP2-")

    def test_blocked_path_shadow_hardware(self):
        """Sentinel blocks ShadowHardware — no mandate or settlement should occur."""
        compliance = verify_vendor_compliance("ShadowHardware")
        assert compliance["status"] == "REJECTED"
        assert compliance["reason"] == "AML_BLACKLIST"

        # Closer must NOT call generate_intent_mandate with no compliance_hash.
        # The gate now fails at mandate generation itself.
        with pytest.raises(ValueError, match="compliance_hash"):
            generate_intent_mandate(
                "v-999",
                "ShadowHardware",
                899.00,
                compliance_hash="",  # no hash — compliance was rejected
            )
