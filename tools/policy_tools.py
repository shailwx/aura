"""
<<<<<<< HEAD
Payment Policy Tools — pre-settlement risk evaluation for the Closer agent.

Evaluates an IntentMandate-like dict against procurement spending policy rules
before the AP2 gateway call. Returns a decision (ALLOW / WARN / REVIEW / BLOCK)
so the Closer can gate or flag the payment accordingly.

Three callable tools:
  - evaluate_procurement_policy  → Governor: pre-flight procurement gate
  - evaluate_vendor_policy       → Sentinel: per-vendor policy check
  - evaluate_payment_policy      → Closer:   pre-settlement payment gate
=======
Policy Tools — evaluate procurement, vendor, and payment policies.

Three callable tools consumed by Governor, Sentinel, and Closer agents:
  - evaluate_procurement_policy(request)  — Governor pre-flight gate
  - evaluate_vendor_policy(vendor, requested_amount)  — Sentinel gate
  - evaluate_payment_policy(mandate, user_id)  — Closer gate
>>>>>>> origin/main
"""

from __future__ import annotations

<<<<<<< HEAD
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
=======
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any

from tools.policy_store import PolicyStore, RuleType, Severity


# ── Decision types ──────────────────────────────────────────────────────────────


@dataclass
class PolicyViolation:
    rule_id: str
    rule_name: str
    severity: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyDecision:
    decision: str  # ALLOW | WARN | REVIEW | BLOCK
    violations: list[PolicyViolation] = field(default_factory=list)
    evaluated_rules: list[str] = field(default_factory=list)
    snapshot_hash: str = ""


_SEVERITY_RANK = {Severity.WARN: 1, Severity.REVIEW: 2, Severity.BLOCK: 3}


def _worst_decision(violations: list[PolicyViolation]) -> str:
    if not violations:
        return "ALLOW"
    worst = max(violations, key=lambda v: _SEVERITY_RANK.get(Severity(v.severity), 0))
    return worst.severity  # WARN | REVIEW | BLOCK


def _make_decision(violations: list[PolicyViolation], evaluated: list[str], snapshot_hash: str) -> dict[str, Any]:
    decision = _worst_decision(violations)
    return asdict(
        PolicyDecision(
            decision=decision,
            violations=[asdict(v) for v in violations],  # type: ignore[arg-type]
            evaluated_rules=evaluated,
            snapshot_hash=snapshot_hash,
        )
    )


# ── In-memory rate-limit state ──────────────────────────────────────────────────


class RateLimitStore:
    _instance: "RateLimitStore | None" = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._hourly: dict[str, deque[float]] = {}
        self._daily: dict[str, deque[float]] = {}
        self._rlock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "RateLimitStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def check_and_record(self, user_id: str, max_per_hour: int, max_per_day: int) -> tuple[bool, str]:
        """Return (allowed, reason). Records the request if allowed."""
        now = time.time()
        with self._rlock:
            hourly = self._hourly.setdefault(user_id, deque())
            daily = self._daily.setdefault(user_id, deque())
            # Evict old timestamps
            while hourly and now - hourly[0] > 3600:
                hourly.popleft()
            while daily and now - daily[0] > 86400:
                daily.popleft()

            if len(hourly) >= max_per_hour:
                return False, f"Rate limit exceeded: {len(hourly)} requests in last hour (max {max_per_hour})"
            if len(daily) >= max_per_day:
                return False, f"Rate limit exceeded: {len(daily)} requests today (max {max_per_day})"

            hourly.append(now)
            daily.append(now)
            return True, ""


# ── Daily spend tracking ────────────────────────────────────────────────────────


class DailySpendStore:
    _instance: "DailySpendStore | None" = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._spends: dict[str, list[tuple[float, float]]] = {}
        self._rlock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "DailySpendStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_daily_total(self, user_id: str) -> float:
        now = time.time()
        entries = self._spends.get(user_id, [])
        return sum(amt for ts, amt in entries if now - ts <= 86400)

    def record_spend(self, user_id: str, amount: float) -> None:
        with self._rlock:
            self._spends.setdefault(user_id, []).append((time.time(), amount))


