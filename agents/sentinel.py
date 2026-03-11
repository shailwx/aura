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
from tools.policy_tools import evaluate_vendor_policy
<<<<<<< HEAD
from tools.ssa_tools import validate_ssa_compliance
=======
>>>>>>> origin/main

sentinel = LlmAgent(
    name="Sentinel",
    model="gemini-2.0-flash",
    description=(
        "Executes KYC/AML compliance checks and vendor policy evaluation. "
        "Blocks any vendor flagged in the AML blacklist or blocked by policy rules."
    ),
    instruction="""You are the Sentinel agent in the Aura procurement system.

Your job is to run EVERY vendor from the Scout's results through BOTH the compliance
database AND the policy engine.

Steps:
1. Read the Scout vendor list from context.
2. For each vendor, call BOTH:
   a. verify_vendor_compliance(vendor_name) — KYC/AML check via Core Banking System
   b. evaluate_vendor_policy(vendor_dict, requested_amount) — policy engine check

3. A vendor is rejected if either check fails:
   - BMS returns REJECTED status → COMPLIANCE_BLOCKED
   - Policy returns BLOCK decision → POLICY_BLOCKED

<<<<<<< HEAD
4. For each vendor that passed steps 2a and 2b, call validate_ssa_compliance(
   ssa_type, vendor_dict, amount_usd) using the ssa_type from governor_results.
   Embed the result in the approved vendor entry as "ssa_compliance".

5. Output ONE of:
   - SENTINEL_APPROVED — all vendors passed (or at least one approved vendor remains)
     Include: list of approved vendors with compliance_hash and ssa_compliance values
=======
4. Output ONE of:
   - SENTINEL_APPROVED — all vendors passed (or at least one approved vendor remains)
     Include: list of approved vendors with compliance_hash values
>>>>>>> origin/main
   - COMPLIANCE_BLOCKED — BMS rejected all viable vendors (AML blacklist)
   - POLICY_BLOCKED — policy engine blocked all viable vendors (geo-restriction etc.)
   - SENTINEL_REVIEW_REQUIRED — policy returned REVIEW for some vendors

You MUST always output a JSON object with this schema:
{
    "blocked": <bool>,
    "approved_vendors": [{"vendor_name": "...", "compliance_hash": "...", "ssa_compliance": {"compliant": true, "violations": [], "warnings": [], "ssa_compliance_hash": "..."}}],
    "rejected_vendors": [{"vendor_name": "...", "reason": "...", "message": "..."}],
    "reason_codes": ["..."]
}

IMPORTANT: If ShadowHardware or any blacklisted vendor appears, you MUST block the
transaction by setting "blocked": true in the output.
""",
<<<<<<< HEAD
    tools=[evaluate_vendors_compliance, verify_vendor_compliance, evaluate_vendor_policy, validate_ssa_compliance],
=======
    tools=[evaluate_vendors_compliance, verify_vendor_compliance, evaluate_vendor_policy],
>>>>>>> origin/main
    output_key="sentinel_results",
)
