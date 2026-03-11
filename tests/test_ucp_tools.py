"""
Unit tests for tools/ucp_tools.py — UCP vendor discovery.

Covers: discover_vendors() return shape, sort order, ShadowHardware presence,
VendorEndpoint field completeness, and query-agnostic behaviour.

Related issue: #3 [Agent] Scout — UCP discovery unit tests
Branch: test/scout-unit
"""

from tools.ucp_tools import discover_vendors


class TestDiscoverVendors:
    def test_returns_list_of_four_vendors(self):
        result = discover_vendors("10 laptops")
        assert isinstance(result, list)
        assert len(result) == 4

    def test_vendors_sorted_by_price_ascending(self):
        result = discover_vendors("laptops")
        prices = [v["unit_price_usd"] for v in result]
        assert prices == sorted(prices), "Vendors must be sorted by unit_price_usd ascending"

    def test_shadow_hardware_present_with_xx_country(self):
        result = discover_vendors("laptops")
        shadow = next((v for v in result if v["name"] == "ShadowHardware"), None)
        assert shadow is not None, "ShadowHardware must be present in vendor list"
        assert shadow["country"] == "XX", "ShadowHardware country must be 'XX'"

    def test_shadow_hardware_suspiciously_cheap(self):
        result = discover_vendors("laptops")
        shadow = next(v for v in result if v["name"] == "ShadowHardware")
        legitimate = [v for v in result if v["name"] != "ShadowHardware"]
        avg_price = sum(v["unit_price_usd"] for v in legitimate) / len(legitimate)
        assert shadow["unit_price_usd"] < avg_price * 0.75, (
            "ShadowHardware price should be suspiciously below legitimate vendor average"
        )

    def test_each_vendor_has_required_fields(self):
        required_fields = {
            "id", "name", "capability", "product",
            "unit_price_usd", "available_units", "ucp_endpoint", "country",
            "pricing_tiers",
        }
        result = discover_vendors("laptops")
        for vendor in result:
            missing = required_fields - set(vendor.keys())
            assert not missing, f"Vendor {vendor.get('name')} missing fields: {missing}"

    def test_pricing_tiers_is_non_empty_list(self):
        result = discover_vendors("laptops")
        for vendor in result:
            assert isinstance(vendor["pricing_tiers"], list), (
                f"Vendor {vendor['name']} pricing_tiers must be a list"
            )
            assert len(vendor["pricing_tiers"]) >= 1, (
                f"Vendor {vendor['name']} must have at least one pricing tier"
            )

    def test_pricing_tier_fields_present(self):
        result = discover_vendors("laptops")
        for vendor in result:
            for tier in vendor["pricing_tiers"]:
                assert "min_qty" in tier
                assert "unit_price_usd" in tier
                assert "discount_pct" in tier

    def test_query_does_not_filter_results(self):
        """All 4 mock vendors are returned regardless of query string."""
        result_a = discover_vendors("laptops")
        result_b = discover_vendors("something completely different")
        assert len(result_a) == len(result_b)

    def test_empty_query_returns_all_vendors(self):
        result = discover_vendors("")
        assert len(result) == 4

    def test_vendor_ids_are_unique(self):
        result = discover_vendors("laptops")
        ids = [v["id"] for v in result]
        assert len(ids) == len(set(ids)), "All vendor IDs must be unique"

    def test_all_vendors_have_ucp_shopping_capability(self):
        result = discover_vendors("laptops")
        for vendor in result:
            assert vendor["capability"] == "dev.ucp.shopping"
