"""Unit tests for structured procurement intent parsing."""

from __future__ import annotations

from tools.intent_tools import (
    build_clarification_message,
    build_structured_procurement_prompt,
    parse_procurement_intent,
)


class TestParseProcurementIntent:
    def test_parses_quantity_and_product(self):
        result = parse_procurement_intent("Buy 3 Laptop Pro 15 units")
        assert result.is_valid
        assert result.intent is not None
        assert result.intent.quantity == 3
        assert result.intent.product == "Laptop Pro 15 units"

    def test_parses_budget_and_currency(self):
        result = parse_procurement_intent("Buy 10 laptops under 4500 eur")
        assert result.is_valid
        assert result.intent is not None
        assert result.intent.budget == 4500.0
        assert result.intent.currency == "EUR"

    def test_missing_quantity_returns_clarification_fields(self):
        result = parse_procurement_intent("Buy laptops from best vendor")
        assert not result.is_valid
        assert "quantity" in result.missing_fields

    def test_missing_product_returns_clarification_fields(self):
        result = parse_procurement_intent("Buy 5")
        assert not result.is_valid
        assert "product" in result.missing_fields

    def test_defaults_currency_to_usd(self):
        result = parse_procurement_intent("Order 2 docking stations")
        assert result.is_valid
        assert result.intent is not None
        assert result.intent.currency == "USD"


class TestPromptBuilders:
    def test_clarification_message_contains_missing_fields(self):
        message = build_clarification_message(["quantity", "product"])
        assert "quantity" in message.lower()
        assert "product" in message.lower()

    def test_structured_prompt_contains_intent_json_marker(self):
        result = parse_procurement_intent("Buy 4 monitors under 2000 usd")
        assert result.is_valid
        prompt = build_structured_procurement_prompt(result.intent)
        assert "INTENT_JSON:" in prompt
        assert '"quantity": 4' in prompt
