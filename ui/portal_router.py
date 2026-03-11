"""
Aura Portal — FastAPI router providing demo-data endpoints for the role-based portal.
All state is seeded in-memory at module load.
Mount this router in main.py:
    from ui.portal_router import router as portal_router
    app.include_router(portal_router)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/portal", tags=["portal"])


def _ts(offset_minutes: int = 0) -> str:
    dt = datetime.utcnow() - timedelta(minutes=offset_minutes)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _uid() -> str:
    return str(uuid.uuid4())[:8].upper()


_PROCUREMENT_HISTORY: list[dict[str, Any]] = [
    {"id":"REQ-001","description":"Buy 3 Laptop Pro 15 from best vendor","category":"hardware","amount_usd":3897.00,"status":"SETTLED","vendor":"TechCorp Nordic","settlement_id":"AP2-3X7K9F2A1B4C","submitted_by":"alice@acme.no","submitted_at":_ts(45)},
    {"id":"REQ-002","description":"SaaS subscription — 10 seats Atlassian Jira Cloud","category":"saas","amount_usd":2400.00,"status":"SETTLED","vendor":"SoftWave AS","settlement_id":"AP2-8A2N5T0X3Q1F","submitted_by":"bob@acme.no","submitted_at":_ts(120)},
    {"id":"REQ-003","description":"AWS cloud hosting — 12-month reserved","category":"cloud_infrastructure","amount_usd":4800.00,"status":"REVIEW","vendor":"CloudNorth Ltd","settlement_id":None,"submitted_by":"alice@acme.no","submitted_at":_ts(30)},
    {"id":"REQ-004","description":"Buy 5 server units from ShadowHardware","category":"hardware","amount_usd":6500.00,"status":"BLOCKED","vendor":"ShadowHardware","settlement_id":None,"submitted_by":"eve@acme.no","submitted_at":_ts(60)},
    {"id":"REQ-005","description":"Office chairs x20 — ergonomic","category":"office_supplies","amount_usd":980.00,"status":"SETTLED","vendor":"FurniPro AS","settlement_id":"AP2-C5D2E8F3A1B7","submitted_by":"bob@acme.no","submitted_at":_ts(200)},
    {"id":"REQ-006","description":"Agile development sprint — 4 weeks","category":"agile_development","amount_usd":4200.00,"status":"REVIEW","vendor":"DevTeam Norway","settlement_id":None,"submitted_by":"carol@acme.no","submitted_at":_ts(15)},
]

_PENDING_APPROVALS: list[dict[str, Any]] = [
    {"id":"REQ-003","description":"AWS cloud hosting — 12-month reserved","category":"cloud_infrastructure","amount_usd":4800.00,"vendor":"CloudNorth Ltd","submitted_by":"alice@acme.no","submitted_at":_ts(30),"status":"PENDING","approver_note":""},
    {"id":"REQ-006","description":"Agile development sprint — 4 weeks","category":"agile_development","amount_usd":4200.00,"vendor":"DevTeam Norway","submitted_by":"carol@acme.no","submitted_at":_ts(15),"status":"PENDING","approver_note":""},
    {"id":"REQ-007","description":"Enterprise security audit — external consultants","category":"consulting","amount_usd":4950.00,"vendor":"SecureNordic AS","submitted_by":"dave@acme.no","submitted_at":_ts(5),"status":"PENDING","approver_note":""},
]

_COMPLIANCE_EVENTS: list[dict[str, Any]] = [
    {"id":"EVT-001","event_type":"AML_BLOCK","vendor":"ShadowHardware","vendor_country":"XX","compliance_hash":"a3f9c2e4b1d7f8a2c9e3b5d1f7a4c8e2b6f1d9c4a7e2b8d5f3a6c1e9b4d7f2","reason":"Vendor on AML blacklist — sanctioned entity","severity":"HIGH","status":"BLOCKED","timestamp":_ts(60),"request_id":"REQ-004"},
    {"id":"EVT-002","event_type":"KYC_PASS","vendor":"TechCorp Nordic","vendor_country":"NO","compliance_hash":"f8d3c5a1e7b4c9d2f6a3e8b1c4d7f2a5e9c3b6d8f1a4c7e2b5d9f3a2c6e1b4","reason":"Vendor passed KYC/AML checks","severity":"LOW","status":"APPROVED","timestamp":_ts(45),"request_id":"REQ-001"},
    {"id":"EVT-003","event_type":"POLICY_REVIEW","vendor":"CloudNorth Ltd","vendor_country":"SE","compliance_hash":"c2e8a4f1b7d5c9e3a6f2b8d4c1e7a3f5b9d2c6e8a1f4b7d3c5e9a2f6b1d4c8","reason":"High-value transaction requires manager approval ($4,800 > $4,000 threshold)","severity":"MEDIUM","status":"REVIEW","timestamp":_ts(30),"request_id":"REQ-003"},
    {"id":"EVT-004","event_type":"KYC_PASS","vendor":"SoftWave AS","vendor_country":"NO","compliance_hash":"d5a2c8f4b1e7a3c9d6f2b5e8c1a4f7d3b9e2c5a8f1d4b7e3c6a9f2d5b8e1c4","reason":"Vendor passed KYC/AML checks","severity":"LOW","status":"APPROVED","timestamp":_ts(120),"request_id":"REQ-002"},
    {"id":"EVT-005","event_type":"COUNTRY_SANCTION","vendor":"RussianTech Ltd","vendor_country":"RU","compliance_hash":"e9b3d6f2c5a1e4b7d9c3f6a2e5b8d1c4f7a3e6b9d2c5f8a1e4b7d3c6f9a2e5","reason":"Vendor country RU is on OFAC sanctions list","severity":"HIGH","status":"BLOCKED","timestamp":_ts(90),"request_id":"REQ-008"},
    {"id":"EVT-006","event_type":"KYC_PASS","vendor":"FurniPro AS","vendor_country":"NO","compliance_hash":"b4f8d2a6e9c3b7f1d5a9e2c6b3f7d1a5e8c2b6f9d3a7e1c5b8f2d6a3e7c1b5","reason":"Vendor passed KYC/AML checks","severity":"LOW","status":"APPROVED","timestamp":_ts(200),"request_id":"REQ-005"},
]

_BLOCKED_VENDORS: list[dict[str, Any]] = [
    {"vendor":"ShadowHardware","country":"XX","reason":"AML blacklist — sanctioned entity","blocked_at":_ts(200),"block_type":"AML_BLACKLIST","request_count":3},
    {"vendor":"RussianTech Ltd","country":"RU","reason":"OFAC sanctioned country code RU","blocked_at":_ts(500),"block_type":"COUNTRY_SANCTION","request_count":1},
    {"vendor":"NorthKoreaElec","country":"KP","reason":"OFAC sanctioned country code KP","blocked_at":_ts(2000),"block_type":"COUNTRY_SANCTION","request_count":1},
]

_VENDOR_CATALOG: list[dict[str, Any]] = [
    {"id":"v-001","name":"TechCorp Nordic","capability":"dev.ucp.hardware","products":["Laptop Pro 15","WorkStation X1"],"unit_price_usd":1299.00,"available_units":47,"country":"NO","compliance_status":"APPROVED","last_checked":_ts(45)},
    {"id":"v-002","name":"SoftWave AS","capability":"dev.ucp.saas","products":["Jira Cloud","Confluence Cloud","Bitbucket"],"unit_price_usd":240.00,"available_units":999,"country":"NO","compliance_status":"APPROVED","last_checked":_ts(120)},
    {"id":"v-003","name":"CloudNorth Ltd","capability":"dev.ucp.cloud","products":["Hosted VM","Object Storage","Managed Kubernetes"],"unit_price_usd":400.00,"available_units":500,"country":"SE","compliance_status":"REVIEW","last_checked":_ts(30)},
    {"id":"v-004","name":"ByteStream DK","capability":"dev.ucp.hardware","products":["Laptop Pro 15 (Refurb)","Monitor 27"],"unit_price_usd":1099.00,"available_units":12,"country":"DK","compliance_status":"APPROVED","last_checked":_ts(80)},
    {"id":"v-005","name":"FurniPro AS","capability":"dev.ucp.office","products":["Ergonomic Chair","Standing Desk","Monitor Arm"],"unit_price_usd":49.00,"available_units":200,"country":"NO","compliance_status":"APPROVED","last_checked":_ts(200)},
    {"id":"v-006","name":"DevTeam Norway","capability":"dev.ucp.consulting","products":["Agile Sprint","Code Review","Architecture Consulting"],"unit_price_usd":1050.00,"available_units":8,"country":"NO","compliance_status":"APPROVED","last_checked":_ts(15)},
]

_SSA_CONTRACTS: list[dict[str, Any]] = [
    {"id":"SSA-001","type":"SSA-L","type_label":"Lisens (SaaS)","vendor":"SoftWave AS","description":"10-seat Atlassian Jira + Confluence Cloud license","amount_usd":2400.00,"start_date":"2026-01-01","end_date":"2026-12-31","status":"ACTIVE","auto_renew":True},
    {"id":"SSA-002","type":"SSA-K","type_label":"Kjøp (Hardware)","vendor":"TechCorp Nordic","description":"3x Laptop Pro 15 one-off purchase","amount_usd":3897.00,"start_date":"2026-03-11","end_date":"2026-03-11","status":"COMPLETED","auto_renew":False},
    {"id":"SSA-003","type":"SSA-D","type_label":"Drift (Managed Hosting)","vendor":"CloudNorth Ltd","description":"12-month Managed Kubernetes + Object Storage","amount_usd":4800.00,"start_date":"2026-04-01","end_date":"2027-03-31","status":"PENDING_APPROVAL","auto_renew":True},
    {"id":"SSA-004","type":"SSA-S","type_label":"Smidig (Agile Dev)","vendor":"DevTeam Norway","description":"4-week agile development sprint — API integration","amount_usd":4200.00,"start_date":"2026-03-17","end_date":"2026-04-11","status":"PENDING_APPROVAL","auto_renew":False},
    {"id":"SSA-005","type":"SSA-sky","type_label":"Sky (Gov Cloud)","vendor":"CloudNorth Ltd","description":"Government cloud compute — 6-month pilot","amount_usd":3600.00,"start_date":"2026-02-01","end_date":"2026-07-31","status":"ACTIVE","auto_renew":False},
]

_AGENT_METRICS: dict[str, Any] = {
    "total_requests":47,"settled":31,"blocked":8,"review":5,"failed":3,"avg_latency_ms":3240,
    "agents":{
        "Architect":{"invocations":47,"errors":1,"avg_ms":310},
        "Governor":{"invocations":46,"errors":0,"avg_ms":210},
        "Scout":{"invocations":44,"errors":2,"avg_ms":1420},
        "Sentinel":{"invocations":42,"errors":0,"avg_ms":860},
        "Closer":{"invocations":32,"errors":0,"avg_ms":480},
    },
    "last_updated":_ts(0),
}

_POLICIES: list[dict[str, Any]] = [
    {"id":"POL-001","name":"Spending Cap","rule_type":"spending_limit","enabled":True,"severity":"BLOCK","parameters":{"max_usd":5000},"description":"Block transactions above $5,000 per request"},
    {"id":"POL-002","name":"High-Value Review","rule_type":"review_threshold","enabled":True,"severity":"REVIEW","parameters":{"threshold_usd":4000},"description":"Flag transactions above $4,000 for manager approval"},
    {"id":"POL-003","name":"Sanctioned Countries","rule_type":"country_block","enabled":True,"severity":"BLOCK","parameters":{"blocked_codes":["IR","KP","RU","SY","XX"]},"description":"Block vendors from OFAC-sanctioned countries"},
    {"id":"POL-004","name":"Category Allowlist","rule_type":"category_filter","enabled":True,"severity":"BLOCK","parameters":{"mode":"allowlist"},"description":"Only approved procurement categories permitted"},
    {"id":"POL-005","name":"Warn Large Purchase","rule_type":"warn_threshold","enabled":True,"severity":"WARN","parameters":{"threshold_usd":2000},"description":"Attach warning note for purchases above $2,000"},
]

_REVIEW_QUEUE: list[dict[str, Any]] = [
    {"id":"REQ-003","description":"AWS cloud hosting — 12-month reserved","amount_usd":4800.00,"vendor":"CloudNorth Ltd","submitted_by":"alice@acme.no","submitted_at":_ts(30),"policy_id":"POL-002","status":"PENDING"},
    {"id":"REQ-006","description":"Agile development sprint — 4 weeks","amount_usd":4200.00,"vendor":"DevTeam Norway","submitted_by":"carol@acme.no","submitted_at":_ts(15),"policy_id":"POL-002","status":"PENDING"},
    {"id":"REQ-007","description":"Enterprise security audit — external consultants","amount_usd":4950.00,"vendor":"SecureNordic AS","submitted_by":"dave@acme.no","submitted_at":_ts(5),"policy_id":"POL-002","status":"PENDING"},
]


# ── Procurement ───────────────────────────────────────────────────────────────

@router.get("/procurement/history")
async def get_procurement_history() -> list[dict[str, Any]]:
    return _PROCUREMENT_HISTORY


@router.get("/procurement/pipelines")
async def get_active_pipelines() -> list[dict[str, Any]]:
    return [
        {"request_id":"REQ-003","description":"AWS cloud hosting — 12-month reserved","agents":{"Architect":"done","Governor":"done","Scout":"done","Sentinel":"done","Closer":"blocked"},"current_stage":"Awaiting finance approval","started_at":_ts(30)},
        {"request_id":"REQ-006","description":"Agile development sprint — 4 weeks","agents":{"Architect":"done","Governor":"done","Scout":"done","Sentinel":"done","Closer":"blocked"},"current_stage":"Awaiting finance approval","started_at":_ts(15)},
    ]


class SubmitRequest(BaseModel):
    message: str
    user_id: str = "portal-user"


@router.post("/procurement/submit")
async def submit_procurement(req: SubmitRequest) -> dict[str, Any]:
    new_id = f"REQ-{_uid()}"
    return {"request_id":new_id,"status":"SUBMITTED","message":f"Request '{req.message[:80]}' submitted. The Aura agent pipeline will process it shortly.","submitted_at":_ts(0),"mode":"demo"}


# ── Finance ────────────────────────────────────────────────────────────────────

@router.get("/finance/pending")
async def get_pending_approvals() -> list[dict[str, Any]]:
    return _PENDING_APPROVALS


@router.post("/finance/approve/{item_id}")
async def approve_item(item_id: str) -> dict[str, Any]:
    for item in _PENDING_APPROVALS:
        if item["id"] == item_id:
            item["status"] = "APPROVED"
            return {"id": item_id, "status": "APPROVED"}
    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")


@router.post("/finance/reject/{item_id}")
async def reject_item(item_id: str) -> dict[str, Any]:
    for item in _PENDING_APPROVALS:
        if item["id"] == item_id:
            item["status"] = "REJECTED"
            return {"id": item_id, "status": "REJECTED"}
    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")


# ── Compliance ─────────────────────────────────────────────────────────────────

@router.get("/compliance/events")
async def get_compliance_events() -> list[dict[str, Any]]:
    return _COMPLIANCE_EVENTS


@router.get("/compliance/blocked")
async def get_blocked_vendors() -> list[dict[str, Any]]:
    return _BLOCKED_VENDORS


@router.get("/compliance/stats")
async def get_compliance_stats() -> dict[str, Any]:
    total = len(_COMPLIANCE_EVENTS)
    approved = sum(1 for e in _COMPLIANCE_EVENTS if e["status"] == "APPROVED")
    blocked  = sum(1 for e in _COMPLIANCE_EVENTS if e["status"] == "BLOCKED")
    review   = sum(1 for e in _COMPLIANCE_EVENTS if e["status"] == "REVIEW")
    return {"total_checks":total,"approved":approved,"blocked":blocked,"review":review,"block_rate_pct":round(blocked/total*100,1) if total else 0,"approval_rate_pct":round(approved/total*100,1) if total else 0}


# ── IT Manager ────────────────────────────────────────────────────────────────

@router.get("/itmanager/vendors")
async def get_vendor_catalog() -> list[dict[str, Any]]:
    return _VENDOR_CATALOG


@router.get("/itmanager/contracts")
async def get_ssa_contracts() -> list[dict[str, Any]]:
    return _SSA_CONTRACTS


# ── Admin ──────────────────────────────────────────────────────────────────────

@router.get("/admin/metrics")
async def get_admin_metrics() -> dict[str, Any]:
    return _AGENT_METRICS


@router.get("/admin/policies")
async def get_policies() -> list[dict[str, Any]]:
    return _POLICIES


@router.get("/admin/queue")
async def get_review_queue() -> list[dict[str, Any]]:
    return _REVIEW_QUEUE


@router.post("/admin/review-queue/resolve/{item_id}")
async def resolve_review_item(item_id: str, action: str = "approve") -> dict[str, Any]:
    for item in _REVIEW_QUEUE:
        if item["id"] == item_id:
            item["status"] = "APPROVED" if action == "approve" else "REJECTED"
            return {"id": item_id, "status": item["status"]}
    raise HTTPException(status_code=404, detail=f"Review item {item_id} not found")
