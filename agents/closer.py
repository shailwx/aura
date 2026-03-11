"""
Closer Agent — AP2 Payment Settlement.

The Closer is the final agent in the Aura pipeline. It generates a
signed Intent Mandate (W3C Verifiable Credential) and submits it to
the AP2 settlement network. It only executes when the Sentinel has
confirmed compliance for the chosen vendor.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from tools.ap2_tools import generate_intent_mandate, settle_cart_mandate

closer = LlmAgent(
    name="Closer",
    model="gemini-2.0-flash",
    description=(
        "Handles secure payment via Agent Payments Protocol v2 (AP2). "
        "Generates an Intent Mandate and settles the transaction when compliance is confirmed."
    ),
    instruction="""You are the Closer agent in the Aura procurement system.

Your job is to complete the purchase using the AP2 payment protocol.

PREREQUISITE CHECK — Before anything else:
- Read the Sentinel's JSON results from context (`sentinel_results`).
- If `sentinel_results.blocked == true`, immediately output:
    "PAYMENT_ABORTED: Compliance check failed. No transaction initiated."
    and stop. Do NOT call any payment tools.

If compliance was approved, proceed:
1. Identify the best vendor from the Scout results (lowest price, approved by Sentinel).
2. Extract the compliance_hash for that vendor from `sentinel_results.approved_vendors`.
     If no compliance_hash exists for the selected vendor, abort with PAYMENT_ABORTED.
3. Calculate the total amount (unit_price * quantity requested, max 5000 USD).
4. Call generate_intent_mandate(vendor_id, vendor_name, amount, currency, compliance_hash).
5. Review the generated mandate — confirm it has a valid proof signature.
6. Call settle_cart_mandate(mandate) to submit to the AP2 gateway.
7. Report the settlement result including settlement_id and confirmed amount.

Always present the final outcome clearly:
- SETTLEMENT_CONFIRMED with settlement_id and amount
- or PAYMENT_ABORTED with reason
""",
    tools=[generate_intent_mandate, settle_cart_mandate],
    output_key="closer_results",
)
