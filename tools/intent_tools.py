"""Intent tools for structured procurement request extraction.

This module provides deterministic parsing helpers so the runtime can validate
and normalize procurement requests before invoking the agent pipeline.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field


_QUANTITY_PATTERN = re.compile(r"\b(?:buy|purchase|order)?\s*(\d+)\s*(?:units?|pcs?|pieces?|x)?\b", re.IGNORECASE)
_BUDGET_PATTERN = re.compile(
    r"\b(?:under|below|max|budget(?:\s+of)?|up\s+to)\s*\$?\s*(\d+(?:\.\d+)?)\b",
    re.IGNORECASE,
)
_CURRENCY_PATTERN = re.compile(r"\b(usd|eur|nok|gbp)\b", re.IGNORECASE)


class ProcurementIntent(BaseModel):
    """Normalized procurement intent extracted from user text."""

    product: str = Field(min_length=2)
    quantity: int = Field(gt=0)
    budget: float | None = Field(default=None, gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    raw_message: str


class IntentParseResult(BaseModel):
    """Outcome wrapper for intent extraction."""

    intent: ProcurementIntent | None
    missing_fields: list[str]

    @property
    def is_valid(self) -> bool:
        return self.intent is not None and not self.missing_fields


def _extract_quantity(message: str) -> int | None:
    match = _QUANTITY_PATTERN.search(message)
    if not match:
        return None
    return int(match.group(1))


def _extract_product(message: str) -> str | None:
    text = message.strip()
    quantity_match = _QUANTITY_PATTERN.search(text)
    if quantity_match:
        trailing = text[quantity_match.end():].strip(" ,.")
        if trailing:
            split_tokens = re.split(r"\b(from|under|below|max|budget|for|at|with)\b", trailing, maxsplit=1, flags=re.IGNORECASE)
            candidate = split_tokens[0].strip(" ,.")
            if len(candidate) >= 2:
                return candidate

    fallback = re.search(r"\b(?:buy|purchase|order)\s+(.+?)\b(?:from|under|below|max|budget|for|at|with|$)", text, re.IGNORECASE)
    if fallback:
        candidate = fallback.group(1).strip(" ,.")
        if len(candidate) >= 2:
            return candidate

    return None


def _extract_budget(message: str) -> float | None:
    match = _BUDGET_PATTERN.search(message)
    if not match:
        return None
    return float(match.group(1))


def _extract_currency(message: str) -> str:
    match = _CURRENCY_PATTERN.search(message)
    if not match:
        return "USD"
    return match.group(1).upper()


def parse_procurement_intent(message: str) -> IntentParseResult:
    """Parse a natural language message into a structured procurement intent."""
    quantity = _extract_quantity(message)
    product = _extract_product(message)
    budget = _extract_budget(message)
    currency = _extract_currency(message)

    missing_fields: list[str] = []
    if quantity is None:
        missing_fields.append("quantity")
    if product is None:
        missing_fields.append("product")

    if missing_fields:
        return IntentParseResult(intent=None, missing_fields=missing_fields)

    intent = ProcurementIntent(
        product=product,
        quantity=quantity,
        budget=budget,
        currency=currency,
        raw_message=message,
    )
    return IntentParseResult(intent=intent, missing_fields=[])


def build_clarification_message(missing_fields: list[str]) -> str:
    """Return a deterministic clarification prompt for missing intent fields."""
    labels: dict[str, str] = {
        "product": "product name",
        "quantity": "quantity",
        "budget": "budget",
    }
    missing = [labels.get(field, field) for field in missing_fields]
    fields = ", ".join(missing)
    return (
        "I need a bit more detail before I can run procurement. "
        f"Please provide: {fields}. "
        "Example: 'Buy 3 Laptop Pro 15 units under 5000 USD'."
    )


def build_structured_procurement_prompt(intent: ProcurementIntent) -> str:
    """Embed normalized intent payload into the message passed to the agents."""
    payload: dict[str, Any] = {
        "product": intent.product,
        "quantity": intent.quantity,
        "budget": intent.budget,
        "currency": intent.currency,
        "raw_message": intent.raw_message,
    }
    return (
        "Use this normalized procurement intent for all calculations and vendor selection.\n"
        f"INTENT_JSON: {json.dumps(payload, sort_keys=True)}"
    )
