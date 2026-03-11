# Aura — Testing Guide

## Overview

Aura's test suite covers the **tool layer** (UCP discovery, Sentinel compliance, AP2 settlement) with unit and integration tests. The tests are deliberately scoped to pure Python tools — not to the LLM agents — so they run fast and deterministically with no GCP credentials required.

---

## Test Structure

```
tests/
├── __init__.py
├── test_compliance_tool.py   # Unit tests for the Sentinel's KYC/AML logic
└── test_flow.py              # Integration tests for UCP + AP2 tool pipeline
```

---

## Running the Tests

### Prerequisites

```bash
# Activate virtualenv
source .venv/bin/activate

# Install dependencies (includes pytest and pytest-asyncio)
pip install -r requirements.txt
```

### Run all tests

```bash
pytest tests/ -v
```

### Run a specific file

```bash
pytest tests/test_compliance_tool.py -v
pytest tests/test_flow.py -v
```

### Run a specific test

```bash
pytest tests/test_compliance_tool.py::TestVerifyVendorCompliance::test_shadow_hardware_is_rejected -v
```

---

## Test Coverage

### `test_compliance_tool.py` — Sentinel Unit Tests

Tests `tools/compliance_tools.verify_vendor_compliance()` — the compliance gate that every vendor must pass before payment.

| Test | What it verifies |
| :--- | :--- |
| `test_shadow_hardware_is_rejected` | ShadowHardware returns `REJECTED` with reason `AML_BLACKLIST` |
| `test_shadow_hardware_case_insensitive` | Blacklist matching is case-insensitive (`shadowhardware`, `SHADOWHARDWARE`, etc.) |
| `test_legitimate_vendor_is_approved` | TechCorp Nordic returns `APPROVED` with a compliance hash |
| `test_compliance_hash_is_64_chars` | ComplianceHash is exactly 64 lowercase hex characters (SHA-256) |
| `test_compliance_hash_deterministic_within_hour` | Same vendor called twice returns the same hash within the same hour |
| `test_different_vendors_get_different_hashes` | Different vendors produce distinct compliance hashes |
| `test_vendor_name_preserved_in_result` | The returned `vendor_name` matches the input string |
| `test_message_present_on_approved` | Approved result contains a human-readable `message` field |
| `test_message_present_on_rejected` | Rejected result contains a `message` referencing AML/blacklist |

**Critical invariant:** A vendor with `status: REJECTED` must **never** have a `compliance_hash` in the result — the Closer's prerequisite check depends on this.

---

### `test_flow.py` — Integration Tests

Tests the three tool layers end-to-end without invoking LLM agents.

#### `TestDiscoverVendors` — UCP Scout tools

| Test | What it verifies |
| :--- | :--- |
| `test_returns_list` | `discover_vendors()` returns a non-empty list |
| `test_shadow_hardware_present_in_results` | ShadowHardware is included (the Scout never filters — that's the Sentinel's job) |
| `test_vendors_sorted_by_price` | Results are sorted ascending by `unit_price_usd` |
| `test_vendor_has_required_fields` | Every vendor dict has `id`, `name`, `product`, `unit_price_usd`, `available_units`, `country` |

#### `TestGenerateIntentMandate` — AP2 tools

| Test | What it verifies |
| :--- | :--- |
| `test_mandate_has_correct_type` | Returns `{"type": "IntentMandate", ...}` |
| `test_mandate_has_id` | Mandate contains a non-empty `id` (UUID) |
| `test_mandate_amount_in_constraints` | Amount is stored under `constraints.amount` with `max_amount = 5000.00` |
| `test_mandate_embeds_compliance_hash` | The `compliance_hash` from the Sentinel is embedded in `constraints` |
| `test_mandate_has_ecdsa_proof` | Proof block exists with `type: "ecdsa-p256-signature"` and a non-empty value |
| `test_mandate_exceeds_max_amount_raises` | Amounts > 5000 USD raise `ValueError` |
| `test_mandate_vendor_info_correct` | Vendor `id` and `name` are preserved in the mandate |

#### `TestSettleCartMandate` — AP2 settlement

| Test | What it verifies |
| :--- | :--- |
| `test_settlement_returns_settled_status` | A valid mandate settles with `status: "SETTLED"` |
| `test_settlement_has_settlement_id` | Settlement result contains a `settlement_id` starting with `"AP2-"` |
| `test_settlement_amount_matches_mandate` | The settled amount equals the mandate's `constraints.amount` |

---

## Key Design Decisions

**Why no LLM agent tests?**  
Agent behaviour depends on the LLM's non-deterministic output. Tool tests are fast, stable, and run without credentials. The agent *instructions* and *pipeline wiring* are validated manually via `adk web` or integration through the `/run` endpoint.

**Why is ShadowHardware in the Scout results?**  
The Scout must present *all* available vendors — filtering is the Sentinel's exclusive responsibility. `test_shadow_hardware_present_in_results` enforces this design boundary.

**Why is the compliance hash deterministic within the hour?**  
The hash is keyed to `COMPLIANCE:{vendor_name}:{hour}`. This lets tests assert hash consistency without mocking `time.time()`, while still rotating hourly in production simulations.

---

## Adding New Tests

To add tests for a new tool:

```
tests/
└── test_<tool_name>.py
```

Import the tool directly and test its return contract:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools.my_tool import my_function

class TestMyTool:
    def test_basic_case(self):
        result = my_function("input")
        assert result["status"] == "expected"
```
