# Aura — Dashboard & Portal

## Overview

Aura ships two complementary UIs:

| UI | Tech | URL | Purpose |
|:---|:-----|:----|:--------|
| **Streamlit Dashboard** | Streamlit (Python) | `http://localhost:8501` | Agent pipeline demo & visualization |
| **Role-Based Portal** | HTML/CSS/JS + FastAPI | `http://localhost:8000/portal/` | Enterprise stakeholder portal |

---

## Streamlit Dashboard

The Streamlit dashboard provides a visual interface for the full procurement pipeline. It shows each agent running in real time, displays vendor discovery results, compliance decisions, and the final settlement outcome.

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

Runs the actual tool functions (`discover_vendors`, `verify_vendor_compliance`, `generate_intent_mandate`, `settle_cart_mandate`) directly in-process with simulated timing delays. No AI model is involved — results are deterministic and come from mock data. **No Gemini / Vertex AI credentials required.** Ideal for quick demos and local development.

### Live Mode (Vertex AI)

Sends the procurement request to the FastAPI `/run` endpoint, which runs the **real Google ADK `Runner`** with **Gemini 2.5 Flash** on Vertex AI. The request flows through the actual multi-agent pipeline:

1. Intent is parsed and validated by `parse_procurement_intent`
2. A `genai_types.Content` message is constructed
3. `Runner.run_async()` sends it to Gemini, which orchestrates the Architect → Governor → Scout → Sentinel → Closer agents
4. Gemini decides which tools to call and how to coordinate the agents

Requires the FastAPI server to be running:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Prerequisites for Live mode:**

| Requirement | Details |
|:------------|:--------|
| FastAPI server | Running on `http://localhost:8000` |
| Google Cloud credentials | `GOOGLE_CLOUD_PROJECT` or `GOOGLE_API_KEY` env var set |
| Auth header | Valid API key for the `/run` endpoint |

Switch between modes using the radio button in the dashboard sidebar.

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

---

## Role-Based Portal

The portal is a traditional web application that simulates what different enterprise stakeholders would see in a production Aura deployment. It is served as static files by the FastAPI server and backed by dedicated API endpoints.

**Files:** `ui/static/index.html`, `ui/static/css/portal.css`, `ui/static/js/portal.js`, `ui/portal_router.py`

---

### Running the Portal

```bash
source .venv/bin/activate

# Launch the FastAPI server (serves both the API and the portal)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The portal is available at `http://localhost:8000/portal/`.

---

### Roles & Views

The portal sidebar provides a role selector. Each role unlocks a different set of views:

| Role | Views |
|:-----|:------|
| **Procurement Officer** | Request History, Active Pipelines, Submit New Request |
| **Finance Approver** | Pending Approvals, Approval History |
| **Compliance Officer** | Compliance Events, Blocked Vendors, Compliance Stats |
| **IT Manager** | Vendor Catalog, SSA Contracts |
| **Admin** | Agent Metrics, Policies, Review Queue, System Overview |

---

### Portal API Endpoints

All portal endpoints are prefixed with `/api/portal` and served by `ui/portal_router.py`.

#### Procurement

| Method | Path | Description |
|:-------|:-----|:------------|
| `GET` | `/api/portal/procurement/history` | Full list of historical procurement requests |
| `GET` | `/api/portal/procurement/pipelines` | Currently active pipelines with per-agent stage status |
| `POST` | `/api/portal/procurement/submit` | Submit a new procurement request |

#### Finance

| Method | Path | Description |
|:-------|:-----|:------------|
| `GET` | `/api/portal/finance/pending` | Requests pending finance approval |
| `GET` | `/api/portal/finance/history` | Resolved (approved/rejected) finance items |
| `POST` | `/api/portal/finance/approve/{item_id}` | Approve a pending item |
| `POST` | `/api/portal/finance/reject/{item_id}` | Reject a pending item |

#### Compliance

| Method | Path | Description |
|:-------|:-----|:------------|
| `GET` | `/api/portal/compliance/events` | Audit log of all compliance check events |
| `GET` | `/api/portal/compliance/blocked` | Vendors on the compliance block list |
| `GET` | `/api/portal/compliance/stats` | Aggregate compliance statistics |

#### IT Manager

| Method | Path | Description |
|:-------|:-----|:------------|
| `GET` | `/api/portal/itmanager/vendors` | Vendor catalog with compliance status and inventory |
| `GET` | `/api/portal/itmanager/contracts` | SSA contracts (Lisens, Kjøp, Drift, Smidig, Sky) |

#### Admin

| Method | Path | Description |
|:-------|:-----|:------------|
| `GET` | `/api/portal/admin/metrics` | Agent invocation metrics and system health |
| `GET` | `/api/portal/admin/policies` | Active policy rules (Governor/Sentinel) |
| `GET` | `/api/portal/admin/queue` | Review queue for pending compliance reviews |
| `POST` | `/api/portal/admin/review-queue/resolve/{item_id}` | Resolve a review-queue item |

#### System

| Method | Path | Description |
|:-------|:-----|:------------|
| `GET` | `/api/portal/overview` | Consolidated system overview (counts, agents, recent history) |
| `GET` | `/api/portal/capabilities` | Runtime capabilities (Gemini availability) |
| `POST` | `/api/portal/run/demo` | Run the agent pipeline in demo mode (SSE stream) |

---

### Demo Data

The portal ships with pre-seeded in-memory data to showcase all views without external dependencies:

| Dataset | Records | Key statuses |
|:--------|:--------|:-------------|
| Procurement History | REQ-001 → REQ-006 | SETTLED, REVIEW, BLOCKED |
| Pending Approvals | REQ-003, REQ-006, REQ-007 | PENDING |
| Compliance Events | EVT-001 → EVT-006 | APPROVED, BLOCKED, REVIEW |
| Blocked Vendors | 3 vendors | ShadowHardware, RussianTech Ltd, NorthKoreaElec |
| Vendor Catalog | 6 vendors | NO, SE, DK countries |
| SSA Contracts | SSA-001 → SSA-005 | ACTIVE, COMPLETED, PENDING_APPROVAL |
| Policy Rules | POL-001 → POL-005 | Spending Cap, Country Block, Review Threshold |
