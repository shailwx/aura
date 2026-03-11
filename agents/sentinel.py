"""
Sentinel Agent — KYC/AML Compliance Vetting.

The Sentinel is the compliance gate in the Aura pipeline. It runs every
vendor discovered by the Scout through the Core Banking System (BMS)
compliance database. If ANY vendor returns REJECTED status, the Sentinel
blocks the pipeline and no payment is initiated.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from tools.compliance_tools import evaluate_vendors_compliance, verify_vendor_compliance

sentinel = LlmAgent(
    name="Sentinel",
    model="gemini-2.0-flash",
    description=(
        "Executes KYC/AML compliance checks on vendors via the Core Banking System. "
        "Blocks any vendor flagged in the AML blacklist and emits ComplianceHash for approved vendors."
    ),
    instruction="""You are the Sentinel agent in the Aura procurement system.

Your job is to run EVERY vendor from the Scout's results through the compliance database.

You MUST produce a strict JSON object as your final output with this exact schema:
{
    "blocked": <bool>,
    "approved_vendors": [{"vendor_name": "...", "compliance_hash": "..."}],
    "rejected_vendors": [{"vendor_name": "...", "reason": "...", "message": "..."}],
    "reason_codes": ["..."]
}

Steps:
1. Read the Scout vendor list from context.
2. Call evaluate_vendors_compliance(vendors) using the full vendor list.
3. Return the result unchanged as the final JSON response.

Fallback behavior: if structured vendor list cannot be parsed from context,
run verify_vendor_compliance(vendor_name) manually for each vendor you can identify,
then still output the final strict JSON schema above.

IMPORTANT: If ShadowHardware or any blacklisted vendor appears, you MUST block the entire
transaction by setting "blocked": true. The safety of the financial system depends on this.
""",
        tools=[evaluate_vendors_compliance, verify_vendor_compliance],
    output_key="sentinel_results",
)
