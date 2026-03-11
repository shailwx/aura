"""Tests for session backend selection and configuration guards."""

from __future__ import annotations

import pytest
from google.adk.sessions import InMemorySessionService

from tools.session_tools import RedisSessionService, build_session_service


def test_default_session_backend_is_inmemory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("SESSION_BACKEND", raising=False)
    service = build_session_service()
    assert isinstance(service, InMemorySessionService)


def test_redis_backend_requires_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SESSION_BACKEND", "redis")
    monkeypatch.delenv("REDIS_URL", raising=False)

    with pytest.raises(RuntimeError, match="REDIS_URL"):
        build_session_service()


def test_redis_backend_builds_with_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SESSION_BACKEND", "redis")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("REDIS_SESSION_KEY_PREFIX", "aura:test")
    monkeypatch.setenv("SESSION_TTL_SECONDS", "60")

    service = build_session_service()
    assert isinstance(service, RedisSessionService)


def test_unknown_session_backend_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SESSION_BACKEND", "unsupported")

    with pytest.raises(RuntimeError, match="Unsupported SESSION_BACKEND"):
        build_session_service()
