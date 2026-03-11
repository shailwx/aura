"""
Policy Store — persistent, thread-safe rule registry for the Aura Policy Engine.

All rules are stored in tmp/policies.json via atomic writes.
The module exposes two singletons:
  - PolicyStore  — CRUD over PolicyRule objects
  - ReviewStore  — queue for transactions that require human review
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

_POLICY_FILE = Path(__file__).parent.parent / "tmp" / "policies.json"


class RuleType(str, Enum):
    SPENDING_LIMIT = "SPENDING_LIMIT"
    GEO_RESTRICTION = "GEO_RESTRICTION"
    CATEGORY_ALLOWLIST = "CATEGORY_ALLOWLIST"
    APPROVAL_THRESHOLD = "APPROVAL_THRESHOLD"
    CERTIFICATION_REQUIRED = "CERTIFICATION_REQUIRED"
    RATE_LIMIT = "RATE_LIMIT"


class Severity(str, Enum):
    WARN = "WARN"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


@dataclass
class PolicyRule:
    id: str
    name: str
    rule_type: RuleType
    enabled: bool
    severity: Severity
    parameters: dict[str, Any]
    description: str
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["rule_type"] = self.rule_type.value
        d["severity"] = self.severity.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyRule":
        return cls(
            id=data["id"],
            name=data["name"],
            rule_type=RuleType(data["rule_type"]),
            enabled=data["enabled"],
            severity=Severity(data["severity"]),
            parameters=data["parameters"],
            description=data.get("description", ""),
            created_at=data.get("created_at", time.time()),
        )


def _default_rules() -> list[PolicyRule]:
    now = time.time()
    return [
        PolicyRule(
            id="rule-spending-limit",
            name="Transaction Spending Limit",
            rule_type=RuleType.SPENDING_LIMIT,
            enabled=True,
            severity=Severity.BLOCK,
            parameters={"max_transaction_usd": 5000, "max_daily_usd": 20000},
            description="Block single transactions above $5,000 and daily spend above $20,000.",
            created_at=now,
        ),
        PolicyRule(
            id="rule-geo-restriction",
            name="Geographic Restriction",
            rule_type=RuleType.GEO_RESTRICTION,
            enabled=True,
            severity=Severity.BLOCK,
            parameters={"blocked_country_codes": ["IR", "KP", "RU", "SY"]},
            description="Block vendors headquartered in sanctioned countries.",
            created_at=now,
        ),
        PolicyRule(
            id="rule-category-allowlist",
            name="Category Allowlist",
            rule_type=RuleType.CATEGORY_ALLOWLIST,
            enabled=True,
            severity=Severity.BLOCK,
            parameters={
                "allowed_categories": [
                    "hardware",
                    "electronics",
                    "computer_components",
                    "office_supplies",
                    "saas",
                    "cloud_infrastructure",
                ]
            },
            description="Only allow procurement in approved product categories.",
            created_at=now,
        ),
        PolicyRule(
            id="rule-approval-threshold",
            name="Approval Threshold",
            rule_type=RuleType.APPROVAL_THRESHOLD,
            enabled=True,
            severity=Severity.REVIEW,
            parameters={
                "auto_approve_below_usd": 1000,
                "review_above_usd": 1000,
                "block_above_usd": 5000,
            },
            description="Auto-approve under $1k; route to review queue $1k–$5k; block above $5k.",
            created_at=now,
        ),
        PolicyRule(
            id="rule-certification-required",
            name="Vendor Certification Requirements",
            rule_type=RuleType.CERTIFICATION_REQUIRED,
            enabled=True,
            severity=Severity.WARN,
            parameters={
                "requirements": {
                    "hardware": ["ISO9001"],
                    "electronics": ["RoHS", "CE"],
                }
            },
            description="Warn when a vendor lacks required certifications for the product category.",
            created_at=now,
        ),
        PolicyRule(
            id="rule-rate-limit",
            name="Request Rate Limit",
            rule_type=RuleType.RATE_LIMIT,
            enabled=True,
            severity=Severity.BLOCK,
            parameters={"max_requests_per_hour": 5, "max_requests_per_day": 20},
            description="Block users who exceed the hourly or daily request rate.",
            created_at=now,
        ),
    ]


class PolicyStore:
    _instance: "PolicyStore | None" = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._rules: dict[str, PolicyRule] = {}
        self._rlock = threading.Lock()
        self._load()

    @classmethod
    def get_instance(cls) -> "PolicyStore":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── persistence ────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not _POLICY_FILE.exists():
            for rule in _default_rules():
                self._rules[rule.id] = rule
            self._flush()
            return
        try:
            data = json.loads(_POLICY_FILE.read_text())
            for item in data:
                rule = PolicyRule.from_dict(item)
                self._rules[rule.id] = rule
        except Exception:
            for rule in _default_rules():
                self._rules[rule.id] = rule

    def _flush(self) -> None:
        _POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _POLICY_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps([r.to_dict() for r in self._rules.values()], indent=2))
        os.replace(tmp, _POLICY_FILE)

    # ── CRUD ───────────────────────────────────────────────────────────────

    def add_rule(self, rule: PolicyRule) -> PolicyRule:
        with self._rlock:
            self._rules[rule.id] = rule
            self._flush()
            return rule

    def get_rule(self, rule_id: str) -> PolicyRule | None:
        return self._rules.get(rule_id)

    def get_all_rules(self) -> list[PolicyRule]:
        return list(self._rules.values())

    def update_rule(self, rule_id: str, updates: dict[str, Any]) -> PolicyRule | None:
        with self._rlock:
            rule = self._rules.get(rule_id)
            if rule is None:
                return None
            for key, val in updates.items():
                if key == "rule_type":
                    rule.rule_type = RuleType(val)
                elif key == "severity":
                    rule.severity = Severity(val)
                elif hasattr(rule, key):
                    setattr(rule, key, val)
            self._flush()
            return rule

    def delete_rule(self, rule_id: str) -> bool:
        with self._rlock:
            if rule_id not in self._rules:
                return False
            del self._rules[rule_id]
            self._flush()
            return True

    def get_snapshot_hash(self) -> str:
        raw = json.dumps(
            [r.to_dict() for r in sorted(self._rules.values(), key=lambda x: x.id)],
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Review Store ────────────────────────────────────────────────────────────────


@dataclass
class ReviewItem:
    id: str
    session_id: str
    user_id: str
    decision_context: dict[str, Any]
    created_at: float = field(default_factory=time.time)
    status: str = "pending"
    resolved_at: float | None = None
    resolution_note: str = ""


class ReviewStore:
    _instance: "ReviewStore | None" = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._items: dict[str, ReviewItem] = {}
        self._rlock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ReviewStore":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def add_item(self, item: ReviewItem) -> ReviewItem:
        with self._rlock:
            self._items[item.id] = item
            return item

    def get_pending(self) -> list[ReviewItem]:
        return [i for i in self._items.values() if i.status == "pending"]

    def resolve(self, review_id: str, approved: bool, note: str = "") -> ReviewItem | None:
        with self._rlock:
            item = self._items.get(review_id)
            if item is None:
                return None
            item.status = "approved" if approved else "rejected"
            item.resolved_at = time.time()
            item.resolution_note = note
            return item
