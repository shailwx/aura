"""
UCP Tools — Universal Commerce Protocol mock implementation.

In production this would hit real /.well-known/ucp endpoints.
For the hackathon prototype we return a curated vendor list that
includes a deliberately blacklisted vendor (ShadowHardware) to
exercise the Sentinel compliance path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, asdict, field
from typing import Any, Protocol

import httpx



@dataclass
class PricingTier:
    """A single volume pricing tier offered by a vendor.

    Attributes:
        min_qty: Minimum number of units for this tier to apply (inclusive).
        max_qty: Maximum number of units for this tier (inclusive); None = no upper bound.
        unit_price_usd: Per-unit price in USD at this tier.
        discount_pct: Percentage discount off the base (Tier-1) price.
    """

    min_qty: int
    max_qty: int | None
    unit_price_usd: float
    discount_pct: float


# Platform-level rebate applied on top of any vendor tier.
# These percentages are deducted from the vendor-tier unit price.
PLATFORM_REBATE_TIERS: list[dict[str, Any]] = [
    {"min_qty": 0,  "max_qty": 4,    "rebate_pct": 0.0},
    {"min_qty": 5,  "max_qty": 19,   "rebate_pct": 1.0},
    {"min_qty": 20, "max_qty": None,  "rebate_pct": 2.0},
]


@dataclass
class VendorEndpoint:
    id: str
    name: str
    capability: str
    product: str
    unit_price_usd: float          # Tier-1 (base) price — kept for backward compatibility
    available_units: int
    ucp_endpoint: str
    country: str
    pricing_tiers: list[PricingTier] = field(default_factory=list)


_MOCK_VENDOR_DB: list[VendorEndpoint] = [
    VendorEndpoint(
        id="v-001",
        name="TechCorp Nordic",
        capability="dev.ucp.shopping",
        product="Laptop Pro 15",
        unit_price_usd=1299.00,
        available_units=50,
        ucp_endpoint="https://techcorp-nordic.example/.well-known/ucp",
        country="NO",
        pricing_tiers=[
            PricingTier(min_qty=1,  max_qty=9,    unit_price_usd=1299.00, discount_pct=0.0),
            PricingTier(min_qty=10, max_qty=49,   unit_price_usd=1199.00, discount_pct=7.7),
            PricingTier(min_qty=50, max_qty=None, unit_price_usd=999.00,  discount_pct=23.1),
        ],
    ),
    VendorEndpoint(
        id="v-002",
        name="EuroTech Supplies",
        capability="dev.ucp.shopping",
        product="Laptop Pro 15",
        unit_price_usd=1349.00,
        available_units=120,
        ucp_endpoint="https://eurotech.example/.well-known/ucp",
        country="DE",
        pricing_tiers=[
            PricingTier(min_qty=1,  max_qty=9,    unit_price_usd=1349.00, discount_pct=0.0),
            PricingTier(min_qty=10, max_qty=49,   unit_price_usd=1249.00, discount_pct=7.4),
            PricingTier(min_qty=50, max_qty=None, unit_price_usd=1049.00, discount_pct=22.3),
        ],
    ),
    VendorEndpoint(
        id="v-003",
        name="NordHardware AS",
        capability="dev.ucp.shopping",
        product="Laptop Pro 15",
        unit_price_usd=1280.00,
        available_units=30,
        ucp_endpoint="https://nordhardware.example/.well-known/ucp",
        country="NO",
        pricing_tiers=[
            PricingTier(min_qty=1,  max_qty=9,    unit_price_usd=1280.00, discount_pct=0.0),
            PricingTier(min_qty=10, max_qty=49,   unit_price_usd=1180.00, discount_pct=7.8),
            PricingTier(min_qty=50, max_qty=None, unit_price_usd=980.00,  discount_pct=23.4),
        ],
    ),
    VendorEndpoint(
        id="v-999",
        name="ShadowHardware",
        capability="dev.ucp.shopping",
        product="Laptop Pro 15",
        unit_price_usd=899.00,  # suspiciously cheap — no volume tiers (blacklisted test vendor)
        available_units=999,
        ucp_endpoint="https://shadowhardware.example/.well-known/ucp",
        country="XX",
        pricing_tiers=[
            PricingTier(min_qty=1, max_qty=None, unit_price_usd=899.00, discount_pct=0.0),
        ],
    ),
]


class UcpProvider(Protocol):
    def discover_vendors(self, query: str) -> list[dict[str, Any]]:
        ...


class MockUcpProvider:
    def discover_vendors(self, query: str) -> list[dict[str, Any]]:
        results = sorted(_MOCK_VENDOR_DB, key=lambda v: v.unit_price_usd)
        return [asdict(v) for v in results]


class HttpUcpProvider:
    def __init__(self, discovery_url: str, timeout_seconds: float = 10.0) -> None:
        self.discovery_url = discovery_url
        self.timeout_seconds = timeout_seconds

    def discover_vendors(self, query: str) -> list[dict[str, Any]]:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(self.discovery_url, params={"q": query})
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                "UCP provider request failed. Verify UCP_DISCOVERY_URL and network connectivity."
            ) from exc

        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict) and isinstance(payload.get("vendors"), list):
            return payload["vendors"]

        raise RuntimeError(
            "UCP provider returned unsupported response schema. Expected list or {'vendors': [...]}"
        )


def _get_ucp_provider() -> UcpProvider:
    mode = os.getenv("AURA_PROVIDER_MODE", "mock").strip().lower()
    if mode == "mock":
        return MockUcpProvider()

    if mode == "real":
        discovery_url = os.getenv("UCP_DISCOVERY_URL", "").strip()
        if not discovery_url:
            raise RuntimeError(
                "AURA_PROVIDER_MODE=real requires UCP_DISCOVERY_URL to be set."
            )
        return HttpUcpProvider(discovery_url=discovery_url)

    raise RuntimeError(
        f"Unsupported AURA_PROVIDER_MODE='{mode}'. Expected 'mock' or 'real'."
    )


def discover_vendors(query: str) -> list[dict[str, Any]]:
    """Discover vendors via Universal Commerce Protocol (UCP).

    Queries the UCP discovery network for vendors matching the given
    procurement query. Returns a list of VendorEndpoint objects as dicts,
    sorted by unit price ascending. Each vendor includes a ``pricing_tiers``
    list with volume discount information.

    Args:
        query: Natural language procurement query, e.g. "10 laptops".

    Returns:
        List of vendor endpoint dicts with id, name, price, availability,
        pricing_tiers, etc.
    """
    provider = _get_ucp_provider()
    return provider.discover_vendors(query)
