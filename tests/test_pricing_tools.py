"""
Unit tests for tools/pricing_tools.py — bulk purchase & volume discount engine.

Covers: no-discount at Tier-1 quantity, vendor Tier-2 at 10 units, vendor Tier-3
at 50 units, platform rebate stacking on top of vendor tier, within_mandate_limit
flag, unknown vendor error handling, and get_vendor_pricing_tiers structure.

Related issue: feat/bulk-discount
"""

import pytest
from tools.pricing_tools import calculate_bulk_price, get_vendor_pricing_tiers

# NordHardware AS (v-003) — cheapest legitimate vendor, used as primary fixture
#   Tier 1: 1–9 units   → $1,280.00  (0% off)
#   Tier 2: 10–49 units → $1,180.00  (7.8% off)
#   Tier 3: 50+ units   → $980.00    (23.4% off)
# Platform rebate (AURA-wide):
#   0–4 units  → 0%
#   5–19 units → 1%
#   20+ units  → 2%

NORDHARDWARE = "v-003"
TECHCORP     = "v-001"
EUROTECH     = "v-002"
SHADOW       = "v-999"
UNKNOWN      = "v-NONEXISTENT"


# ─────────────────────────────────────────────
# calculate_bulk_price — Tier-1 (no discount)
# ─────────────────────────────────────────────

class TestTier1NoDiscount:
    def test_single_unit_returns_base_price(self):
        result = calculate_bulk_price(NORDHARDWARE, 1)
        assert result["final_unit_price"] == result["base_unit_price"]

    def test_single_unit_zero_savings(self):
        result = calculate_bulk_price(NORDHARDWARE, 1)
        assert result["savings_per_unit"] == 0.0
        assert result["total_savings"] == 0.0
        assert result["savings_pct"] == 0.0

    def test_total_price_is_unit_times_qty(self):
        result = calculate_bulk_price(NORDHARDWARE, 3)
        expected = round(result["final_unit_price"] * 3, 2)
        assert result["total_price"] == expected

    def test_within_mandate_limit_true_for_small_orders(self):
        result = calculate_bulk_price(NORDHARDWARE, 1)
        assert result["within_mandate_limit"] is True


# ─────────────────────────────────────────────
# calculate_bulk_price — Tier-2 (10-49 units)
# ─────────────────────────────────────────────

class TestTier2AtTenUnits:
    def test_vendor_tier_price_drops_at_ten(self):
        result = calculate_bulk_price(NORDHARDWARE, 10)
        # Vendor Tier-2 price for NordHardware is $1,180
        # Platform rebate at 10 units = 1% (5–19 band)
        assert result["vendor_tier_price"] == 1180.00

    def test_platform_rebate_applies_at_ten_units(self):
        result = calculate_bulk_price(NORDHARDWARE, 10)
        assert result["platform_rebate_pct"] == 1.0

    def test_final_unit_price_stacks_both_discounts(self):
        result = calculate_bulk_price(NORDHARDWARE, 10)
        # $1,180 × (1 - 0.01) = $1,168.20
        assert result["final_unit_price"] == 1168.20

    def test_savings_pct_positive_at_ten_units(self):
        result = calculate_bulk_price(NORDHARDWARE, 10)
        assert result["savings_pct"] > 0

    def test_all_required_keys_present(self):
        result = calculate_bulk_price(NORDHARDWARE, 10)
        required = {
            "vendor_id", "vendor_name", "quantity",
            "base_unit_price", "vendor_tier_price", "platform_rebate_pct",
            "final_unit_price", "total_price",
            "savings_per_unit", "total_savings", "savings_pct",
            "within_mandate_limit",
        }
        assert required.issubset(result.keys())


# ─────────────────────────────────────────────
# calculate_bulk_price — Tier-3 (50+ units)
# ─────────────────────────────────────────────

class TestTier3AtFiftyUnits:
    def test_vendor_tier_price_drops_at_fifty(self):
        result = calculate_bulk_price(NORDHARDWARE, 50)
        # Vendor Tier-3 price for NordHardware is $980
        assert result["vendor_tier_price"] == 980.00

    def test_platform_rebate_at_fifty_units_is_two_pct(self):
        result = calculate_bulk_price(NORDHARDWARE, 50)
        # 50 units falls in 20+ band → 2% platform rebate
        assert result["platform_rebate_pct"] == 2.0

    def test_final_unit_price_at_fifty_units(self):
        result = calculate_bulk_price(NORDHARDWARE, 50)
        # $980 × (1 - 0.02) = $960.40
        assert result["final_unit_price"] == 960.40

    def test_savings_pct_greater_than_tier2(self):
        tier2 = calculate_bulk_price(NORDHARDWARE, 10)
        tier3 = calculate_bulk_price(NORDHARDWARE, 50)
        assert tier3["savings_pct"] > tier2["savings_pct"]

    def test_total_savings_at_fifty_units(self):
        result = calculate_bulk_price(NORDHARDWARE, 50)
        expected_savings = round((1280.00 - 960.40) * 50, 2)
        assert result["total_savings"] == expected_savings


# ─────────────────────────────────────────────
# calculate_bulk_price — platform rebate stacking
# ─────────────────────────────────────────────

