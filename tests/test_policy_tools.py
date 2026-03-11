"""
Tests for tools/policy_tools.py — all six rule types.

Uses monkeypatch to inject a fresh PolicyStore per test so singleton state
never bleeds between test classes.
"""

from __future__ import annotations

import pytest

from tools.policy_store import PolicyRule, RuleType, Severity
from tools.policy_tools import (
    DailySpendStore,
    RateLimitStore,
    evaluate_payment_policy,
    evaluate_procurement_policy,
    evaluate_vendor_policy,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_store(*extra_rules: PolicyRule):
    """Return a fresh PolicyStore mock pre-loaded with given rules."""
    from tools.policy_store import PolicyStore

    obj = object.__new__(PolicyStore)
    object.__setattr__(obj, "_rules", {r.id: r for r in extra_rules})
    object.__setattr__(obj, "_rlock", __import__("threading").Lock())
    return obj


def _patch_store(monkeypatch, *rules: PolicyRule):
    store = _make_store(*rules)
    monkeypatch.setattr(
        "tools.policy_tools.PolicyStore.get_instance",
        lambda: store,
    )
    return store


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset RateLimitStore and DailySpendStore before each test."""
    RateLimitStore._instance = None
    DailySpendStore._instance = None
    yield
    RateLimitStore._instance = None
    DailySpendStore._instance = None


# ── SPENDING_LIMIT ─────────────────────────────────────────────────────────────


class TestSpendingLimit:
    _rule = PolicyRule(
        id="r-spend",
        name="Spending Limit",
        rule_type=RuleType.SPENDING_LIMIT,
        enabled=True,
        severity=Severity.BLOCK,
        parameters={"max_transaction_usd": 5000, "max_daily_usd": 20000},
        description="",
    )

    def test_allow_within_limit(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_procurement_policy({"amount_usd": 4999, "user_id": "u1"})
        assert result["decision"] == "ALLOW"

    def test_block_over_limit(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_procurement_policy({"amount_usd": 6000, "user_id": "u2"})
        assert result["decision"] == "BLOCK"
        assert any("limit" in v["reason"].lower() for v in result["violations"])

    def test_boundary_exact_limit_allows(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_procurement_policy({"amount_usd": 5000, "user_id": "u3"})
        assert result["decision"] == "ALLOW"


# ── GEO_RESTRICTION ────────────────────────────────────────────────────────────


class TestGeoRestriction:
    _rule = PolicyRule(
        id="r-geo",
        name="Geo Restriction",
        rule_type=RuleType.GEO_RESTRICTION,
        enabled=True,
        severity=Severity.BLOCK,
        parameters={"blocked_country_codes": ["IR", "KP", "RU", "SY"]},
        description="",
    )

    def test_blocked_country(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_vendor_policy({"name": "VendorX", "country": "RU"})
        assert result["decision"] == "BLOCK"
        assert any("RU" in v["reason"] for v in result["violations"])

    def test_allowed_country(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_vendor_policy({"name": "VendorY", "country": "NO"})
        assert result["decision"] == "ALLOW"
        assert result["violations"] == []

    def test_all_four_sanctioned_codes_block(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        for code in ("IR", "KP", "RU", "SY"):
            result = evaluate_vendor_policy({"name": "V", "country": code})
            assert result["decision"] == "BLOCK", f"Expected BLOCK for {code}"


# ── CATEGORY_ALLOWLIST ─────────────────────────────────────────────────────────


class TestCategoryAllowlist:
    _rule = PolicyRule(
        id="r-cat",
        name="Category Allowlist",
        rule_type=RuleType.CATEGORY_ALLOWLIST,
        enabled=True,
        severity=Severity.BLOCK,
        parameters={"allowed_categories": ["hardware", "electronics", "saas"]},
        description="",
    )

    def test_approved_category(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_procurement_policy({"category": "hardware", "user_id": "u1"})
        assert result["decision"] == "ALLOW"

    def test_denied_category(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_procurement_policy({"category": "weapons", "user_id": "u1"})
        assert result["decision"] == "BLOCK"
        assert any("allow-list" in v["reason"].lower() for v in result["violations"])

    def test_missing_category_skips_check(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_procurement_policy({"user_id": "u1"})
        assert result["decision"] == "ALLOW"


# ── APPROVAL_THRESHOLD ─────────────────────────────────────────────────────────


class TestApprovalThreshold:
    _rule = PolicyRule(
        id="r-thresh",
        name="Approval Threshold",
        rule_type=RuleType.APPROVAL_THRESHOLD,
        enabled=True,
        severity=Severity.REVIEW,
        parameters={
            "auto_approve_below_usd": 1000,
            "review_above_usd": 1000,
            "block_above_usd": 5000,
        },
        description="",
    )

    def test_auto_approve_below_threshold(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_payment_policy({"amount_usd": 500}, user_id="u1")
        assert result["decision"] == "ALLOW"

    def test_review_in_middle_band(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_payment_policy({"amount_usd": 2000}, user_id="u1")
        assert result["decision"] == "REVIEW"

    def test_block_above_ceiling(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_payment_policy({"amount_usd": 6000}, user_id="u1")
        assert result["decision"] == "BLOCK"

    def test_vendor_policy_ignores_amount(self, monkeypatch):
        """evaluate_vendor_policy does NOT apply APPROVAL_THRESHOLD — that belongs in
        evaluate_payment_policy (Closer layer), not in vendor vetting (Sentinel layer)."""
        _patch_store(monkeypatch, self._rule)
        result = evaluate_vendor_policy({"name": "V", "country": "NO"}, requested_amount=1500)
        assert result["decision"] == "ALLOW"


# ── CERTIFICATION_REQUIRED ─────────────────────────────────────────────────────


class TestCertificationRequired:
    _rule = PolicyRule(
        id="r-cert",
        name="Certifications",
        rule_type=RuleType.CERTIFICATION_REQUIRED,
        enabled=True,
        severity=Severity.WARN,
        parameters={"requirements": {"hardware": ["ISO9001"], "electronics": ["RoHS", "CE"]}},
        description="",
    )

    def test_cert_present_no_violation(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_vendor_policy(
            {"name": "V", "capability": "hardware", "certifications": ["ISO9001"]}
        )
        assert result["decision"] == "ALLOW"
        assert result["violations"] == []

    def test_cert_missing_warns(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_vendor_policy(
            {"name": "V", "capability": "hardware", "certifications": []}
        )
        assert result["decision"] == "WARN"
        assert any("ISO9001" in v["reason"] for v in result["violations"])

    def test_saas_no_requirement_allows(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_vendor_policy(
            {"name": "V", "capability": "saas", "certifications": []}
        )
        assert result["decision"] == "ALLOW"


# ── RATE_LIMIT ─────────────────────────────────────────────────────────────────


class TestRateLimit:
    _rule = PolicyRule(
        id="r-rate",
        name="Rate Limit",
        rule_type=RuleType.RATE_LIMIT,
        enabled=True,
        severity=Severity.BLOCK,
        parameters={"max_requests_per_hour": 2, "max_requests_per_day": 5},
        description="",
    )

    def test_within_limit_allows(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        r1 = evaluate_procurement_policy({"user_id": "ua"})
        r2 = evaluate_procurement_policy({"user_id": "ua"})
        assert r1["decision"] == "ALLOW"
        assert r2["decision"] == "ALLOW"

    def test_exceeds_hourly_blocks(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        evaluate_procurement_policy({"user_id": "ub"})
        evaluate_procurement_policy({"user_id": "ub"})
        result = evaluate_procurement_policy({"user_id": "ub"})
        assert result["decision"] == "BLOCK"
        assert any("rate limit" in v["reason"].lower() for v in result["violations"])

    def test_different_users_are_independent(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        for _ in range(2):
            evaluate_procurement_policy({"user_id": "uc"})
        result = evaluate_procurement_policy({"user_id": "ud"})
        assert result["decision"] == "ALLOW"


# ── DAILY_SPEND_LIMIT ──────────────────────────────────────────────────────────


class TestDailySpendLimit:
    _rule = PolicyRule(
        id="r-daily",
        name="Daily Spend",
        rule_type=RuleType.SPENDING_LIMIT,
        enabled=True,
        severity=Severity.BLOCK,
        parameters={"max_transaction_usd": 99999, "max_daily_usd": 10000},
        description="",
    )

    def test_daily_total_not_exceeded(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        DailySpendStore.get_instance().record_spend("ue", 5000)
        result = evaluate_payment_policy({"amount_usd": 4000}, user_id="ue")
        assert result["decision"] == "ALLOW"

    def test_daily_total_exceeded_blocks(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        DailySpendStore.get_instance().record_spend("uf", 8000)
        result = evaluate_payment_policy({"amount_usd": 3000}, user_id="uf")
        assert result["decision"] == "BLOCK"


# ── SNAPSHOT_HASH ──────────────────────────────────────────────────────────────


class TestSnapshotHash:
    _rule = PolicyRule(
        id="r-snap",
        name="Some Rule",
        rule_type=RuleType.SPENDING_LIMIT,
        enabled=True,
        severity=Severity.BLOCK,
        parameters={"max_transaction_usd": 1000, "max_daily_usd": 5000},
        description="",
    )

    def test_snapshot_hash_present_and_16_chars(self, monkeypatch):
        _patch_store(monkeypatch, self._rule)
        result = evaluate_procurement_policy({"amount_usd": 500, "user_id": "u1"})
        assert "snapshot_hash" in result
        assert len(result["snapshot_hash"]) == 16

    def test_snapshot_hash_changes_after_update(self, monkeypatch):
        store = _patch_store(monkeypatch, self._rule)
        h1 = store.get_snapshot_hash()
        store._rules["r-snap"].parameters["max_transaction_usd"] = 2000
        h2 = store.get_snapshot_hash()
        assert h1 != h2


# ── DISABLED_RULES ─────────────────────────────────────────────────────────────


class TestDisabledRules:
    def test_disabled_rule_is_skipped(self, monkeypatch):
        disabled = PolicyRule(
            id="r-disabled",
            name="Disabled Geo",
            rule_type=RuleType.GEO_RESTRICTION,
            enabled=False,
            severity=Severity.BLOCK,
            parameters={"blocked_country_codes": ["NO"]},
            description="",
        )
        _patch_store(monkeypatch, disabled)
        result = evaluate_vendor_policy({"name": "V", "country": "NO"})
        assert result["decision"] == "ALLOW"
        assert result["violations"] == []
