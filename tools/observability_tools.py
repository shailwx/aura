"""Observability utilities: correlation IDs, structured logs, and metrics."""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from fastapi import Request


CORRELATION_HEADER = "X-Correlation-ID"


@dataclass
class InMemoryMetrics:
    """Simple in-memory metrics registry for API observability."""

    started_at: float = field(default_factory=time.time)
    request_total: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    request_errors: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    request_duration_ms_sum: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    request_duration_ms_count: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record_request(self, path: str, status_code: int, duration_ms: float) -> None:
        key = path or "unknown"
        with self._lock:
            self.request_total[key] += 1
            self.request_duration_ms_sum[key] += duration_ms
            self.request_duration_ms_count[key] += 1
            if status_code >= 400:
                self.request_errors[key] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg_duration_ms: dict[str, float] = {}
            for path, total_duration in self.request_duration_ms_sum.items():
                count = self.request_duration_ms_count[path]
                avg_duration_ms[path] = round(total_duration / count, 3) if count else 0.0

            return {
                "uptime_seconds": round(time.time() - self.started_at, 3),
                "request_total": dict(self.request_total),
                "request_errors": dict(self.request_errors),
                "request_avg_duration_ms": avg_duration_ms,
            }


METRICS = InMemoryMetrics()


def get_correlation_id(request: Request) -> str:
    correlation_id = getattr(request.state, "correlation_id", None)
    if correlation_id:
        return correlation_id
    return request.headers.get(CORRELATION_HEADER, str(uuid.uuid4()))


def log_event(event: str, **fields: Any) -> str:
    payload = {"event": event, **fields, "timestamp": round(time.time(), 3)}
    return json.dumps(payload, sort_keys=True, default=str)
