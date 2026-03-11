"""Tests for SSA (Statens standardavtaler) tools."""

from __future__ import annotations

import hashlib
import pytest

from tools.ssa_tools import (
    FOA_TENDER_THRESHOLD_NOK,
    FOA_TENDER_THRESHOLD_USD,
    classify_ssa_type,
    generate_ssa_contract_summary,
    validate_ssa_compliance,
)


class TestClassifySsaType:
    def test_hardware_category_returns_ssa_k(self):
        result = classify_ssa_type("hardware")
        assert result["ssa_type"] == "SSA-K"
        assert "SSA-K" in result["name"]

    def test_software_licenses_returns_ssa_l(self):
        result = classify_ssa_type("software_licenses", is_recurring=True)
        assert result["ssa_type"] == "SSA-L"

    def test_managed_services_returns_ssa_d(self):
        result = classify_ssa_type("managed_services", is_recurring=True)
        assert result["ssa_type"] == "SSA-D"

    def test_consulting_returns_ssa_b(self):
        result = classify_ssa_type("consulting")
        assert result["ssa_type"] == "SSA-B"

    def test_services_returns_ssa_t(self):
        result = classify_ssa_type("services", is_recurring=True)
        assert result["ssa_type"] == "SSA-T"

    def test_agile_development_returns_ssa_s(self):
        result = classify_ssa_type(
            "agile_development",
            is_recurring=True,
            is_development=True,
            is_agile=True,
        )
        assert result["ssa_type"] == "SSA-S"

    def test_maintenance_returns_ssa_v(self):
        result = classify_ssa_type("maintenance", is_recurring=True)
        assert result["ssa_type"] == "SSA-V"

    def test_small_cloud_returns_ssa_sky_liten(self):
        result = classify_ssa_type("hosting", is_recurring=True, is_cloud=True)
        assert result["ssa_type"] == "SSA-sky-liten"

    def test_complex_cloud_returns_ssa_sky_stor(self):
        result = classify_ssa_type(
            "cloud_infrastructure",
            is_recurring=True,
            is_cloud=True,
            is_complex=True,
        )
        assert result["ssa_type"] == "SSA-sky-stor"

    def test_result_includes_reference_url(self):
        result = classify_ssa_type("hardware")
        assert result["reference_url"].startswith("https://www.dfo.no/")

    def test_result_includes_annexes(self):
        result = classify_ssa_type("hardware")
        assert isinstance(result["annexes"], list)
        assert len(result["annexes"]) > 0

    def test_result_includes_companion_contracts(self):
        result = classify_ssa_type("software_licenses", is_recurring=True)
        assert "SSA-D" in result["companion_contracts"]

    def test_result_includes_score(self):
        result = classify_ssa_type("hardware")
        assert isinstance(result["score"], int)
        assert result["score"] >= 0


