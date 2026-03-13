"""
Tests for the Aura Portal Dashboard — FastAPI portal_router endpoints.
Covers procurement, finance, compliance, IT-manager, admin, overview,
capabilities, and the demo SSE pipeline.
"""

from __future__ import annotations

import json
import sys
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ui.portal_router import router, _PENDING_APPROVALS, _REVIEW_QUEUE


@pytest.fixture()
def client():
    """Create a TestClient with the portal router mounted."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_mutable_state():
    """Reset in-memory state that mutates across tests (approve/reject)."""
    # Snapshot originals
    orig_approvals = [dict(a) for a in _PENDING_APPROVALS]
    orig_queue = [dict(q) for q in _REVIEW_QUEUE]
    yield
    # Restore
    _PENDING_APPROVALS.clear()
    _PENDING_APPROVALS.extend(orig_approvals)
    _REVIEW_QUEUE.clear()
    _REVIEW_QUEUE.extend(orig_queue)


# ── Procurement History ──────────────────────────────────────────────────────

class TestProcurementHistory:

    def test_returns_list(self, client):
        resp = client.get("/api/portal/procurement/history")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_history_item_has_required_fields(self, client):
        data = client.get("/api/portal/procurement/history").json()
        required = {"id", "description", "category", "amount_usd", "status", "vendor"}
        for item in data:
            assert required.issubset(item.keys()), f"Missing fields in {item['id']}"

    def test_contains_settled_and_blocked(self, client):
        data = client.get("/api/portal/procurement/history").json()
        statuses = {item["status"] for item in data}
        assert "SETTLED" in statuses
        assert "BLOCKED" in statuses


# ── Active Pipelines ─────────────────────────────────────────────────────────

class TestActivePipelines:

    def test_returns_list(self, client):
        resp = client.get("/api/portal/procurement/pipelines")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_pipeline_has_agent_stages(self, client):
        data = client.get("/api/portal/procurement/pipelines").json()
        for pipeline in data:
            assert "agents" in pipeline
            assert "request_id" in pipeline
            assert "current_stage" in pipeline


# ── Submit Procurement ───────────────────────────────────────────────────────

class TestSubmitProcurement:

    def test_submit_returns_request_id(self, client):
        resp = client.post(
            "/api/portal/procurement/submit",
            json={"message": "Buy 5 monitors", "user_id": "test-user"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUBMITTED"
        assert data["request_id"].startswith("REQ-")
        assert "mode" in data

    def test_submit_with_default_user(self, client):
        resp = client.post(
            "/api/portal/procurement/submit",
            json={"message": "Buy office supplies"},
        )
        assert resp.status_code == 200


# ── Finance: Pending Approvals ───────────────────────────────────────────────

class TestFinancePending:

    def test_returns_list(self, client):
        resp = client.get("/api/portal/finance/pending")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_all_items_pending(self, client):
        data = client.get("/api/portal/finance/pending").json()
        for item in data:
            assert item["status"] == "PENDING"

    def test_items_have_amount(self, client):
        data = client.get("/api/portal/finance/pending").json()
        for item in data:
            assert "amount_usd" in item
            assert item["amount_usd"] > 0


# ── Finance: Approve / Reject ────────────────────────────────────────────────

class TestFinanceApproveReject:

    def test_approve_item(self, client):
        resp = client.post("/api/portal/finance/approve/REQ-003")
        assert resp.status_code == 200
        assert resp.json()["status"] == "APPROVED"

    def test_reject_item(self, client):
        resp = client.post("/api/portal/finance/reject/REQ-007")
        assert resp.status_code == 200
        assert resp.json()["status"] == "REJECTED"

    def test_approve_nonexistent_returns_404(self, client):
        resp = client.post("/api/portal/finance/approve/REQ-NOPE")
        assert resp.status_code == 404

    def test_reject_nonexistent_returns_404(self, client):
        resp = client.post("/api/portal/finance/reject/REQ-NOPE")
        assert resp.status_code == 404


# ── Finance: History ─────────────────────────────────────────────────────────

class TestFinanceHistory:

    def test_returns_list(self, client):
        resp = client.get("/api/portal/finance/history")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_contains_approved_and_rejected(self, client):
        data = client.get("/api/portal/finance/history").json()
        statuses = {item["status"] for item in data}
        assert "APPROVED" in statuses
        assert "REJECTED" in statuses


# ── Compliance ───────────────────────────────────────────────────────────────

class TestComplianceEvents:

    def test_returns_list(self, client):
        resp = client.get("/api/portal/compliance/events")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    def test_event_has_compliance_hash(self, client):
        data = client.get("/api/portal/compliance/events").json()
        for evt in data:
            assert "compliance_hash" in evt
            assert len(evt["compliance_hash"]) >= 60

    def test_contains_multiple_event_types(self, client):
        data = client.get("/api/portal/compliance/events").json()
        types = {evt["event_type"] for evt in data}
        assert "AML_BLOCK" in types
        assert "KYC_PASS" in types


class TestBlockedVendors:

    def test_returns_list(self, client):
        resp = client.get("/api/portal/compliance/blocked")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_blocked_vendor_has_reason(self, client):
        data = client.get("/api/portal/compliance/blocked").json()
        for v in data:
            assert "reason" in v
            assert "vendor" in v

    def test_shadow_hardware_blocked(self, client):
        data = client.get("/api/portal/compliance/blocked").json()
        names = [v["vendor"] for v in data]
        assert "ShadowHardware" in names


class TestComplianceStats:

    def test_returns_stats(self, client):
        resp = client.get("/api/portal/compliance/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_checks" in data
        assert "approved" in data
        assert "blocked" in data
        assert "block_rate_pct" in data
        assert "approval_rate_pct" in data

    def test_stats_add_up(self, client):
        data = client.get("/api/portal/compliance/stats").json()
        assert data["approved"] + data["blocked"] + data["review"] <= data["total_checks"]

    def test_rates_are_percentages(self, client):
        data = client.get("/api/portal/compliance/stats").json()
        assert 0 <= data["block_rate_pct"] <= 100
        assert 0 <= data["approval_rate_pct"] <= 100


# ── IT Manager ───────────────────────────────────────────────────────────────

class TestITManagerVendors:

    def test_returns_vendor_catalog(self, client):
        resp = client.get("/api/portal/itmanager/vendors")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    def test_vendor_has_compliance_status(self, client):
        data = client.get("/api/portal/itmanager/vendors").json()
        for v in data:
            assert v["compliance_status"] in ("APPROVED", "REVIEW", "BLOCKED")


class TestITManagerContracts:

    def test_returns_ssa_contracts(self, client):
        resp = client.get("/api/portal/itmanager/contracts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    def test_contract_types_present(self, client):
        data = client.get("/api/portal/itmanager/contracts").json()
        types = {c["type"] for c in data}
        assert "SSA-L" in types  # Lisens
        assert "SSA-K" in types  # Kjøp

    def test_contract_has_dates(self, client):
        data = client.get("/api/portal/itmanager/contracts").json()
        for c in data:
            assert "start_date" in c
            assert "end_date" in c


# ── Admin ────────────────────────────────────────────────────────────────────

class TestAdminMetrics:

    def test_returns_metrics(self, client):
        resp = client.get("/api/portal/admin/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "agents" in data
        assert "last_updated" in data

    def test_agent_metrics_present(self, client):
        data = client.get("/api/portal/admin/metrics").json()
        expected_agents = {"Architect", "Governor", "Scout", "Sentinel", "Closer"}
        assert expected_agents == set(data["agents"].keys())

    def test_settled_less_than_total(self, client):
        data = client.get("/api/portal/admin/metrics").json()
        assert data["settled"] <= data["total_requests"]


class TestAdminPolicies:

    def test_returns_policy_list(self, client):
        resp = client.get("/api/portal/admin/policies")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    def test_policy_has_severity(self, client):
        data = client.get("/api/portal/admin/policies").json()
        for p in data:
            assert p["severity"] in ("BLOCK", "REVIEW", "WARN")

    def test_spending_cap_policy_exists(self, client):
        data = client.get("/api/portal/admin/policies").json()
        names = [p["name"] for p in data]
        assert "Spending Cap" in names


class TestAdminReviewQueue:

    def test_returns_queue(self, client):
        resp = client.get("/api/portal/admin/queue")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_resolve_approve(self, client):
        resp = client.post("/api/portal/admin/review-queue/resolve/REQ-003?action=approve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "APPROVED"

    def test_resolve_reject(self, client):
        resp = client.post("/api/portal/admin/review-queue/resolve/REQ-006?action=reject")
        assert resp.status_code == 200
        assert resp.json()["status"] == "REJECTED"

    def test_resolve_nonexistent_returns_404(self, client):
        resp = client.post("/api/portal/admin/review-queue/resolve/REQ-NOPE")
        assert resp.status_code == 404


# ── Overview ─────────────────────────────────────────────────────────────────

class TestOverview:

    def test_returns_overview(self, client):
        resp = client.get("/api/portal/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "settlement_rate_pct" in data
        assert "agents" in data
        assert "recent" in data

    def test_settlement_rate_is_percentage(self, client):
        data = client.get("/api/portal/overview").json()
        assert 0 <= data["settlement_rate_pct"] <= 100

    def test_agents_have_roles(self, client):
        data = client.get("/api/portal/overview").json()
        for name, info in data["agents"].items():
            assert "role" in info
            assert "status" in info
            assert "avg_ms" in info

    def test_recent_is_list(self, client):
        data = client.get("/api/portal/overview").json()
        assert isinstance(data["recent"], list)
        assert len(data["recent"]) <= 5


# ── Capabilities ─────────────────────────────────────────────────────────────

class TestCapabilities:

    def test_returns_capabilities(self, client):
        resp = client.get("/api/portal/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert "gemini_available" in data
        assert isinstance(data["gemini_available"], bool)


# ── Demo Pipeline SSE ────────────────────────────────────────────────────────

class TestDemoPipelineSSE:

    @staticmethod
    def _parse_sse(resp) -> list[dict]:
        events = []
        for chunk in resp.text.split("\n"):
            chunk = chunk.strip()
            if chunk.startswith("data: "):
                try:
                    events.append(json.loads(chunk[6:]))
                except json.JSONDecodeError:
                    pass
        return events

    def test_streams_sse_events(self, client):
        """Run the demo pipeline and verify SSE agent progression events."""
        resp = client.post(
            "/api/portal/run/demo",
            json={"message": "Buy 3 Laptop Pro 15 from best vendor"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

        events = self._parse_sse(resp)
        assert len(events) >= 5, f"Expected >=5 SSE events, got {len(events)}"

        agent_events = [e for e in events if e.get("type") == "agent"]
        assert len(agent_events) >= 5  # Architect, Governor, Scout, Sentinel, Closer stages

        # Verify pipeline progresses through expected agents
        agent_names = [e["name"] for e in agent_events]
        for expected in ["Architect", "Governor", "Scout", "Sentinel"]:
            assert expected in agent_names, f"Missing agent: {expected}"

    def test_happy_path_with_mocked_vendors(self, client, monkeypatch):
        """With ShadowHardware removed from discovery, pipeline should settle."""
        clean_vendors = [
            {"id": "v-001", "name": "TechCorp Nordic", "capability": "dev.ucp.shopping",
             "product": "Laptop Pro 15", "unit_price_usd": 1299.0, "available_units": 50,
             "ucp_endpoint": "https://techcorp-nordic.example/.well-known/ucp", "country": "NO",
             "pricing_tiers": [], "org_number": "914778271"},
        ]
        monkeypatch.setattr("tools.ucp_tools.discover_vendors", lambda q: clean_vendors)

        resp = client.post(
            "/api/portal/run/demo",
            json={"message": "Buy 3 Laptop Pro 15"},
        )
        assert resp.status_code == 200

        events = self._parse_sse(resp)
        result_events = [e for e in events if e.get("type") == "result"]
        assert len(result_events) == 1
        result = result_events[0]
        assert result["settlement"]["status"] == "SETTLED"

    def test_blocked_path_streams_blocked_event(self, client):
        resp = client.post(
            "/api/portal/run/demo",
            json={"message": "Buy laptops from ShadowHardware"},
        )
        assert resp.status_code == 200

        events = self._parse_sse(resp)

        blocked_events = [e for e in events if e.get("type") == "blocked"]
        assert len(blocked_events) == 1
        assert blocked_events[0]["vendor"] == "ShadowHardware"

        # Sentinel should be blocked
        sentinel = [e for e in events if e.get("type") == "agent" and e.get("name") == "Sentinel" and e.get("status") == "blocked"]
        assert len(sentinel) == 1


# ── Dashboard helpers (unit-level) ───────────────────────────────────────────

class TestDashboardConstants:
    """Verify dashboard module-level constants used by the Streamlit UI."""

    def test_agents_list(self):
        from ui.dashboard import AGENTS, AGENT_ICONS, AGENT_DESC
        assert AGENTS == ["Architect", "Scout", "Sentinel", "Closer"]
        for a in AGENTS:
            assert a in AGENT_ICONS
            assert a in AGENT_DESC
