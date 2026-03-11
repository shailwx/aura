"""
UCP Tools — Universal Commerce Protocol mock implementation.

In production this would hit real /.well-known/ucp endpoints.
For the hackathon prototype we return a curated vendor list that
includes a deliberately blacklisted vendor (ShadowHardware) to
exercise the Sentinel compliance path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Any, Protocol

import httpx

from tools.reliability_tools import CircuitBreaker, CircuitOpenError, execute_with_retries


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
        self.retry_attempts = int(os.getenv("HTTP_RETRY_ATTEMPTS", "3"))
        self.retry_backoff_seconds = float(os.getenv("HTTP_RETRY_BACKOFF_SECONDS", "0.2"))
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "3")),
            reset_timeout_seconds=float(os.getenv("CIRCUIT_BREAKER_RESET_SECONDS", "30")),
        )

    def discover_vendors(self, query: str) -> list[dict[str, Any]]:
        def _request() -> Any:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(self.discovery_url, params={"q": query})
                response.raise_for_status()
                return response.json()

        try:
            payload = execute_with_retries(
                _request,
                attempts=self.retry_attempts,
                base_backoff_seconds=self.retry_backoff_seconds,
                circuit_breaker=self._circuit_breaker,
                retryable_exceptions=(httpx.HTTPError,),
            )
        except CircuitOpenError as exc:
            raise RuntimeError(
                "UCP provider circuit is open due to repeated failures. Try again later."
            ) from exc
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
    sorted by unit price ascending.

    Args:
        query: Natural language procurement query, e.g. "10 laptops".

    Returns:
        List of vendor endpoint dicts with id, name, price, availability, etc.
    """
    provider = _get_ucp_provider()
    return provider.discover_vendors(query)