class TestValidateSsaCompliance:
    _NO_VENDOR = {"name": "TechCorp Nordic", "country": "NO", "org_number": "914325762"}
    _DE_VENDOR_WITH_ORG = {"name": "EuroTech", "country": "DE", "org_number": "123456789"}
    _DE_VENDOR_NO_ORG = {"name": "EuroTech", "country": "DE", "org_number": None}
    _XX_VENDOR = {"name": "ShadowHardware", "country": "XX", "org_number": None}

    def test_valid_norwegian_vendor_is_compliant(self):
        result = validate_ssa_compliance("SSA-K", self._NO_VENDOR, 1000.0)
        assert result["compliant"] is True
        assert result["violations"] == []

    def test_norwegian_vendor_without_org_number_has_violation(self):
        vendor = {"name": "BadNO", "country": "NO", "org_number": None}
        result = validate_ssa_compliance("SSA-K", vendor, 1000.0)
        assert result["compliant"] is False
        assert len(result["violations"]) > 0
        assert "org number" in result["violations"][0].lower()

    def test_norwegian_vendor_with_invalid_org_number_has_violation(self):
        vendor = {"name": "BadNO", "country": "NO", "org_number": "12345"}
        result = validate_ssa_compliance("SSA-K", vendor, 1000.0)
        assert result["compliant"] is False

    def test_eea_vendor_with_org_number_is_compliant(self):
        result = validate_ssa_compliance("SSA-K", self._DE_VENDOR_WITH_ORG, 1000.0)
        assert result["compliant"] is True
        assert result["violations"] == []

    def test_eea_vendor_without_org_number_gets_warning(self):
        result = validate_ssa_compliance("SSA-K", self._DE_VENDOR_NO_ORG, 1000.0)
        assert result["compliant"] is True  # warning, not violation
        assert len(result["warnings"]) > 0
        assert "lacks Norwegian org number" in result["warnings"][0]

    def test_non_eea_without_org_number_has_violation(self):
        result = validate_ssa_compliance("SSA-K", self._XX_VENDOR, 1000.0)
        assert result["compliant"] is False
        assert len(result["violations"]) > 0

    def test_amount_above_threshold_gives_foa_warning(self):
        result = validate_ssa_compliance("SSA-K", self._NO_VENDOR, FOA_TENDER_THRESHOLD_USD + 1)
        assert any("FOA §5-3" in w for w in result["warnings"])

    def test_amount_at_threshold_no_foa_warning(self):
        result = validate_ssa_compliance("SSA-K", self._NO_VENDOR, FOA_TENDER_THRESHOLD_USD)
        assert not any("FOA §5-3" in w for w in result["warnings"])

    def test_unknown_ssa_type_is_violation(self):
        result = validate_ssa_compliance("SSA-INVALID", self._NO_VENDOR, 1000.0)
        assert result["compliant"] is False
        assert any("Unknown SSA type" in v for v in result["violations"])

    def test_compliance_hash_is_64_hex_chars(self):
        result = validate_ssa_compliance("SSA-K", self._NO_VENDOR, 1000.0)
        assert len(result["ssa_compliance_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in result["ssa_compliance_hash"])

    def test_compliance_hash_is_deterministic(self):
        r1 = validate_ssa_compliance("SSA-K", self._NO_VENDOR, 1000.0)
        r2 = validate_ssa_compliance("SSA-K", self._NO_VENDOR, 1000.0)
        assert r1["ssa_compliance_hash"] == r2["ssa_compliance_hash"]

    def test_foa_threshold_is_500k_nok(self):
        assert FOA_TENDER_THRESHOLD_NOK == 500_000.0

    def test_foa_threshold_usd_is_approx_45k(self):
        assert 40_000 < FOA_TENDER_THRESHOLD_USD < 50_000


class TestGenerateSsaContractSummary:
    _VENDOR = {"name": "TechCorp Nordic", "country": "NO", "org_number": "914325762"}
    _MANDATE = {
        "id": "test-mandate-001",
        "constraints": {"amount": 12990.0, "currency": "USD"},
        "settlement_id": "AP2-TEST123",
    }

    def test_returns_correct_contract_type(self):
        result = generate_ssa_contract_summary("SSA-K", self._VENDOR, self._MANDATE)
        assert result["contract_type"] == "SSA-K"

    def test_returns_reference_url(self):
        result = generate_ssa_contract_summary("SSA-K", self._VENDOR, self._MANDATE)
        assert "dfo.no" in result["reference_url"]

    def test_returns_annexes(self):
        result = generate_ssa_contract_summary("SSA-K", self._VENDOR, self._MANDATE)
        assert len(result["annexes"]) > 0

    def test_foa_compliant_for_small_amount(self):
        result = generate_ssa_contract_summary("SSA-K", self._VENDOR, self._MANDATE)
        assert result["foa_compliant"] is True

    def test_foa_not_compliant_for_large_amount(self):
        large_mandate = {"id": "x", "constraints": {"amount": 100_000.0, "currency": "USD"}}
        result = generate_ssa_contract_summary("SSA-K", self._VENDOR, large_mandate)
        assert result["foa_compliant"] is False

    def test_contract_parties_seller_name(self):
        result = generate_ssa_contract_summary("SSA-K", self._VENDOR, self._MANDATE)
        assert result["contract_parties"]["seller"]["name"] == "TechCorp Nordic"

    def test_contract_parties_seller_org_number(self):
        result = generate_ssa_contract_summary("SSA-K", self._VENDOR, self._MANDATE)
        assert result["contract_parties"]["seller"]["org_number"] == "914325762"

    def test_procurement_details_amount(self):
        result = generate_ssa_contract_summary("SSA-K", self._VENDOR, self._MANDATE)
        assert result["procurement_details"]["amount"] == 12990.0

    def test_unknown_ssa_type_falls_back_to_ssa_k(self):
        result = generate_ssa_contract_summary("SSA-UNKNOWN", self._VENDOR, self._MANDATE)
        assert result["contract_type"] == "SSA-UNKNOWN"  # type preserved, meta from SSA-K
        assert "dfo.no" in result["reference_url"]
