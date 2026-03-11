"""
Aura — FastAPI entry point and ADK Runner.

Exposes:
  POST /run      — submit a procurement request, get streamed response
  GET  /health   — liveness probe for Kubernetes

Also exports `root_agent` at module level for `adk web` dev UI auto-discovery.
"""

from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import AsyncIterator
import logging

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from google.adk.runners import Runner
from google.genai import types as genai_types

from agents.architect import architect
from tools.intent_tools import (
    build_clarification_message,
    build_structured_procurement_prompt,
    parse_procurement_intent,
)
from tools.auth_tools import AuthIdentity, require_procurement_identity
from tools.session_tools import build_session_service
from tools.policy_store import PolicyRule, PolicyStore, ReviewStore, RuleType, Severity

load_dotenv()

logger = logging.getLogger(__name__)

# ── ADK wiring ────────────────────────────────────────────────────────────────

APP_NAME = os.getenv("APP_NAME", "aura")
_session_service = build_session_service()

_runner = Runner(
    app_name=APP_NAME,
    agent=architect,
    session_service=_session_service,
)

# Expose root_agent for `adk web` dev UI
root_agent = architect


# ── FastAPI app ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await _runner.close()


app = FastAPI(
    title="Aura — Autonomous Reliable Agentic Commerce",
    description="Multi-agent B2B procurement system powered by Google ADK and Gemini 2.0 Flash.",
    version="2026.1.0",
    lifespan=lifespan,
)


class RunRequest(BaseModel):
    message: str
    user_id: str = "default-user"
    session_id: str | None = None


class RunResponse(BaseModel):
    session_id: str
    response: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME}


@app.post("/run", response_model=RunResponse)
async def run_procurement(
    request: RunRequest,
    identity: AuthIdentity = Depends(require_procurement_identity),
) -> RunResponse:
    """Submit a natural language procurement request to the Aura agent pipeline."""
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id if request.user_id != "default-user" else identity.subject

    logger.info(
        "procurement_run_request",
        extra={"caller": identity.subject, "role": identity.role, "session_id": session_id},
    )

    # Ensure session exists
    existing = await _session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if existing is None:
        await _session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    parsed_intent = parse_procurement_intent(request.message)
    if not parsed_intent.is_valid:
        return RunResponse(
            session_id=session_id,
            response=build_clarification_message(parsed_intent.missing_fields),
        )

    normalized_prompt = build_structured_procurement_prompt(parsed_intent.intent)
    normalized_prompt = f"{normalized_prompt}\nCALLER_ROLE: {identity.role}\nCALLER_SUBJECT: {identity.subject}"

    new_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=normalized_prompt)],
    )

    # Collect all agent response chunks
    response_parts: list[str] = []
    async for event in _runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_parts.append(part.text)

    if not response_parts:
        raise HTTPException(status_code=500, detail="Agent produced no response.")

    return RunResponse(
        session_id=session_id,
        response="\n".join(response_parts),
    )


@app.post("/run/stream")
async def run_procurement_stream(
    request: RunRequest,
    identity: AuthIdentity = Depends(require_procurement_identity),
) -> StreamingResponse:
    """Stream the agent response token by token (SSE-compatible)."""
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id if request.user_id != "default-user" else identity.subject

    logger.info(
        "procurement_stream_request",
        extra={"caller": identity.subject, "role": identity.role, "session_id": session_id},
    )

    existing = await _session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if existing is None:
        await _session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    parsed_intent = parse_procurement_intent(request.message)
    if not parsed_intent.is_valid:
        clarification = build_clarification_message(parsed_intent.missing_fields)

        async def clarification_generator() -> AsyncIterator[str]:
            yield f"data: {clarification}\n\n"

        return StreamingResponse(
            clarification_generator(),
            media_type="text/event-stream",
        )

    normalized_prompt = build_structured_procurement_prompt(parsed_intent.intent)
    normalized_prompt = f"{normalized_prompt}\nCALLER_ROLE: {identity.role}\nCALLER_SUBJECT: {identity.subject}"

    new_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=normalized_prompt)],
    )

    async def event_generator() -> AsyncIterator[str]:
        async for event in _runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        yield f"data: {part.text}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Policy API — admin auth ───────────────────────────────────────────────────

