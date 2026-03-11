"""Tests for observability middleware and metrics endpoint."""

from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

import main


class _DummySessionService:
    async def get_session(self, app_name: str, user_id: str, session_id: str):
        return None

    async def create_session(self, app_name: str, user_id: str, session_id: str):
        return {"app_name": app_name, "user_id": user_id, "session_id": session_id}


class _DummyRunner:
    async def run_async(self, user_id: str, session_id: str, new_message):
        event = SimpleNamespace(content=SimpleNamespace(parts=[SimpleNamespace(text="ok")]))
        yield event


def test_correlation_id_is_propagated_when_provided(monkeypatch):
    monkeypatch.setattr(main, "_session_service", _DummySessionService())
    monkeypatch.setattr(main, "_runner", _DummyRunner())
    monkeypatch.setenv("AUTH_ENABLED", "false")

    client = TestClient(main.app)
    response = client.post(
        "/run",
        json={"message": "Buy 2 laptops"},
        headers={"X-Correlation-ID": "corr-123"},
    )

    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "corr-123"


def test_correlation_id_is_generated_when_missing(monkeypatch):
    monkeypatch.setattr(main, "_session_service", _DummySessionService())
    monkeypatch.setattr(main, "_runner", _DummyRunner())
    monkeypatch.setenv("AUTH_ENABLED", "false")

    client = TestClient(main.app)
    response = client.get("/health")

    assert response.status_code == 200
    correlation_id = response.headers.get("X-Correlation-ID")
    assert correlation_id is not None
    assert len(correlation_id) > 10


def test_metrics_endpoint_returns_request_counters(monkeypatch):
    monkeypatch.setattr(main, "_session_service", _DummySessionService())
    monkeypatch.setattr(main, "_runner", _DummyRunner())
    monkeypatch.setenv("AUTH_ENABLED", "false")

    client = TestClient(main.app)
    client.get("/health")
    client.get("/health")

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200

    body = metrics_response.json()
    assert "request_total" in body
    assert "/health" in body["request_total"]
    assert body["request_total"]["/health"] >= 2
