"""
Unit tests for tools/ap2_tools.py — AP2 IntentMandate generation & settlement.

Covers: mandate structure, vendor embedding, amount constraints, proof fields,
settlement ID format, missing-hash guard, and invalid mandate type guard.

Related issue: #5 [Agent] Closer — AP2 settlement unit tests
Branch: test/closer-unit
"""

import re
import uuid
import pytest
from tools.ap2_tools import generate_intent_mandate, settle_cart_mandate


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

VALID_HASH = "a" * 64  # 64-char hex placeholder

@pytest.fixture
def valid_mandate():
    return generate_intent_mandate(
        vendor_id="v-001",
        vendor_name="TechCorp Nordic",
        amount=1299.00,
        currency="USD",
        compliance_hash=VALID_HASH,
    )


# ─────────────────────────────────────────────
# generate_intent_mandate
# ─────────────────────────────────────────────

class TestGenerateIntentMandate:
    def test_type_is_intent_mandate(self, valid_mandate):
        assert valid_mandate["type"] == "IntentMandate"

    def test_id_is_valid_uuid(self, valid_mandate):
        mandate_id = valid_mandate["id"]
        assert uuid.UUID(mandate_id), "Mandate ID must be a valid UUID"

    def test_vendor_info_embedded(self, valid_mandate):
        assert valid_mandate["vendor"]["id"] == "v-001"
        assert valid_mandate["vendor"]["name"] == "TechCorp Nordic"

    def test_amount_in_constraints(self, valid_mandate):
        assert valid_mandate["constraints"]["amount"] == 1299.00

    def test_max_amount_constraint_is_5000(self, valid_mandate):
        assert valid_mandate["constraints"]["max_amount"] == 5000.00

    def test_currency_embedded(self, valid_mandate):
        assert valid_mandate["constraints"]["currency"] == "USD"

    def test_compliance_required_is_true(self, valid_mandate):
        assert valid_mandate["constraints"]["compliance_required"] is True

    def test_compliance_hash_embedded(self, valid_mandate):
        assert valid_mandate["constraints"]["compliance_hash"] == VALID_HASH

    def test_proof_type_is_ecdsa_p256(self, valid_mandate):
        assert valid_mandate["proof"]["type"] == "ecdsa-p256-signature"

    def test_proof_value_is_non_empty_string(self, valid_mandate):
        assert isinstance(valid_mandate["proof"]["value"], str)
        assert len(valid_mandate["proof"]["value"]) > 0

    def test_proof_created_timestamp_present(self, valid_mandate):
        assert isinstance(valid_mandate["proof"]["created"], int)
        assert valid_mandate["proof"]["created"] > 0

    def test_issued_at_is_int_timestamp(self, valid_mandate):
        assert isinstance(valid_mandate["issued_at"], int)
        assert valid_mandate["issued_at"] > 0

    def test_amount_at_limit_is_accepted(self):
        """Exactly 5000.00 should not raise."""
        mandate = generate_intent_mandate("v-001", "TechCorp Nordic", 5000.00, "USD", VALID_HASH)
        assert mandate["constraints"]["amount"] == 5000.00

    def test_amount_over_limit_raises(self):
        with pytest.raises(ValueError, match="5000"):
            generate_intent_mandate("v-001", "TechCorp Nordic", 5000.01, "USD", VALID_HASH)

    def test_different_calls_produce_different_mandate_ids(self):
        m1 = generate_intent_mandate("v-001", "TechCorp Nordic", 1299.00, "USD", VALID_HASH)
        m2 = generate_intent_mandate("v-001", "TechCorp Nordic", 1299.00, "USD", VALID_HASH)
        assert m1["id"] != m2["id"], "Each mandate must have a unique UUID"

    def test_default_currency_is_usd(self):
        mandate = generate_intent_mandate("v-001", "TechCorp Nordic", 1299.00, compliance_hash=VALID_HASH)
        assert mandate["constraints"]["currency"] == "USD"


# ─────────────────────────────────────────────
# settle_cart_mandate
# ─────────────────────────────────────────────

class TestSettleCartMandate:
    def test_settlement_status_is_settled(self, valid_mandate):
        result = settle_cart_mandate(valid_mandate)
        assert result["status"] == "SETTLED"

    def test_settlement_id_format(self, valid_mandate):
        result = settle_cart_mandate(valid_mandate)
        # Format: AP2-<first 12 chars of UUID uppercased>, e.g. AP2-B4497855-ED7
        assert re.match(r"^AP2-[A-F0-9-]{12}$", result["settlement_id"]), (
            f"Settlement ID must start with AP2- followed by 12 uppercase hex chars, got: {result['settlement_id']}"
        )

    def test_settlement_mandate_id_matches(self, valid_mandate):
        result = settle_cart_mandate(valid_mandate)
        assert result["mandate_id"] == valid_mandate["id"]

    def test_settlement_vendor_name_matches(self, valid_mandate):
        result = settle_cart_mandate(valid_mandate)
        assert result["vendor"] == "TechCorp Nordic"

    def test_settlement_amount_matches(self, valid_mandate):
        result = settle_cart_mandate(valid_mandate)
        assert result["amount"] == 1299.00

    def test_settlement_currency_matches(self, valid_mandate):
        result = settle_cart_mandate(valid_mandate)
        assert result["currency"] == "USD"

    def test_settled_at_is_int_timestamp(self, valid_mandate):
        result = settle_cart_mandate(valid_mandate)
        assert isinstance(result["settled_at"], int)
        assert result["settled_at"] > 0

    def test_settlement_has_message(self, valid_mandate):
        result = settle_cart_mandate(valid_mandate)
        assert "message" in result
        assert len(result["message"]) > 0

    def test_missing_compliance_hash_raises(self):
        bad_mandate = generate_intent_mandate("v-001", "TechCorp Nordic", 1299.00, "USD", "")
        with pytest.raises(ValueError, match="compliance_hash"):
            settle_cart_mandate(bad_mandate)

    def test_wrong_mandate_type_raises(self, valid_mandate):
        bad = dict(valid_mandate)
        bad["type"] = "CartMandate"
        with pytest.raises(ValueError, match="IntentMandate"):
            settle_cart_mandate(bad)

    def test_missing_proof_value_raises(self, valid_mandate):
        bad = dict(valid_mandate)
        bad["proof"] = {"type": "ecdsa-p256-signature", "value": "", "created": 0}
        with pytest.raises(ValueError, match="proof"):
            settle_cart_mandate(bad)
