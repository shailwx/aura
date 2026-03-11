"""
Unit tests for tools/compliance_tools.py — KYC/AML compliance gate.

Covers: blacklist rejection (exact + case variants), APPROVED hash structure,
hash determinism, and return dict shape.

Related issue: #4 [Agent] Sentinel — KYC/AML compliance unit tests
Branch: test/sentinel-unit
"""

import re
import pytest
from tools.compliance_tools import verify_vendor_compliance


APPROVED_VENDORS = ["TechCorp Nordic", "EuroTech Supplies", "NordHardware AS"]
BLACKLISTED_VARIANTS = [
    "ShadowHardware",
    "shadowhardware",
    "SHADOWHARDWARE",
    "  ShadowHardware  ",  # leading/trailing whitespace
]


class TestBlacklist:
    @pytest.mark.parametrize("vendor_name", ["ShadowHardware", "shadowhardware"])
    def test_blacklisted_vendor_rejected(self, vendor_name):
        result = verify_vendor_compliance(vendor_name)
        assert result["status"] == "REJECTED"

    @pytest.mark.parametrize("vendor_name", ["ShadowHardware", "shadowhardware"])
    def test_rejected_reason_is_aml_blacklist(self, vendor_name):
        result = verify_vendor_compliance(vendor_name)
        assert result["reason"] == "AML_BLACKLIST"

    @pytest.mark.parametrize("vendor_name", ["ShadowHardware", "shadowhardware"])
    def test_rejected_result_has_no_compliance_hash(self, vendor_name):
        result = verify_vendor_compliance(vendor_name)
        assert "compliance_hash" not in result

    @pytest.mark.parametrize("vendor_name", ["ShadowHardware", "shadowhardware"])
    def test_rejected_result_has_message(self, vendor_name):
        result = verify_vendor_compliance(vendor_name)
        assert "message" in result
        assert len(result["message"]) > 0

    def test_whitespace_trimmed_before_blacklist_check(self):
        """Vendors with leading/trailing spaces should still be caught."""
        result = verify_vendor_compliance("  ShadowHardware  ")
        assert result["status"] == "REJECTED"


class TestApproved:
    @pytest.mark.parametrize("vendor_name", APPROVED_VENDORS)
    def test_approved_vendor_status(self, vendor_name):
        result = verify_vendor_compliance(vendor_name)
        assert result["status"] == "APPROVED"

    @pytest.mark.parametrize("vendor_name", APPROVED_VENDORS)
    def test_approved_vendor_has_compliance_hash(self, vendor_name):
        result = verify_vendor_compliance(vendor_name)
        assert "compliance_hash" in result

    @pytest.mark.parametrize("vendor_name", APPROVED_VENDORS)
    def test_compliance_hash_is_64_char_hex(self, vendor_name):
        result = verify_vendor_compliance(vendor_name)
        h = result["compliance_hash"]
        assert len(h) == 64, f"Expected 64-char hash, got {len(h)}"
        assert re.match(r"^[0-9a-f]{64}$", h), "Compliance hash must be lowercase hex"

    @pytest.mark.parametrize("vendor_name", APPROVED_VENDORS)
    def test_compliance_hash_is_deterministic_within_hour(self, vendor_name):
        """Same vendor called twice in the same hour returns identical hash."""
        result_a = verify_vendor_compliance(vendor_name)
        result_b = verify_vendor_compliance(vendor_name)
        assert result_a["compliance_hash"] == result_b["compliance_hash"]

    @pytest.mark.parametrize("vendor_name", APPROVED_VENDORS)
    def test_approved_result_has_vendor_name(self, vendor_name):
        result = verify_vendor_compliance(vendor_name)
        assert result["vendor_name"] == vendor_name

    def test_different_vendors_different_hashes(self):
        """Each vendor should produce a unique compliance hash."""
        hashes = {verify_vendor_compliance(v)["compliance_hash"] for v in APPROVED_VENDORS}
        assert len(hashes) == len(APPROVED_VENDORS), "Each vendor should have a unique compliance hash"


class TestReturnShape:
    def test_approved_result_shape(self):
        result = verify_vendor_compliance("TechCorp Nordic")
        assert set(result.keys()) >= {"vendor_name", "status", "compliance_hash", "message"}

    def test_rejected_result_shape(self):
        result = verify_vendor_compliance("ShadowHardware")
        assert set(result.keys()) >= {"vendor_name", "status", "reason", "message"}