class TestPlatformRebateStacking:
    def test_rebate_zero_for_under_five_units(self):
        result = calculate_bulk_price(NORDHARDWARE, 4)
        assert result["platform_rebate_pct"] == 0.0

    def test_rebate_one_pct_for_five_to_nineteen(self):
        for qty in (5, 10, 19):
            result = calculate_bulk_price(NORDHARDWARE, qty)
            assert result["platform_rebate_pct"] == 1.0, f"Failed at qty={qty}"

    def test_rebate_two_pct_for_twenty_plus(self):
        for qty in (20, 50, 100):
            result = calculate_bulk_price(NORDHARDWARE, qty)
            assert result["platform_rebate_pct"] == 2.0, f"Failed at qty={qty}"

    def test_final_price_lower_than_vendor_tier_price_when_rebate_applies(self):
        result = calculate_bulk_price(NORDHARDWARE, 10)
        assert result["final_unit_price"] < result["vendor_tier_price"]

    def test_final_price_equals_vendor_tier_when_no_rebate(self):
        result = calculate_bulk_price(NORDHARDWARE, 1)
        assert result["final_unit_price"] == result["vendor_tier_price"]

    def test_rebate_stacks_on_vendor_tier_not_base_price(self):
        """Platform rebate should be applied after vendor tier, not on base price."""
        result = calculate_bulk_price(NORDHARDWARE, 10)
        # Vendor tier price at 10 units = $1,180 (not $1,280 base)
        expected = round(1180.00 * (1 - 1.0 / 100), 2)
        assert result["final_unit_price"] == expected


# ─────────────────────────────────────────────
# calculate_bulk_price — mandate limit flag
# ─────────────────────────────────────────────

class TestMandateLimitFlag:
    def test_within_limit_true_for_single_unit(self):
        result = calculate_bulk_price(NORDHARDWARE, 1)
        assert result["within_mandate_limit"] is True

    def test_within_limit_false_when_total_exceeds_five_thousand(self):
        # NordHardware: 50 units × $960.40 = $48,020 >> $5,000
        result = calculate_bulk_price(NORDHARDWARE, 50)
        assert result["within_mandate_limit"] is False

    def test_boundary_exactly_at_five_thousand(self):
        # TechCorp: 1 unit = $1,299 → within limit
        # Craft a scenario: 3 units of NordHardware Tier-1 = $3,840 → within limit
        result = calculate_bulk_price(NORDHARDWARE, 3)
        assert result["total_price"] <= 5000.00
        assert result["within_mandate_limit"] is True


# ─────────────────────────────────────────────
# calculate_bulk_price — error handling
# ─────────────────────────────────────────────

class TestUnknownVendor:
    def test_unknown_vendor_returns_error_dict(self):
        result = calculate_bulk_price(UNKNOWN, 5)
        assert "error" in result

    def test_unknown_vendor_error_contains_vendor_id(self):
        result = calculate_bulk_price(UNKNOWN, 5)
        assert UNKNOWN in result["error"]

    def test_invalid_quantity_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_bulk_price(NORDHARDWARE, 0)

    def test_negative_quantity_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_bulk_price(NORDHARDWARE, -1)


# ─────────────────────────────────────────────
# calculate_bulk_price — multiple vendors
# ─────────────────────────────────────────────

class TestMultipleVendors:
    def test_techcorp_tier2_price(self):
        result = calculate_bulk_price(TECHCORP, 10)
        # TechCorp Tier-2: $1,199 × (1 - 0.01) = $1,187.01
        assert result["vendor_tier_price"] == 1199.00
        assert result["final_unit_price"] == 1187.01

    def test_eurotech_tier3_price(self):
        result = calculate_bulk_price(EUROTECH, 50)
        # EuroTech Tier-3: $1,049 × (1 - 0.02) = $1,028.02
        assert result["vendor_tier_price"] == 1049.00
        assert result["final_unit_price"] == 1028.02

    def test_nordhardware_cheapest_at_tier3(self):
        nord = calculate_bulk_price(NORDHARDWARE, 50)
        tech = calculate_bulk_price(TECHCORP, 50)
        euro = calculate_bulk_price(EUROTECH, 50)
        assert nord["final_unit_price"] <= tech["final_unit_price"]
        assert nord["final_unit_price"] <= euro["final_unit_price"]


# ─────────────────────────────────────────────
# get_vendor_pricing_tiers
# ─────────────────────────────────────────────

class TestGetVendorPricingTiers:
    def test_returns_vendor_id_and_name(self):
        result = get_vendor_pricing_tiers(NORDHARDWARE)
        assert result["vendor_id"] == NORDHARDWARE
        assert result["vendor_name"] == "NordHardware AS"

    def test_returns_three_vendor_tiers(self):
        result = get_vendor_pricing_tiers(NORDHARDWARE)
        assert len(result["vendor_tiers"]) == 3

    def test_tier_fields_present(self):
        result = get_vendor_pricing_tiers(NORDHARDWARE)
        for tier in result["vendor_tiers"]:
            assert "min_qty" in tier
            assert "max_qty" in tier
            assert "unit_price_usd" in tier
            assert "discount_pct" in tier

    def test_returns_platform_rebates(self):
        result = get_vendor_pricing_tiers(NORDHARDWARE)
        rebates = result["platform_rebates"]
        assert len(rebates) == 3
        assert rebates[0]["rebate_pct"] == 0.0
        assert rebates[1]["rebate_pct"] == 1.0
        assert rebates[2]["rebate_pct"] == 2.0

    def test_unknown_vendor_returns_error(self):
        result = get_vendor_pricing_tiers(UNKNOWN)
        assert "error" in result

    def test_base_unit_price_matches_tier1(self):
        result = get_vendor_pricing_tiers(NORDHARDWARE)
        tier1_price = result["vendor_tiers"][0]["unit_price_usd"]
        assert result["base_unit_price"] == tier1_price
