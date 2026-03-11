"""
UCP Tools — Universal Commerce Protocol mock implementation.

In production this would hit real /.well-known/ucp endpoints.
For the hackathon prototype we return a curated vendor list that
includes a deliberately blacklisted vendor (ShadowHardware) to
exercise the Sentinel compliance path.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class VendorEndpoint:
    id: str
    name: str
    capability: str
    product: str
    unit_price_usd: float
    available_units: int
    ucp_endpoint: str
    country: str


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
    ),
    VendorEndpoint(
        id="v-999",
        name="ShadowHardware",
        capability="dev.ucp.shopping",
        product="Laptop Pro 15",
        unit_price_usd=899.00,  # suspiciously cheap
        available_units=999,
        ucp_endpoint="https://shadowhardware.example/.well-known/ucp",
        country="XX",
    ),
]


def discover_vendors(query: str) -> list[dict[str, Any]]:
    """Discover vendors via Universal Commerce Protocol (UCP).

    Queries the UCP discovery network for vendors matching the given
    procurement query. Returns a list of VendorEndpoint objects as dicts,
    sorted by unit price ascending.

    Args:
        query: Natural language procurement query, e.g. "10 laptops".

    Returns:
        List of vendor endpoint dicts with id, name, price, availability, etc.
    """
    # In production: HTTP GET each /.well-known/ucp endpoint and parse manifest
    results = sorted(_MOCK_VENDOR_DB, key=lambda v: v.unit_price_usd)
    return [asdict(v) for v in results]
