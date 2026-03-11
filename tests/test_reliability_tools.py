"""Tests for retry and circuit breaker behavior."""

from __future__ import annotations

import pytest

from tools.reliability_tools import CircuitBreaker, CircuitOpenError, execute_with_retries


def test_execute_with_retries_eventually_succeeds(monkeypatch: pytest.MonkeyPatch):
    attempts: dict[str, int] = {"count": 0}

    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("transient")
        return "ok"

    monkeypatch.setattr("tools.reliability_tools.time.sleep", lambda _: None)

    result = execute_with_retries(
        flaky,
        attempts=3,
        base_backoff_seconds=0.01,
        circuit_breaker=CircuitBreaker(failure_threshold=10, reset_timeout_seconds=1),
        retryable_exceptions=(ValueError,),
    )

    assert result == "ok"
    assert attempts["count"] == 3


def test_execute_with_retries_raises_after_max_attempts(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("tools.reliability_tools.time.sleep", lambda _: None)

    with pytest.raises(ValueError, match="boom"):
        execute_with_retries(
            lambda: (_ for _ in ()).throw(ValueError("boom")),
            attempts=2,
            base_backoff_seconds=0.01,
            circuit_breaker=CircuitBreaker(failure_threshold=10, reset_timeout_seconds=1),
            retryable_exceptions=(ValueError,),
        )


def test_circuit_breaker_opens_after_threshold():
    breaker = CircuitBreaker(failure_threshold=2, reset_timeout_seconds=10)
    breaker.record_failure()
    breaker.record_failure()

    with pytest.raises(CircuitOpenError):
        breaker.before_call()
