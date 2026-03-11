"""
Aura — Procurement Dashboard
Google AI Agent Labs Oslo 2026 · Team 6

Run with:
    streamlit run ui/dashboard.py
"""

from __future__ import annotations

import sys
import os
import time
import json
from dataclasses import dataclass, field
from typing import Any

import streamlit as st
import httpx

# ── Path setup so tools/ is importable ────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools.ucp_tools import discover_vendors
from tools.compliance_tools import verify_vendor_compliance
from tools.ap2_tools import generate_intent_mandate, settle_cart_mandate

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Aura · Autonomous Commerce",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0d1117; color: #e6edf3; }

    /* Agent status card */
    .agent-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    .agent-card.running {
        border-color: #f0b429;
        background: #1c1a0f;
        box-shadow: 0 0 12px rgba(240, 180, 41, 0.3);
    }
    .agent-card.done {
        border-color: #238636;
        background: #0c1a0f;
        box-shadow: 0 0 12px rgba(35, 134, 54, 0.2);
    }
    .agent-card.blocked {
        border-color: #da3633;
        background: #1f0d0d;
        box-shadow: 0 0 12px rgba(218, 54, 51, 0.3);
    }
    .agent-name { font-size: 1.05rem; font-weight: 600; }
    .agent-status { font-size: 0.85rem; color: #8b949e; margin-top: 4px; }
    .agent-status.running { color: #f0b429; }
    .agent-status.done { color: #3fb950; }
    .agent-status.blocked { color: #f85149; }

    /* Result cards */
    .result-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-top: 10px;
    }
    .settled-card {
        background: #0c1a0f;
        border: 2px solid #238636;
        border-radius: 10px;
        padding: 24px;
        margin-top: 16px;
        text-align: center;
    }
    .blocked-card {
        background: #1f0d0d;
        border: 2px solid #da3633;
        border-radius: 10px;
        padding: 24px;
        margin-top: 16px;
        text-align: center;
    }
    .badge-approved {
        background: #238636; color: white;
        padding: 3px 10px; border-radius: 20px; font-size: 0.8rem;
    }
    .badge-rejected {
        background: #da3633; color: white;
        padding: 3px 10px; border-radius: 20px; font-size: 0.8rem;
    }
    .metric-big { font-size: 2rem; font-weight: 700; color: #3fb950; }
    .metric-label { font-size: 0.85rem; color: #8b949e; }
    .divider { border-top: 1px solid #30363d; margin: 16px 0; }

    /* Header */
    h1 { color: #e6edf3 !important; }
    .subtitle { color: #8b949e; font-size: 1rem; margin-top: -16px; }
    .stButton > button {
        background: linear-gradient(135deg, #1f6feb, #388bfd);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 24px;
        width: 100%;
    }
    .stButton > button:hover { background: linear-gradient(135deg, #388bfd, #58a6ff); }
    [data-testid="stTextInput"] input {
        background: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
    }
</style>
""", unsafe_allow_html=True)


# ── State helpers ─────────────────────────────────────────────────────────────
AGENTS = ["Architect", "Scout", "Sentinel", "Closer"]
AGENT_ICONS = {"Architect": "🏛️", "Scout": "🔭", "Sentinel": "🛡️", "Closer": "💳"}
AGENT_DESC = {
    "Architect": "Root orchestrator — parsing intent",
    "Scout": "UCP vendor discovery",
    "Sentinel": "KYC/AML compliance gate",
    "Closer": "AP2 payment settlement",
}

def init_state():
    defaults = {
        "running": False,
        "agent_status": {a: "idle" for a in AGENTS},      # idle|running|done|blocked
        "agent_detail": {a: "" for a in AGENTS},
        "vendors": [],
        "compliance": [],
        "settlement": None,
        "blocked_vendor": None,
        "error": None,
        "mode": "demo",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Demo simulation ───────────────────────────────────────────────────────────
def run_demo(query: str):
    """Run the full pipeline using real tool functions with simulated timing."""
    ss = st.session_state
    ss["agent_status"] = {a: "idle" for a in AGENTS}
    ss["agent_detail"] = {a: "" for a in AGENTS}
    ss["vendors"] = []
    ss["compliance"] = []
    ss["settlement"] = None
    ss["blocked_vendor"] = None
    ss["error"] = None

    # ── Architect ──────────────────────────────────────────────────────────
    ss["agent_status"]["Architect"] = "running"
    ss["agent_detail"]["Architect"] = f'Parsing: "{query}"'
    yield
    time.sleep(1.2)
    ss["agent_status"]["Architect"] = "done"
    ss["agent_detail"]["Architect"] = "Intent parsed → delegating to pipeline"
    yield

    # ── Scout ──────────────────────────────────────────────────────────────
    ss["agent_status"]["Scout"] = "running"
    ss["agent_detail"]["Scout"] = "Querying UCP discovery network…"
    yield
    time.sleep(1.5)
    vendors = discover_vendors(query)
    ss["vendors"] = vendors
    ss["agent_status"]["Scout"] = "done"
    ss["agent_detail"]["Scout"] = f"Discovered {len(vendors)} vendors"
    yield

    # ── Sentinel ───────────────────────────────────────────────────────────
    ss["agent_status"]["Sentinel"] = "running"
    ss["agent_detail"]["Sentinel"] = "Running KYC/AML checks…"
    yield

    compliance_results = []
    blocked = False
    for v in vendors:
        time.sleep(0.6)
        result = verify_vendor_compliance(v["name"])
        compliance_results.append({**v, **result})
        if result["status"] == "REJECTED":
            blocked = True
            ss["blocked_vendor"] = v["name"]
        ss["compliance"] = compliance_results
        yield

    if blocked:
        ss["agent_status"]["Sentinel"] = "blocked"
        ss["agent_detail"]["Sentinel"] = f"COMPLIANCE_BLOCKED — {ss['blocked_vendor']} on AML blacklist"
        ss["agent_status"]["Closer"] = "blocked"
        ss["agent_detail"]["Closer"] = "PAYMENT_ABORTED — compliance failed"
        ss["agent_status"]["Architect"] = "blocked"
        ss["agent_detail"]["Architect"] = "Transaction blocked — no payment initiated"
        yield
        return

    ss["agent_status"]["Sentinel"] = "done"
    approved = [c for c in compliance_results if c["status"] == "APPROVED"]
    ss["agent_detail"]["Sentinel"] = f"SENTINEL_APPROVED — {len(approved)} vendors cleared"
    yield

    # ── Closer ─────────────────────────────────────────────────────────────
    ss["agent_status"]["Closer"] = "running"
    ss["agent_detail"]["Closer"] = "Generating Intent Mandate…"
    yield
    time.sleep(1.0)

    # Pick cheapest approved vendor
    best = min(
        (c for c in compliance_results if c["status"] == "APPROVED"),
        key=lambda x: x["unit_price_usd"],
    )

    qty = 3  # default quantity for demo
    amount = round(best["unit_price_usd"] * qty, 2)
    amount = min(amount, 5000.0)

    mandate = generate_intent_mandate(
        vendor_id=best["id"],
        vendor_name=best["name"],
        amount=amount,
        compliance_hash=best["compliance_hash"],
    )

    ss["agent_detail"]["Closer"] = "Submitting to AP2 gateway…"
    yield
    time.sleep(0.8)

    result = settle_cart_mandate(mandate)
    ss["settlement"] = result
    ss["agent_status"]["Closer"] = "done"
    ss["agent_detail"]["Closer"] = f"SETTLEMENT_CONFIRMED — {result['settlement_id']}"
    ss["agent_status"]["Architect"] = "done"
    ss["agent_detail"]["Architect"] = "Procurement complete ✓"
    yield


# ── Live mode (calls FastAPI) ─────────────────────────────────────────────────
def run_live(query: str, api_url: str):
    ss = st.session_state
    ss["agent_status"] = {a: "running" for a in AGENTS}
    ss["agent_detail"] = {a: "Processing…" for a in AGENTS}
    yield
    try:
        resp = httpx.post(f"{api_url}/run", json={"message": query}, timeout=60.0)
        resp.raise_for_status()
        data = resp.json()
        for a in AGENTS:
            ss["agent_status"][a] = "done"
            ss["agent_detail"][a] = "Complete"
        ss["settlement"] = {"status": "SETTLED", "message": data["response"], "settlement_id": "LIVE"}
    except Exception as e:
        ss["error"] = str(e)
        for a in AGENTS:
            ss["agent_status"][a] = "blocked"
    yield


# ── Agent card renderer ───────────────────────────────────────────────────────
def render_agent_card(name: str):
    status = st.session_state["agent_status"][name]
    detail = st.session_state["agent_detail"][name]
    icon = AGENT_ICONS[name]
    desc = AGENT_DESC[name]

    status_text = {
        "idle": "⏸ Waiting",
        "running": "⚡ Running",
        "done": "✅ Complete",
        "blocked": "🚫 Blocked",
    }.get(status, status)

    css_class = "agent-card" + (" running" if status == "running" else " done" if status == "done" else " blocked" if status == "blocked" else "")

    badge_color = {"idle": "#8b949e", "running": "#f0b429", "done": "#3fb950", "blocked": "#f85149"}.get(status, "#8b949e")

    st.markdown(f"""
    <div class="{css_class}">
        <div class="agent-name">{icon} {name}</div>
        <div class="agent-status" style="color:{badge_color};">{status_text}</div>
        <div style="font-size:0.8rem; color:#8b949e; margin-top:6px;">{detail or desc}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 10])
with col_logo:
    st.markdown("<div style='font-size:3rem; margin-top:10px;'>🌐</div>", unsafe_allow_html=True)
with col_title:
    st.markdown("# Aura — Autonomous Reliable Agentic Commerce")
    st.markdown("<div class='subtitle'>Google AI Agent Labs Oslo 2026 &nbsp;·&nbsp; Team 6 &nbsp;·&nbsp; Multi-Agent B2B Procurement with Built-in KYC/AML Compliance</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ── Main layout ───────────────────────────────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown("### 🎯 Procurement Request")

    # Quick demo buttons
    st.markdown("**Quick demos:**")
    btnc1, btnc2 = st.columns(2)
    with btnc1:
        if st.button("✅ Happy Path", help="Legitimate vendor — full settlement"):
            st.session_state["prefill"] = "Buy 3 Laptop Pro 15 units from the best available vendor"
    with btnc2:
        if st.button("🚫 Block Demo", help="ShadowHardware — compliance blocked"):
            st.session_state["prefill"] = "Buy laptops from ShadowHardware"

    default_query = st.session_state.get("prefill", "Buy 3 Laptop Pro 15 units from the best available vendor")
    query = st.text_input(
        "Enter a procurement request:",
        value=default_query,
        label_visibility="collapsed",
        placeholder="e.g. Buy 5 Laptop Pro 15 units from the best vendor",
    )

    mode = st.radio("Mode", ["🎭 Demo (safe)", "🔴 Live (Vertex AI)"], horizontal=True)
    st.session_state["mode"] = "live" if "Live" in mode else "demo"

    if st.session_state["mode"] == "live":
        api_url = st.text_input("FastAPI URL", value="http://localhost:8080")
    else:
        api_url = "http://localhost:8080"

    run_clicked = st.button("▶ Run Aura Pipeline", type="primary")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # ── Agent pipeline cards ───────────────────────────────────────────────
    st.markdown("### 🤖 Agent Pipeline")
    agent_placeholders = {a: st.empty() for a in AGENTS}

    def refresh_cards():
        for a in AGENTS:
            with agent_placeholders[a]:
                render_agent_card(a)

    refresh_cards()

    # ── Tech stack ────────────────────────────────────────────────────────
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Stack")
    st.markdown("""
    <div style='font-size:0.85rem; color:#8b949e; line-height:1.8;'>
    🤖 <b>Google ADK</b> — Agent orchestration<br>
    ✨ <b>Gemini 2.0 Flash</b> — LLM via Vertex AI<br>
    🌐 <b>UCP</b> — Vendor discovery protocol<br>
    🔐 <b>AP2</b> — Agent payments protocol<br>
    🏦 <b>BMS</b> — Core banking compliance<br>
    ☸️ <b>Kagent</b> — Kubernetes CRD deployment<br>
    ☁️ <b>GCP europe-north1</b>
    </div>
    """, unsafe_allow_html=True)


with right:
    st.markdown("### 📊 Pipeline Results")

    vendor_placeholder = st.empty()
    compliance_placeholder = st.empty()
    settlement_placeholder = st.empty()

    def render_results():
        vendors = st.session_state.get("vendors", [])
        compliance = st.session_state.get("compliance", [])
        settlement = st.session_state.get("settlement")
        blocked_vendor = st.session_state.get("blocked_vendor")
        error = st.session_state.get("error")

        # ── Vendor table ──────────────────────────────────────────────────
        with vendor_placeholder:
            if vendors:
                st.markdown("#### 🔭 Vendors Discovered (UCP)")
                rows_html = ""
                for v in vendors:
                    flag = "🚩" if v["country"] == "XX" else "✅"
                    price_color = "#f85149" if v["unit_price_usd"] < 1000 else "#e6edf3"
                    rows_html += f"""
                    <tr>
                        <td style='padding:8px 12px; border-bottom:1px solid #30363d;'>{v['name']}</td>
                        <td style='padding:8px 12px; border-bottom:1px solid #30363d; color:{price_color}; font-weight:600;'>${v['unit_price_usd']:,.2f}</td>
                        <td style='padding:8px 12px; border-bottom:1px solid #30363d;'>{v['available_units']} units</td>
                        <td style='padding:8px 12px; border-bottom:1px solid #30363d;'>{flag} {v['country']}</td>
                    </tr>"""

                st.markdown(f"""
                <div class='result-card'>
                <table style='width:100%; border-collapse:collapse; font-size:0.9rem;'>
                <thead>
                <tr style='color:#8b949e; border-bottom:1px solid #30363d;'>
                    <th style='padding:8px 12px; text-align:left;'>Vendor</th>
                    <th style='padding:8px 12px; text-align:left;'>Unit Price</th>
                    <th style='padding:8px 12px; text-align:left;'>Stock</th>
                    <th style='padding:8px 12px; text-align:left;'>Country</th>
                </tr>
                </thead>
                <tbody>{rows_html}</tbody>
                </table>
                </div>
                """, unsafe_allow_html=True)
            elif st.session_state["agent_status"]["Scout"] == "idle":
                st.markdown("<div class='result-card' style='color:#8b949e; text-align:center; padding:40px;'>🔭 Vendor discovery results will appear here</div>", unsafe_allow_html=True)

        # ── Compliance table ───────────────────────────────────────────────
        with compliance_placeholder:
            if compliance:
                st.markdown("#### 🛡️ Sentinel Compliance Results")
                rows_html = ""
                for c in compliance:
                    if c["status"] == "APPROVED":
                        badge = "<span class='badge-approved'>✅ APPROVED</span>"
                        hash_display = f"<span style='font-family:monospace; font-size:0.75rem; color:#8b949e;'>{c['compliance_hash'][:16]}…</span>"
                    else:
                        badge = "<span class='badge-rejected'>🚫 REJECTED</span>"
                        hash_display = f"<span style='color:#f85149; font-size:0.8rem;'>{c.get('reason','AML_BLACKLIST')}</span>"

                    rows_html += f"""
                    <tr>
                        <td style='padding:8px 12px; border-bottom:1px solid #30363d; font-weight:500;'>{c['name']}</td>
                        <td style='padding:8px 12px; border-bottom:1px solid #30363d;'>{badge}</td>
                        <td style='padding:8px 12px; border-bottom:1px solid #30363d;'>{hash_display}</td>
                    </tr>"""

                st.markdown(f"""
                <div class='result-card'>
                <table style='width:100%; border-collapse:collapse; font-size:0.9rem;'>
                <thead>
                <tr style='color:#8b949e; border-bottom:1px solid #30363d;'>
                    <th style='padding:8px 12px; text-align:left;'>Vendor</th>
                    <th style='padding:8px 12px; text-align:left;'>Compliance Status</th>
                    <th style='padding:8px 12px; text-align:left;'>Hash / Reason</th>
                </tr>
                </thead>
                <tbody>{rows_html}</tbody>
                </table>
                </div>
                """, unsafe_allow_html=True)

        # ── Settlement / Block result ──────────────────────────────────────
        with settlement_placeholder:
            if error:
                st.markdown(f"""
                <div class='blocked-card'>
                    <div style='font-size:2.5rem;'>⚠️</div>
                    <div style='font-size:1.2rem; font-weight:700; color:#f85149; margin-top:8px;'>ERROR</div>
                    <div style='color:#8b949e; margin-top:8px; font-size:0.9rem;'>{error}</div>
                </div>""", unsafe_allow_html=True)

            elif blocked_vendor and not settlement:
                st.markdown(f"""
                <div class='blocked-card'>
                    <div style='font-size:3rem;'>🚫</div>
                    <div style='font-size:1.4rem; font-weight:700; color:#f85149; margin-top:12px;'>COMPLIANCE BLOCKED</div>
                    <div style='color:#e6edf3; margin-top:8px;'>Vendor <b>{blocked_vendor}</b> is on the AML blacklist</div>
                    <div style='color:#8b949e; margin-top:8px; font-size:0.9rem;'>No payment was initiated. Contact the compliance team.</div>
                    <div style='margin-top:16px; padding:12px; background:#2d1515; border-radius:6px; font-size:0.85rem; color:#f85149;'>
                        🔒 AP2 Intent Mandate was never generated — transaction provably blocked
                    </div>
                </div>""", unsafe_allow_html=True)

            elif settlement and settlement.get("status") == "SETTLED":
                s = settlement
                vendor = s.get("vendor", "")
                amount = s.get("amount", 0)
                currency = s.get("currency", "USD")
                sid = s.get("settlement_id", "")
                st.markdown(f"""
                <div class='settled-card'>
                    <div style='font-size:3rem;'>✅</div>
                    <div style='font-size:1.4rem; font-weight:700; color:#3fb950; margin-top:12px;'>SETTLEMENT CONFIRMED</div>
                    <div style='margin-top:20px; display:flex; justify-content:center; gap:40px;'>
                        <div>
                            <div class='metric-big'>${amount:,.2f}</div>
                            <div class='metric-label'>{currency}</div>
                        </div>
                        <div>
                            <div class='metric-big' style='font-size:1.2rem;'>{vendor}</div>
                            <div class='metric-label'>Selected vendor</div>
                        </div>
                    </div>
                    <div style='margin-top:20px; padding:12px; background:#0d2117; border-radius:6px; font-size:0.85rem; color:#8b949e;'>
                        🔐 Settlement ID: <span style='font-family:monospace; color:#3fb950;'>{sid}</span>
                    </div>
                    <div style='margin-top:8px; font-size:0.8rem; color:#8b949e;'>
                        Routed via AP2 Compliant Banking Gateway · ECDSA-P256 signed mandate
                    </div>
                </div>""", unsafe_allow_html=True)

            elif settlement and settlement.get("status") == "SETTLED_LIVE":
                st.markdown(f"""
                <div class='settled-card'>
                    <div style='font-size:2rem;'>✅</div>
                    <div style='color:#3fb950; font-weight:700; font-size:1.2rem; margin-top:8px;'>LIVE AGENT RESPONSE</div>
                    <div style='color:#e6edf3; margin-top:12px; text-align:left; font-size:0.9rem; white-space:pre-wrap;'>{settlement.get('message','')}</div>
                </div>""", unsafe_allow_html=True)

            elif not vendors:
                st.markdown("""
                <div style='text-align:center; padding:60px 40px; color:#8b949e; font-size:1rem;'>
                    <div style='font-size:4rem; margin-bottom:16px;'>🌐</div>
                    <div>Submit a procurement request to start the Aura pipeline</div>
                    <div style='font-size:0.85rem; margin-top:8px;'>Scout → Sentinel → Closer</div>
                </div>""", unsafe_allow_html=True)

    render_results()


# ── Run the pipeline ──────────────────────────────────────────────────────────
if run_clicked and query:
    if st.session_state["mode"] == "demo":
        generator = run_demo(query)
    else:
        generator = run_live(query, api_url)

    for _ in generator:
        refresh_cards()
        render_results()
        time.sleep(0.05)

    refresh_cards()
    render_results()

    # Clear prefill after run
    if "prefill" in st.session_state:
        del st.session_state["prefill"]
