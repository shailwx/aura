"""Authentication and authorization tests for procurement API endpoints."""

from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient
from jose import jwt

import main


class _DummySessionService:
    async def get_session(self, app_name: str, user_id: str, session_id: str):
        return None

    async def create_session(self, app_name: str, user_id: str, session_id: str):
        return {"app_name": app_name, "user_id": user_id, "session_id": session_id}


class _DummyRunner:
    async def run_async(self, user_id: str, session_id: str, new_message):
        event = SimpleNamespace(
            content=SimpleNamespace(parts=[SimpleNamespace(text="ok")])
        )
        yield event


def _token(secret: str, role: str, sub: str = "alice") -> str:
    return jwt.encode({"sub": sub, "role": role}, secret, algorithm="HS256")


def test_run_requires_auth_when_enabled(monkeypatch):
    monkeypatch.setattr(main, "_session_service", _DummySessionService())
    monkeypatch.setattr(main, "_runner", _DummyRunner())
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_JWT_SECRET", "test-secret")
    monkeypatch.setenv("AUTH_ALLOWED_ROLES", "procurement_runner,admin")

    client = TestClient(main.app)
    response = client.post("/run", json={"message": "Buy 2 laptops"})

    assert response.status_code == 401


def test_run_rejects_forbidden_role(monkeypatch):
    monkeypatch.setattr(main, "_session_service", _DummySessionService())
    monkeypatch.setattr(main, "_runner", _DummyRunner())
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_JWT_SECRET", "test-secret")
    monkeypatch.setenv("AUTH_ALLOWED_ROLES", "procurement_runner,admin")

    token = _token(secret="test-secret", role="viewer")
    client = TestClient(main.app)
    response = client.post(
        "/run",
        json={"message": "Buy 2 laptops"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_run_allows_authorized_role(monkeypatch):
    monkeypatch.setattr(main, "_session_service", _DummySessionService())
    monkeypatch.setattr(main, "_runner", _DummyRunner())
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_JWT_SECRET", "test-secret")
    monkeypatch.setenv("AUTH_ALLOWED_ROLES", "procurement_runner,admin")

    token = _token(secret="test-secret", role="procurement_runner")
    client = TestClient(main.app)
    response = client.post(
        "/run",
        json={"message": "Buy 2 laptops"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "session_id" in body
    assert body["response"] == "ok"


def test_stream_requires_auth_when_enabled(monkeypatch):
    monkeypatch.setattr(main, "_session_service", _DummySessionService())
    monkeypatch.setattr(main, "_runner", _DummyRunner())
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_JWT_SECRET", "test-secret")

    client = TestClient(main.app)
    response = client.post("/run/stream", json={"message": "Buy 2 laptops"})

    assert response.status_code == 401


def test_stream_allows_authorized_role(monkeypatch):
    monkeypatch.setattr(main, "_session_service", _DummySessionService())
    monkeypatch.setattr(main, "_runner", _DummyRunner())
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_JWT_SECRET", "test-secret")
    monkeypatch.setenv("AUTH_ALLOWED_ROLES", "procurement_runner,admin")

    token = _token(secret="test-secret", role="admin")
    client = TestClient(main.app)

    with client.stream(
        "POST",
        "/run/stream",
        json={"message": "Buy 2 laptops"},
        headers={"Authorization": f"Bearer {token}"},
    ) as response:
        payload = "".join(chunk.decode("utf-8") for chunk in response.iter_raw())

    assert response.status_code == 200
    assert "data: ok" in payload
