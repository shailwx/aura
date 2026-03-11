"""Tests for integration provider mode selection and runtime config guards."""

from __future__ import annotations

import pytest

from tools.ap2_tools import generate_intent_mandate
from tools.compliance_tools import verify_vendor_compliance
from tools.ucp_tools import discover_vendors


def test_ucp_real_mode_requires_discovery_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AURA_PROVIDER_MODE", "real")
    monkeypatch.delenv("UCP_DISCOVERY_URL", raising=False)

    with pytest.raises(RuntimeError, match="UCP_DISCOVERY_URL"):
        discover_vendors("laptops")


def test_compliance_real_mode_requires_endpoint(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AURA_PROVIDER_MODE", "real")
    monkeypatch.delenv("BMS_COMPLIANCE_URL", raising=False)

    with pytest.raises(RuntimeError, match="BMS_COMPLIANCE_URL"):
        verify_vendor_compliance("TechCorp Nordic")


def test_ap2_real_mode_requires_endpoints(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AURA_PROVIDER_MODE", "real")
    monkeypatch.delenv("AP2_MANDATE_URL", raising=False)
    monkeypatch.delenv("AP2_SETTLEMENT_URL", raising=False)

    with pytest.raises(RuntimeError, match="AP2_MANDATE_URL"):
        generate_intent_mandate(
            vendor_id="v-001",
            vendor_name="TechCorp Nordic",
            amount=1000.00,
            currency="USD",
            compliance_hash="a" * 64,
        )


def test_mock_mode_still_works_when_mode_unset(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AURA_PROVIDER_MODE", raising=False)

    vendors = discover_vendors("laptops")
    assert len(vendors) >= 1
