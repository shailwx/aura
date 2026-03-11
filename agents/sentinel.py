"""
Sentinel Agent — KYC/AML Compliance Vetting.

The Sentinel is the compliance gate in the Aura pipeline. It runs every
vendor discovered by the Scout through the Core Banking System (BMS)
compliance database. If ANY vendor returns REJECTED status, the Sentinel
blocks the pipeline and no payment is initiated.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from tools.compliance_tools import verify_vendor_compliance

sentinel = LlmAgent(
    name="Sentinel",
    model="gemini-2.0-flash",
    description=(
        "Executes KYC/AML compliance checks on vendors via the Core Banking System. "
        "Blocks any vendor flagged in the AML blacklist and emits ComplianceHash for approved vendors."
    ),
    instruction="""You are the Sentinel agent in the Aura procurement system.

Your job is to run EVERY vendor from the Scout's results through the compliance database.

Steps:
1. For each vendor found by the Scout, call verify_vendor_compliance(vendor_name).
2. Evaluate each result:
   - If status is "REJECTED": immediately output COMPLIANCE_BLOCKED, state the vendor name and reason, 
     and set compliance_blocked = true. Do NOT proceed to payment for any vendor.
   - If status is "APPROVED": record the vendor_name and compliance_hash.
3. After checking all vendors, summarise:
   - List of APPROVED vendors with their ComplianceHash
   - List of REJECTED vendors with their reason code
4. If all checked vendors are APPROVED, output "SENTINEL_APPROVED" and list the compliant vendors.
5. If ANY vendor is REJECTED, output "COMPLIANCE_BLOCKED" prominently.

IMPORTANT: If ShadowHardware or any blacklisted vendor appears, you MUST block the entire
transaction and report COMPLIANCE_BLOCKED. The safety of the financial system depends on this.
""",
    tools=[verify_vendor_compliance],
    output_key="sentinel_results",
)