_api_key_header = APIKeyHeader(name="X-Admin-Token", auto_error=False)


def _require_admin_token(token: str | None = Security(_api_key_header)) -> str:
    expected = os.getenv("AURA_ADMIN_TOKEN", "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin token not configured on this server.",
        )
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-Admin-Token header.",
        )
    return token


# ── Policy API — Pydantic models ──────────────────────────────────────────────


class PolicyRuleCreate(BaseModel):
    id: str
    name: str
    rule_type: str
    enabled: bool = True
    severity: str
    parameters: dict
    description: str = ""


class PolicyRuleUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    severity: str | None = None
    parameters: dict | None = None
    description: str | None = None


class PolicyRuleResponse(BaseModel):
    id: str
    name: str
    rule_type: str
    enabled: bool
    severity: str
    parameters: dict
    description: str
    created_at: float


class ReviewResolution(BaseModel):
    note: str = ""


# ── Policy CRUD endpoints ─────────────────────────────────────────────────────


@app.get("/policies", response_model=list[PolicyRuleResponse])
async def list_policies() -> list[PolicyRuleResponse]:
    """List all active policy rules."""
    return [PolicyRuleResponse(**r.to_dict()) for r in PolicyStore.get_instance().get_all_rules()]


@app.post("/policies", response_model=PolicyRuleResponse, status_code=201)
async def create_policy(
    body: PolicyRuleCreate,
    _: str = Depends(_require_admin_token),
) -> PolicyRuleResponse:
    """Create a new policy rule (admin only)."""
    try:
        rule = PolicyRule(
            id=body.id,
            name=body.name,
            rule_type=RuleType(body.rule_type),
            enabled=body.enabled,
            severity=Severity(body.severity),
            parameters=body.parameters,
            description=body.description,
            created_at=time.time(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    PolicyStore.get_instance().add_rule(rule)
    return PolicyRuleResponse(**rule.to_dict())


@app.get("/policies/{rule_id}", response_model=PolicyRuleResponse)
async def get_policy(rule_id: str) -> PolicyRuleResponse:
    """Get a single policy rule by ID."""
    rule = PolicyStore.get_instance().get_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Policy rule '{rule_id}' not found.")
    return PolicyRuleResponse(**rule.to_dict())


@app.put("/policies/{rule_id}", response_model=PolicyRuleResponse)
async def update_policy(
    rule_id: str,
    body: PolicyRuleUpdate,
    _: str = Depends(_require_admin_token),
) -> PolicyRuleResponse:
    """Partially update a policy rule (admin only)."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    rule = PolicyStore.get_instance().update_rule(rule_id, updates)
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Policy rule '{rule_id}' not found.")
    return PolicyRuleResponse(**rule.to_dict())


@app.delete("/policies/{rule_id}", status_code=204)
async def delete_policy(
    rule_id: str,
    _: str = Depends(_require_admin_token),
) -> None:
    """Delete a policy rule (admin only)."""
    if not PolicyStore.get_instance().delete_rule(rule_id):
        raise HTTPException(status_code=404, detail=f"Policy rule '{rule_id}' not found.")


# ── Review queue endpoints ────────────────────────────────────────────────────


@app.get("/reviews")
async def list_reviews() -> list[dict]:
    """List pending review items."""
    return [asdict(item) for item in ReviewStore.get_instance().get_pending()]


@app.post("/reviews/{review_id}/approve")
async def approve_review(
    review_id: str,
    body: ReviewResolution,
    _: str = Depends(_require_admin_token),
) -> dict:
    """Approve a queued payment review (admin only)."""
    item = ReviewStore.get_instance().resolve(review_id, approved=True, note=body.note)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Review '{review_id}' not found.")
    return asdict(item)


@app.post("/reviews/{review_id}/reject")
async def reject_review(
    review_id: str,
    body: ReviewResolution,
    _: str = Depends(_require_admin_token),
) -> dict:
    """Reject a queued payment review (admin only)."""
    item = ReviewStore.get_instance().resolve(review_id, approved=False, note=body.note)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Review '{review_id}' not found.")
    return asdict(item)
