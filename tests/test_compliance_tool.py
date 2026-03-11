"""Unit tests for the compliance tool — the Sentinel's core logic."""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.compliance_tools import evaluate_vendors_compliance, verify_vendor_compliance


class TestVerifyVendorCompliance:

    def test_shadow_hardware_is_rejected(self):
        result = verify_vendor_compliance("ShadowHardware")
        assert result["status"] == "REJECTED"
        assert result["reason"] == "AML_BLACKLIST"
        assert "compliance_hash" not in result

    def test_shadow_hardware_case_insensitive(self):
        """Blacklist check must be case-insensitive."""
        for name in ["shadowhardware", "SHADOWHARDWARE", "ShadowHardware", "sHaDoWhArDwArE"]:
            result = verify_vendor_compliance(name)
            assert result["status"] == "REJECTED", f"Expected REJECTED for '{name}'"

    def test_legitimate_vendor_is_approved(self):
        result = verify_vendor_compliance("TechCorp Nordic")
        assert result["status"] == "APPROVED"
        assert "compliance_hash" in result

    def test_compliance_hash_is_64_chars(self):
        """ComplianceHash must be exactly 64 hex characters (SHA-256)."""
        result = verify_vendor_compliance("EuroTech Supplies")
        assert result["status"] == "APPROVED"
        hash_val = result["compliance_hash"]
        assert len(hash_val) == 64
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_compliance_hash_deterministic_within_hour(self):
        """Same vendor called twice in the same hour should return same hash."""
        r1 = verify_vendor_compliance("NordHardware AS")
        r2 = verify_vendor_compliance("NordHardware AS")
        assert r1["compliance_hash"] == r2["compliance_hash"]

    def test_different_vendors_get_different_hashes(self):
        r1 = verify_vendor_compliance("TechCorp Nordic")
        r2 = verify_vendor_compliance("EuroTech Supplies")
        assert r1["compliance_hash"] != r2["compliance_hash"]

    def test_vendor_name_preserved_in_result(self):
        result = verify_vendor_compliance("TechCorp Nordic")
        assert result["vendor_name"] == "TechCorp Nordic"

    def test_message_present_on_approved(self):
        result = verify_vendor_compliance("TechCorp Nordic")
        assert "message" in result
        assert "TechCorp Nordic" in result["message"]

    def test_message_present_on_rejected(self):
        result = verify_vendor_compliance("ShadowHardware")
        assert "message" in result
        assert "AML" in result["message"] or "blacklist" in result["message"].lower()


class TestEvaluateVendorsCompliance:

    def test_returns_structured_payload(self):
        decision = evaluate_vendors_compliance(
            [
                {"name": "TechCorp Nordic"},
                {"name": "ShadowHardware"},
            ]
        )
        assert set(decision.keys()) == {
            "blocked",
            "approved_vendors",
            "rejected_vendors",
            "reason_codes",
        }

    def test_blocked_when_any_rejected(self):
        decision = evaluate_vendors_compliance(
            [
                {"name": "TechCorp Nordic"},
                {"name": "ShadowHardware"},
            ]
        )
        assert decision["blocked"] is True
        assert any(v["vendor_name"] == "ShadowHardware" for v in decision["rejected_vendors"])
        assert "AML_BLACKLIST" in decision["reason_codes"]

    def test_not_blocked_when_all_approved(self):
        decision = evaluate_vendors_compliance(
            [
                {"name": "TechCorp Nordic"},
                {"name": "EuroTech Supplies"},
            ]
        )
        assert decision["blocked"] is False
        assert len(decision["approved_vendors"]) == 2
        assert decision["rejected_vendors"] == []
