# Aura — Procurement Dashboard

## Overview

The Aura dashboard is a **Streamlit** web application that provides a visual interface for the full procurement pipeline. It shows each agent running in real time, displays vendor discovery results, compliance decisions, and the final settlement outcome — all with a dark GitHub-style theme.

**File:** `ui/dashboard.py`

---

## Running the Dashboard

```bash
# Activate virtualenv first
source .venv/bin/activate

# Launch from the project root
streamlit run ui/dashboard.py
```

The dashboard opens automatically at `http://localhost:8501`.

---

## Modes

### Demo Mode (default)

Runs the actual tool functions (`discover_vendors`, `verify_vendor_compliance`, `generate_intent_mandate`, `settle_cart_mandate`) directly in-process with simulated timing delays. **No Gemini / Vertex AI credentials required.** Ideal for quick demos and local development.

### API Mode

Calls the Aura FastAPI server at `http://localhost:8080/run`. Requires the server to be running:

```bash
uvicorn main:app --reload --port 8080
```

Switch between modes in the dashboard sidebar.

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🌐  Aura · Autonomous Commerce                             │
│  Google AI Agent Labs Oslo 2026 · Team 6                    │
├────────────────────────┬────────────────────────────────────┤
│  Procurement Request   │  Agent Pipeline                    │
│  ┌──────────────────┐  │  ┌─────────────┐  ┌────────────┐  │
│  │  [text input]    │  │  │ 🏛️ Architect│  │ 🔭 Scout  │  │
│  └──────────────────┘  │  └─────────────┘  └────────────┘  │
│  [ Launch Procurement ]│  ┌─────────────┐  ┌────────────┐  │
│                        │  │ 🛡️ Sentinel │  │ 💳 Closer │  │
│  Quick paths:          │  └─────────────┘  └────────────┘  │
│  • Happy path          ├────────────────────────────────────┤
│  • Blocked path        │  Vendor Table / Results            │
└────────────────────────┴────────────────────────────────────┘
```

---

## Agent Status Cards

Each agent card updates in real time with one of three states:

| State | Border colour | Meaning |
| :--- | :--- | :--- |
| `running` | 🟡 Yellow | Agent is currently executing |
| `done` | 🟢 Green | Agent completed successfully |
| `blocked` | 🔴 Red | Compliance block detected |
| `idle` | Grey | Not yet invoked |

---

## Pipeline Outputs Displayed

### Vendor Discovery (Scout)

A table showing all discovered vendors:

| Field | Description |
| :--- | :--- |
| Vendor Name | Trading name |
| Product | Item discovered |
| Unit Price | Price in USD |
| Units | Available stock |
| Country | Origin code (`XX` = flagged risky) |

### Compliance Results (Sentinel)

Each vendor shown with an **APPROVED** (green badge) or **REJECTED** (red badge) status and reason code.

### Settlement Result (Closer)

**Success:**
```
✅ SETTLEMENT CONFIRMED
NordHardware AS
$3,840.00 USD
Settlement ID: AP2-3X7K9F2A1B4C
```

**Blocked:**
```
⛔ TRANSACTION BLOCKED
ShadowHardware
AML_BLACKLIST
No payment was initiated.
```

---

## Quick Demo Paths

The dashboard provides two one-click demo buttons:

| Button | Query | Expected outcome |
| :--- | :--- | :--- |
| **Happy Path** | `"Buy 3 Laptop Pro 15 units from best vendor"` | Vendor selected, compliance passed, AP2 settled |
| **Blocked Path** | `"Buy laptops from ShadowHardware"` | Sentinel REJECTED, pipeline halted, no payment |

---

## Session State

The dashboard uses `st.session_state` to track:

| Key | Type | Description |
| :--- | :--- | :--- |
| `running` | `bool` | Whether pipeline is currently executing |
| `agent_status` | `dict` | Per-agent status: `idle/running/done/blocked` |
| `agent_detail` | `dict` | Per-agent status text |
| `vendors` | `list` | Vendor list from Scout |
| `compliance` | `list` | Compliance results from Sentinel |
| `settlement` | `dict \| None` | Settlement result from Closer |
| `blocked_vendor` | `str \| None` | Name of any blocked vendor |
| `mode` | `str` | `"demo"` or `"api"` |
