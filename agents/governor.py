"""
Governor Agent — pre-flight policy gate for the Aura procurement pipeline.

The Governor runs FIRST in the SequentialAgent pipeline (before Scout).
It evaluates the procurement request against the Policy Engine rules and
writes its decision to session_state["governor_results"].
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from tools.policy_tools import evaluate_procurement_policy

governor = LlmAgent(
    name="Governor",
    model="gemini-3.1-flash",
    description=(
        "Pre-flight policy gate. Evaluates every procurement request against "
        "the organisation's procurement rules before any vendor discovery begins."
    ),
    instruction="""You are the Governor agent in the Aura procurement system.

Your job is to evaluate procurement requests against the organisation's policy rules
BEFORE any vendor is contacted.

Steps:
1. Extract the following fields from the user's request:
   - category: the product/service category (e.g. "hardware", "saas")
   - amount_usd: the estimated total spend in US dollars
   - user_id: the requesting user or session identifier (default "unknown" if not provided)

2. Call evaluate_procurement_policy with:
   {"category": <category>, "amount_usd": <amount_usd>, "user_id": <user_id>}

3. Interpret the result and output ONE of:
   - POLICY_CLEAR — decision is ALLOW, no violations
   - POLICY_WARNINGS — decision is WARN, list each warning
   - POLICY_REVIEW_REQUIRED — decision is REVIEW, list reasons and add to review queue
   - POLICY_BLOCKED — decision is BLOCK, state each violation and STOP

4. Always include the snapshot_hash from the decision in your output so downstream
   agents can verify the rule set did not change between stages.

Examples:
  POLICY_CLEAR (snapshot: a1b2c3d4e5f6g7h8) — all rules passed
  POLICY_BLOCKED: Category 'weapons' not allowed. Transaction $12,000 exceeds limit. (snapshot: a1b2c3d4e5f6g7h8)
""",
    tools=[evaluate_procurement_policy],
    output_key="governor_results",
)
