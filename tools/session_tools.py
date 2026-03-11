"""Session backend selection and durable Redis session service."""

from __future__ import annotations

import copy
import os
import time
import uuid
from typing import Optional

from google.adk.events import Event
from google.adk.sessions import BaseSessionService, InMemorySessionService, Session
from google.adk.sessions.base_session_service import GetSessionConfig, ListSessionsResponse

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover - optional import for redis backend
    redis = None


class RedisSessionService(BaseSessionService):
    """Redis-backed session service for cross-process persistence."""

    def __init__(self, redis_url: str, key_prefix: str = "aura:sessions", ttl_seconds: int = 0):
        if redis is None:
            raise RuntimeError("redis package is required for SESSION_BACKEND=redis")
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds

    def _session_key(self, app_name: str, user_id: str, session_id: str) -> str:
        return f"{self._key_prefix}:{app_name}:{user_id}:{session_id}"

    def _session_pattern(self, app_name: str, user_id: Optional[str] = None) -> str:
        if user_id is None:
            return f"{self._key_prefix}:{app_name}:*:*"
        return f"{self._key_prefix}:{app_name}:{user_id}:*"

    async def _persist_session(self, session: Session) -> None:
        key = self._session_key(session.app_name, session.user_id, session.id)
        await self._redis.set(key, session.model_dump_json())
        if self._ttl_seconds > 0:
            await self._redis.expire(key, self._ttl_seconds)

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, object]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        resolved_session_id = session_id.strip() if session_id and session_id.strip() else str(uuid.uuid4())
        existing = await self.get_session(app_name=app_name, user_id=user_id, session_id=resolved_session_id)
        if existing is not None:
            raise ValueError(f"Session with id {resolved_session_id} already exists.")

        session = Session(
            app_name=app_name,
            user_id=user_id,
            id=resolved_session_id,
            state=state or {},
            last_update_time=time.time(),
        )
        await self._persist_session(session)
        return copy.deepcopy(session)

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        key = self._session_key(app_name, user_id, session_id)
        raw = await self._redis.get(key)
        if raw is None:
            return None

        session = Session.model_validate_json(raw)
        copied_session = copy.deepcopy(session)

        if config:
            if config.num_recent_events:
                copied_session.events = copied_session.events[-config.num_recent_events :]
            if config.after_timestamp:
                copied_session.events = [
                    event for event in copied_session.events if event.timestamp >= config.after_timestamp
                ]

        return copied_session

    async def list_sessions(
        self, *, app_name: str, user_id: Optional[str] = None
    ) -> ListSessionsResponse:
        sessions: list[Session] = []
        async for key in self._redis.scan_iter(match=self._session_pattern(app_name, user_id)):
            raw = await self._redis.get(key)
            if raw is None:
                continue
            session = Session.model_validate_json(raw)
            copied = copy.deepcopy(session)
            copied.events = []
            sessions.append(copied)

        return ListSessionsResponse(sessions=sessions)

    async def delete_session(self, *, app_name: str, user_id: str, session_id: str) -> None:
        key = self._session_key(app_name, user_id, session_id)
        await self._redis.delete(key)

    async def append_event(self, session: Session, event: Event) -> Event:
        if event.partial:
            return event

        await super().append_event(session=session, event=event)
        session.last_update_time = event.timestamp
        await self._persist_session(session)
        return event


def build_session_service() -> BaseSessionService:
    """Create session service based on SESSION_BACKEND environment setting."""
    backend = os.getenv("SESSION_BACKEND", "inmemory").strip().lower()
    if backend == "inmemory":
        return InMemorySessionService()

    if backend == "redis":
        redis_url = os.getenv("REDIS_URL", "").strip()
        if not redis_url:
            raise RuntimeError("SESSION_BACKEND=redis requires REDIS_URL to be set.")

        key_prefix = os.getenv("REDIS_SESSION_KEY_PREFIX", "aura:sessions").strip() or "aura:sessions"
        ttl_seconds = int(os.getenv("SESSION_TTL_SECONDS", "0").strip() or "0")
        return RedisSessionService(
            redis_url=redis_url,
            key_prefix=key_prefix,
            ttl_seconds=ttl_seconds,
        )

    raise RuntimeError(
        f"Unsupported SESSION_BACKEND='{backend}'. Expected 'inmemory' or 'redis'."
    )
