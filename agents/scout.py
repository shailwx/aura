"""
Scout Agent — UCP Vendor Discovery.

The Scout queries the Universal Commerce Protocol (UCP) discovery
network to find vendors matching the procurement request. It writes
the discovered vendor list into ADK session state for downstream agents.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from tools.ucp_tools import discover_vendors

scout = LlmAgent(
    name="Scout",
    model="gemini-2.0-flash",
    description=(
        "Discovers vendors via the Universal Commerce Protocol (UCP). "
        "Given a procurement query, finds all available vendors and their pricing."
    ),
    instruction="""You are the Scout agent in the Aura procurement system.

Your job is to discover vendors for the procurement request using the discover_vendors tool.

Steps:
1. Call discover_vendors(query) with the user's procurement query.
2. Review the returned vendor list.
3. Present the vendors as a clear table: ID, Name, Product, Unit Price, Available Units, Country.
4. Store the full vendor list in your response for the Architect to use.
5. Flag any vendor with country code "XX" or a suspiciously low price as potentially risky.

Always include ALL vendors in your response — the Sentinel will decide which ones pass compliance.
Do not skip or filter any vendors yourself.
""",
    tools=[discover_vendors],
    output_key="scout_results",
)