# ── Tool: evaluate_procurement_policy ──────────────────────────────────────────


def evaluate_procurement_policy(request: dict[str, Any]) -> dict[str, Any]:
    """Evaluate pre-flight procurement policy rules for a purchase request.

    Called by the Governor agent before Scout discovers vendors.

    Args:
        request: Dict with optional keys:
            - category (str): Product category
            - amount_usd (float): Transaction amount
            - user_id (str): User or session identifier

    Returns:
        PolicyDecision dict with decision, violations, evaluated_rules, snapshot_hash.
    """
    store = PolicyStore.get_instance()
    snapshot_hash = store.get_snapshot_hash()
    violations: list[PolicyViolation] = []
    evaluated: list[str] = []

    category = request.get("category", "")
    amount_usd = float(request.get("amount_usd", 0))
    user_id = str(request.get("user_id", "unknown"))

    for rule in store.get_all_rules():
        if not rule.enabled:
            continue

        if rule.rule_type == RuleType.CATEGORY_ALLOWLIST and category:
            evaluated.append(rule.id)
            allowed = rule.parameters.get("allowed_categories", [])
            if category not in allowed:
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity.value,
                    reason=f"Category '{category}' is not in the allow-list: {allowed}",
                    details={"category": category, "allowed": allowed},
                ))

        elif rule.rule_type == RuleType.SPENDING_LIMIT and amount_usd > 0:
            evaluated.append(rule.id)
            max_tx = rule.parameters.get("max_transaction_usd", float("inf"))
            if amount_usd > max_tx:
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity.value,
                    reason=f"Transaction ${amount_usd:,.2f} exceeds limit ${max_tx:,.2f}",
                    details={"amount_usd": amount_usd, "max_transaction_usd": max_tx},
                ))

        elif rule.rule_type == RuleType.RATE_LIMIT:
            evaluated.append(rule.id)
            max_hour = rule.parameters.get("max_requests_per_hour", 999)
            max_day = rule.parameters.get("max_requests_per_day", 9999)
            allowed_rl, reason = RateLimitStore.get_instance().check_and_record(user_id, max_hour, max_day)
            if not allowed_rl:
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity.value,
                    reason=reason,
                    details={"user_id": user_id},
                ))

    return _make_decision(violations, evaluated, snapshot_hash)


# ── Tool: evaluate_vendor_policy ───────────────────────────────────────────────


def evaluate_vendor_policy(vendor: dict[str, Any], requested_amount: float = 0.0) -> dict[str, Any]:
    """Evaluate vendor-specific policy rules (geo-restriction, certifications, thresholds).

    Called by the Sentinel agent for each candidate vendor.

    Args:
        vendor: Dict with optional keys:
            - country (str): ISO 3166-1 alpha-2 country code
            - capability (str): Product capability / category
            - certifications (list[str]): Certifications the vendor holds
        requested_amount: Transaction amount in USD.

    Returns:
        PolicyDecision dict.
    """
    store = PolicyStore.get_instance()
    snapshot_hash = store.get_snapshot_hash()
    violations: list[PolicyViolation] = []
    evaluated: list[str] = []

    country = vendor.get("country", "").upper()
    capability = vendor.get("capability", "")
    certifications = set(vendor.get("certifications", []))

    for rule in store.get_all_rules():
        if not rule.enabled:
            continue

        if rule.rule_type == RuleType.GEO_RESTRICTION and country:
            evaluated.append(rule.id)
            blocked = rule.parameters.get("blocked_country_codes", [])
            if country in blocked:
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity.value,
                    reason=f"Vendor country {country} is blocked (sanctioned/restricted).",
                    details={"country": country, "blocked_codes": blocked},
                ))

        elif rule.rule_type == RuleType.CERTIFICATION_REQUIRED and capability:
            evaluated.append(rule.id)
            requirements: dict[str, list[str]] = rule.parameters.get("requirements", {})
            required = requirements.get(capability, [])
            missing = [c for c in required if c not in certifications]
            if missing:
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity.value,
                    reason=f"Vendor missing required certifications for '{capability}': {missing}",
                    details={"capability": capability, "missing": missing},
                ))

        elif rule.rule_type == RuleType.APPROVAL_THRESHOLD and requested_amount > 0:
            evaluated.append(rule.id)
            block_above = rule.parameters.get("block_above_usd", float("inf"))
            review_above = rule.parameters.get("review_above_usd", float("inf"))
            if requested_amount > block_above:
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=Severity.BLOCK.value,
                    reason=f"Amount ${requested_amount:,.2f} exceeds block threshold ${block_above:,.2f}",
                    details={"amount": requested_amount, "block_above_usd": block_above},
                ))
            elif requested_amount > review_above:
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity.value,
                    reason=f"Amount ${requested_amount:,.2f} requires review (above ${review_above:,.2f})",
                    details={"amount": requested_amount, "review_above_usd": review_above},
                ))

    return _make_decision(violations, evaluated, snapshot_hash)


