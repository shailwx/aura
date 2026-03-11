"""
Pricing Tools — bulk purchase and volume discount engine.

Implements two-level discount stacking:
  1. Vendor-specific pricing tiers  (quantity thresholds set per-vendor in UCP)
  2. AURA platform rebate           (universal, stacks on top of the vendor tier)

The ``calculate_bulk_price`` function is the primary tool used by Scout
(to surface savings to the buyer) and Closer (to compute the discounted
mandate amount before settlement).

``get_vendor_pricing_tiers`` gives a full breakdown of all tiers for a
vendor, useful when the user explicitly asks "show me all pricing options".
"""

from __future__ import annotations

from typing import Any

from tools.ucp_tools import _MOCK_VENDOR_DB, PLATFORM_REBATE_TIERS

# Hard-coded mandate ceiling from AP2 spec (IntentMandate max_amount constraint).
_MANDATE_LIMIT_USD: float = 5000.00


def _find_vendor(vendor_id: str) -> Any | None:
    """Return the VendorEndpoint for *vendor_id*, or None if not found."""
    for v in _MOCK_VENDOR_DB:
        if v.id == vendor_id:
            return v
    return None


def _vendor_tier_price(vendor: Any, quantity: int) -> tuple[float, float]:
    """Return (unit_price_usd, discount_pct) for the applicable vendor tier.

    Evaluates against the vendor's ``pricing_tiers`` list and returns the
    tier that covers *quantity*.  Falls back to the base ``unit_price_usd``
    (0 % discount) if no tier matches — which should not happen with the
    current mock data but guards against misconfiguration.
    """
    for tier in vendor.pricing_tiers:
        above_min = quantity >= tier.min_qty
        below_max = tier.max_qty is None or quantity <= tier.max_qty
        if above_min and below_max:
            return tier.unit_price_usd, tier.discount_pct
    # Fallback: Tier-1 base price
    return vendor.unit_price_usd, 0.0


def _platform_rebate_pct(quantity: int) -> float:
    """Return the AURA platform rebate percentage for *quantity* units."""
    for tier in PLATFORM_REBATE_TIERS:
        above_min = quantity >= tier["min_qty"]
        below_max = tier["max_qty"] is None or quantity <= tier["max_qty"]
        if above_min and below_max:
            return tier["rebate_pct"]
    return 0.0


def calculate_bulk_price(vendor_id: str, quantity: int) -> dict[str, Any]:
    """Calculate the discounted bulk price for a vendor at a given quantity.

    Applies two discount layers in sequence:
      1. Vendor pricing tier  — price drops at volume thresholds set by the vendor.
      2. AURA platform rebate — additional percentage off the vendor-tier price.

    Args:
        vendor_id: UCP vendor identifier (e.g. ``"v-001"``).
        quantity:  Number of units requested. Must be >= 1.

    Returns:
        A dict with the following keys:

        - ``vendor_id``           — echo of the input vendor_id
        - ``vendor_name``         — trading name of the vendor
        - ``quantity``            — echo of the input quantity
        - ``base_unit_price``     — Tier-1 (1-unit) price in USD
        - ``vendor_tier_price``   — per-unit price after vendor volume tier
        - ``platform_rebate_pct`` — AURA rebate % stacked on top
        - ``final_unit_price``    — per-unit price after both discounts (rounded 2 dp)
        - ``total_price``         — final_unit_price × quantity (rounded 2 dp)
        - ``savings_per_unit``    — base_unit_price − final_unit_price
        - ``total_savings``       — savings_per_unit × quantity
        - ``savings_pct``         — total savings as % of base total (rounded 1 dp)
        - ``within_mandate_limit``— True if total_price <= $5,000 (AP2 cap)
        - ``error``               — present only when vendor_id is not found

    Raises:
        ValueError: If *quantity* is less than 1.
    """
    if quantity < 1:
        raise ValueError(f"quantity must be >= 1, got {quantity}")

    vendor = _find_vendor(vendor_id)
    if vendor is None:
        return {
            "error": f"Vendor '{vendor_id}' not found in UCP network.",
            "vendor_id": vendor_id,
        }

    base_unit_price = vendor.unit_price_usd
    vendor_tier_price, _vendor_discount_pct = _vendor_tier_price(vendor, quantity)
    platform_rebate_pct = _platform_rebate_pct(quantity)

    # Stack platform rebate on top of vendor-tier price
    final_unit_price = round(vendor_tier_price * (1 - platform_rebate_pct / 100), 2)
    total_price = round(final_unit_price * quantity, 2)

    savings_per_unit = round(base_unit_price - final_unit_price, 2)
    total_savings = round(savings_per_unit * quantity, 2)
    base_total = round(base_unit_price * quantity, 2)
    savings_pct = round((total_savings / base_total) * 100, 1) if base_total > 0 else 0.0

    return {
        "vendor_id": vendor_id,
        "vendor_name": vendor.name,
        "quantity": quantity,
        "base_unit_price": base_unit_price,
        "vendor_tier_price": vendor_tier_price,
        "platform_rebate_pct": platform_rebate_pct,
        "final_unit_price": final_unit_price,
        "total_price": total_price,
        "savings_per_unit": savings_per_unit,
        "total_savings": total_savings,
        "savings_pct": savings_pct,
        "within_mandate_limit": total_price <= _MANDATE_LIMIT_USD,
    }


def get_vendor_pricing_tiers(vendor_id: str) -> dict[str, Any]:
    """Return the full pricing tier table for a vendor, including platform rebates.

    Useful when the buyer asks "what are all the pricing options?" before
    deciding on a quantity.

    Args:
        vendor_id: UCP vendor identifier.

    Returns:
        A dict with:

        - ``vendor_id``       — echo of the input
        - ``vendor_name``     — trading name
        - ``base_unit_price`` — Tier-1 single-unit price
        - ``vendor_tiers``    — list of vendor tier dicts
          (``min_qty``, ``max_qty``, ``unit_price_usd``, ``discount_pct``)
        - ``platform_rebates``— list of AURA rebate tier dicts
          (``min_qty``, ``max_qty``, ``rebate_pct``)
        - ``error``           — present only when vendor_id is not found
    """
    vendor = _find_vendor(vendor_id)
    if vendor is None:
        return {
            "error": f"Vendor '{vendor_id}' not found in UCP network.",
            "vendor_id": vendor_id,
        }

    vendor_tiers = [
        {
            "min_qty": t.min_qty,
            "max_qty": t.max_qty,
            "unit_price_usd": t.unit_price_usd,
            "discount_pct": t.discount_pct,
        }
        for t in vendor.pricing_tiers
    ]

    return {
        "vendor_id": vendor_id,
        "vendor_name": vendor.name,
        "base_unit_price": vendor.unit_price_usd,
        "vendor_tiers": vendor_tiers,
        "platform_rebates": [
            {
                "min_qty": r["min_qty"],
                "max_qty": r["max_qty"],
                "rebate_pct": r["rebate_pct"],
            }
            for r in PLATFORM_REBATE_TIERS
        ],
    }
