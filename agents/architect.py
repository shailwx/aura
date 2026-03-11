"""
Architect Agent — Root Orchestrator.

The Architect is the root LlmAgent that owns the full procurement
pipeline. It parses the user's natural language intent and delegates
to a SequentialAgent that chains Scout → Sentinel → Closer.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent, SequentialAgent

from agents.scout import scout
from agents.sentinel import sentinel
from agents.closer import closer

# The pipeline: Scout discovers → Sentinel vets → Closer settles
_pipeline = SequentialAgent(
    name="AuraPipeline",
    description="Sequential procurement pipeline: discovery → compliance → settlement.",
    sub_agents=[scout, sentinel, closer],
)

architect = LlmAgent(
    name="Architect",
    model="gemini-2.0-flash",
    description=(
        "Root orchestrator of the Aura autonomous procurement system. "
        "Parses enterprise procurement intent and coordinates the multi-agent pipeline."
    ),
    instruction="""You are Architect, the root orchestrator of Project Aura — 
Autonomous Reliable Agentic Commerce.

Aura automates B2B procurement with built-in compliance. Your pipeline:
  1. Scout   → discovers vendors via UCP protocol
  2. Sentinel → verifies KYC/AML compliance via Core Banking
  3. Closer  → settles payment via AP2 protocol

When the user submits a procurement request:
0. If an INTENT_JSON payload is present in the message context, treat it as the source of truth
    for product, quantity, budget, and currency.
1. Acknowledge the request and clarify any missing details (product, quantity, budget).
2. Hand off to the AuraPipeline sub-agent to execute Scout → Sentinel → Closer.
3. Summarise the final outcome for the user:
   - If successful: vendor chosen, compliance status, settlement ID, amount paid.
   - If blocked: which vendor failed compliance and why, what the user should do next.

You are the user's trusted agent. Always prioritise compliance — never allow a 
transaction to proceed if the Sentinel has flagged a compliance issue.

Respond in clear, professional language suitable for an enterprise procurement context.
""",
    sub_agents=[_pipeline],
)

# Expose root_agent for `adk web` dev UI auto-discovery
root_agent = architect