# ── Tool: evaluate_payment_policy ──────────────────────────────────────────────


def evaluate_payment_policy(mandate: dict[str, Any], user_id: str = "unknown") -> dict[str, Any]:
    """Evaluate payment-stage policy rules before AP2 settlement.

    Called by the Closer agent after mandate generation, before settlement.

    Args:
        mandate: Dict with optional keys:
            - amount_usd (float): Payment amount (top-level shorthand)
            - constraints.amount (float): Amount from IntentMandate structure
        user_id: User or session identifier for daily spend tracking.

    Returns:
        PolicyDecision dict.
    """
    store = PolicyStore.get_instance()
    snapshot_hash = store.get_snapshot_hash()
    violations: list[PolicyViolation] = []
    evaluated: list[str] = []

    # Accept both flat {amount_usd: X} and nested IntentMandate {constraints: {amount: X}}
    amount_usd = float(
        mandate.get("amount_usd")
        or mandate.get("constraints", {}).get("amount", 0)
        or 0
    )

    for rule in store.get_all_rules():
        if not rule.enabled:
            continue

        if rule.rule_type == RuleType.APPROVAL_THRESHOLD and amount_usd > 0:
            evaluated.append(rule.id)
            block_above = rule.parameters.get("block_above_usd", float("inf"))
            review_above = rule.parameters.get("review_above_usd", float("inf"))
            auto_approve = rule.parameters.get("auto_approve_below_usd", 0)
            if amount_usd > block_above:
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=Severity.BLOCK.value,
                    reason=f"Payment ${amount_usd:,.2f} exceeds block ceiling ${block_above:,.2f}",
                    details={"amount": amount_usd, "block_above_usd": block_above},
                ))
            elif amount_usd > review_above and amount_usd > auto_approve:
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity.value,
                    reason=f"Payment ${amount_usd:,.2f} requires review (above ${review_above:,.2f})",
                    details={"amount": amount_usd, "review_above_usd": review_above},
                ))

        elif rule.rule_type == RuleType.SPENDING_LIMIT and amount_usd > 0:
            evaluated.append(rule.id)
            max_daily = rule.parameters.get("max_daily_usd", float("inf"))
            daily_store = DailySpendStore.get_instance()
            daily_total = daily_store.get_daily_total(user_id)
            if daily_total + amount_usd > max_daily:
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity.value,
                    reason=(
                        f"Daily spend limit exceeded: existing ${daily_total:,.2f} + "
                        f"new ${amount_usd:,.2f} > limit ${max_daily:,.2f}"
                    ),
                    details={"daily_total": daily_total, "amount_usd": amount_usd, "max_daily_usd": max_daily},
                ))
            else:
                daily_store.record_spend(user_id, amount_usd)

    return _make_decision(violations, evaluated, snapshot_hash)
>>>>>>> origin/main
