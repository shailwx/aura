"""Reliability primitives: retry policy and in-process circuit breaker."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    """Raised when a circuit breaker is open and call execution is blocked."""


@dataclass
class CircuitBreaker:
    """Simple in-process circuit breaker with time-based reset."""

    failure_threshold: int = 3
    reset_timeout_seconds: float = 30.0
    failure_count: int = 0
    opened_at: float | None = None

    def before_call(self) -> None:
        if self.opened_at is None:
            return
        now = time.time()
        if now - self.opened_at >= self.reset_timeout_seconds:
            self.failure_count = 0
            self.opened_at = None
            return
        raise CircuitOpenError("Circuit is open. Skipping downstream call.")

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = time.time()


def execute_with_retries(
    operation: Callable[[], T],
    *,
    attempts: int,
    base_backoff_seconds: float,
    circuit_breaker: CircuitBreaker,
    retryable_exceptions: tuple[type[Exception], ...],
) -> T:
    """Execute callable with retry + backoff + circuit breaker semantics."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        circuit_breaker.before_call()
        try:
            result = operation()
            circuit_breaker.record_success()
            return result
        except retryable_exceptions as exc:
            last_error = exc
            circuit_breaker.record_failure()
            if attempt >= attempts:
                break

            sleep_seconds = base_backoff_seconds * (2 ** (attempt - 1))
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    assert last_error is not None
    raise last_error
