"""
Payment Policy Tools — pre-settlement risk evaluation for the Closer agent.

Evaluates an IntentMandate-like dict against procurement spending policy rules
before the AP2 gateway call. Returns a decision (ALLOW / WARN / REVIEW / BLOCK)
so the Closer can gate or flag the payment accordingly.

Three callable tools:
  - evaluate_procurement_policy  → Governor: pre-flight procurement gate
  - evaluate_vendor_policy       → Sentinel: per-vendor policy check
  - evaluate_payment_policy      → Closer:   pre-settlement payment gate
"""

from __future__ import annotations

from typing import Any


# Spending thresholds (USD) — tunable via future config store.
_WARN_THRESHOLD_USD: float = 2000.00    # large purchase — proceed with note
_REVIEW_THRESHOLD_USD: float = 4000.00  # high-value — requires manager approval

# Sanctioned / restricted country codes (simplified OFAC list for demo)
_BLOCKED_COUNTRY_CODES: frozenset[str] = frozenset({"IR", "KP", "RU", "SY", "XX"})

# Product categories allowed in procurement
_ALLOWED_CATEGORIES: frozenset[str] = frozenset({
    "hardware", "electronics", "computer_components", "office_supplies",
    "saas", "cloud_infrastructure", "software_development", "consulting",
    "managed_services", "services", "professional_services", "staffing",
    "agile_development", "software_licenses", "maintenance", "hosting",
    "outsourcing", "government_cloud",
})


def evaluate_procurement_policy(request: dict[str, Any]) -> dict[str, Any]:
    """Evaluate pre-flight procurement policy for the Governor agent.

    Args:
        request: Dict with optional keys:
            - category (str): Product/service category.
            - amount_usd (float): Estimated transaction amount.
            - user_id (str): User or session identifier.

    Returns:
        Dict with decision (ALLOW|WARN|REVIEW|BLOCK), reason, and evaluated fields.
    """
    category = str(request.get("category", "")).strip().lower()
    amount_usd = float(request.get("amount_usd", 0) or 0)

    if category and category not in _ALLOWED_CATEGORIES:
        return {
            "decision": "BLOCK",
            "reason": (
                f"Category '{category}' is not in the approved procurement category list. "
                f"Contact your procurement officer to request an exception."
            ),
            "category": category,
            "amount_usd": amount_usd,
        }

    if amount_usd > 5000.00:
        return {
            "decision": "BLOCK",
            "reason": (
                f"Estimated amount ${amount_usd:,.2f} exceeds the per-transaction "
                "cap of $5,000. Split the order or request a limit increase."
            ),
            "category": category,
            "amount_usd": amount_usd,
        }

    if amount_usd >= _REVIEW_THRESHOLD_USD:
        return {
            "decision": "REVIEW",
            "reason": (
                f"High-value procurement of ${amount_usd:,.2f} requires manager "
                f"approval per policy (threshold: ${_REVIEW_THRESHOLD_USD:,.2f})."
            ),
            "category": category,
            "amount_usd": amount_usd,
        }

    if amount_usd >= _WARN_THRESHOLD_USD:
        return {
            "decision": "WARN",
            "reason": f"Large purchase estimated at ${amount_usd:,.2f}. Proceeding.",
            "category": category,
            "amount_usd": amount_usd,
        }

    return {
        "decision": "ALLOW",
        "reason": "Procurement request is within policy limits.",
        "category": category,
        "amount_usd": amount_usd,
    }


def evaluate_vendor_policy(vendor: dict[str, Any], requested_amount: float = 0.0) -> dict[str, Any]:
    """Evaluate vendor-specific policy rules for the Sentinel agent.

    Args:
        vendor: Dict with optional keys:
            - country (str): ISO 3166-1 alpha-2 country code.
            - name (str): Vendor trading name.
        requested_amount: Transaction amount in USD.

    Returns:
        Dict with decision (ALLOW|WARN|REVIEW|BLOCK) and reason.
    """
    country = str(vendor.get("country", "")).upper().strip()
    vendor_name = str(vendor.get("name", "unknown"))

    if country in _BLOCKED_COUNTRY_CODES:
        return {
            "decision": "BLOCK",
            "reason": (
                f"Vendor '{vendor_name}' is headquartered in a sanctioned or "
                f"restricted country ({country}). Transaction blocked per geo-restriction policy."
            ),
            "vendor": vendor_name,
            "country": country,
            "amount_usd": requested_amount,
        }

    if requested_amount > 5000.00:
        return {
            "decision": "BLOCK",
            "reason": (
                f"Amount ${requested_amount:,.2f} to vendor '{vendor_name}' "
                "exceeds the $5,000 per-transaction cap."
            ),
            "vendor": vendor_name,
            "country": country,
            "amount_usd": requested_amount,
        }

    if requested_amount >= _REVIEW_THRESHOLD_USD:
        return {
            "decision": "REVIEW",
            "reason": (
                f"High-value transaction of ${requested_amount:,.2f} to '{vendor_name}' "
                f"requires approval (threshold: ${_REVIEW_THRESHOLD_USD:,.2f})."
            ),
            "vendor": vendor_name,
            "country": country,
            "amount_usd": requested_amount,
        }

    return {
        "decision": "ALLOW",
        "reason": f"Vendor '{vendor_name}' ({country}) passed policy checks.",
        "vendor": vendor_name,
        "country": country,
        "amount_usd": requested_amount,
    }



def evaluate_payment_policy(
    mandate: dict[str, Any],
    user_id: str = "default",
) -> dict[str, Any]:
    """Evaluate an IntentMandate against procurement payment-policy rules.

    Checks the transaction amount against spending thresholds and returns a
    structured decision that the Closer agent uses to gate or annotate the
    settlement.

    Args:
        mandate: A dict containing at least::

            {
                "constraints": {"amount": <float>, "currency": "USD"},
                "vendor": {"name": <str>}
            }

        user_id: Identifier of the procuring user (reserved for future
            per-user policy look-ups).

    Returns:
        A dict with keys:

        - ``decision`` (str): One of ``"ALLOW"``, ``"WARN"``, ``"REVIEW"``,
          or ``"BLOCK"``.
        - ``reason`` (str): Human-readable explanation.
        - ``amount`` (float): The amount that was evaluated.
    """
    constraints = mandate.get("constraints", {})
    amount: float = float(constraints.get("amount", 0))
    vendor_name: str = mandate.get("vendor", {}).get("name", "unknown")

    if amount > 5000.00:
        return {
            "decision": "BLOCK",
            "reason": (
                f"Amount ${amount:,.2f} exceeds the AP2 IntentMandate cap of "
                "$5,000.00. Split the order or use a separate mandate."
            ),
            "amount": amount,
        }

    if amount >= _REVIEW_THRESHOLD_USD:
        return {
            "decision": "REVIEW",
            "reason": (
                f"High-value purchase of ${amount:,.2f} to {vendor_name} "
                f"requires manager approval per procurement policy "
                f"(threshold: ${_REVIEW_THRESHOLD_USD:,.2f})."
            ),
            "amount": amount,
        }

    if amount >= _WARN_THRESHOLD_USD:
        return {
            "decision": "WARN",
            "reason": (
                f"Large purchase of ${amount:,.2f} to {vendor_name}. "
                f"Proceeding as per procurement policy "
                f"(review threshold: ${_REVIEW_THRESHOLD_USD:,.2f})."
            ),
            "amount": amount,
        }

    return {
        "decision": "ALLOW",
        "reason": (
            f"Purchase of ${amount:,.2f} to {vendor_name} is within "
            "procurement policy limits."
        ),
        "amount": amount,
    }
