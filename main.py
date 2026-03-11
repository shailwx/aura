"""
Aura — FastAPI entry point and ADK Runner.

Exposes:
  POST /run      — submit a procurement request, get streamed response
  GET  /health   — liveness probe for Kubernetes

Also exports `root_agent` at module level for `adk web` dev UI auto-discovery.
"""

from __future__ import annotations

import os
import uuid
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator
import logging

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
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
from tools.observability_tools import CORRELATION_HEADER, METRICS, get_correlation_id, log_event
from tools.session_tools import build_session_service

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


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    started_at = time.perf_counter()
    correlation_id = request.headers.get(CORRELATION_HEADER, str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        duration_ms = (time.perf_counter() - started_at) * 1000
        METRICS.record_request(request.url.path, 500, duration_ms)
        logger.exception(
            log_event(
                "http_request_failed",
                path=request.url.path,
                method=request.method,
                correlation_id=correlation_id,
                duration_ms=round(duration_ms, 3),
            )
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000
    METRICS.record_request(request.url.path, status_code, duration_ms)
    response.headers[CORRELATION_HEADER] = correlation_id
    logger.info(
        log_event(
            "http_request",
            path=request.url.path,
            method=request.method,
            status_code=status_code,
            correlation_id=correlation_id,
            duration_ms=round(duration_ms, 3),
        )
    )
    return response


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


@app.get("/metrics")
async def metrics() -> JSONResponse:
    return JSONResponse(METRICS.snapshot())


@app.post("/run", response_model=RunResponse)
async def run_procurement(
    http_request: Request,
    request: RunRequest,
    identity: AuthIdentity = Depends(require_procurement_identity),
) -> RunResponse:
    """Submit a natural language procurement request to the Aura agent pipeline."""
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id if request.user_id != "default-user" else identity.subject

    correlation_id = get_correlation_id(http_request)
    logger.info(
        log_event(
            "procurement_run_request",
            caller=identity.subject,
            role=identity.role,
            session_id=session_id,
            correlation_id=correlation_id,
        )
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
    normalized_prompt = (
        f"{normalized_prompt}\nCALLER_ROLE: {identity.role}\nCALLER_SUBJECT: {identity.subject}"
        f"\nCORRELATION_ID: {correlation_id}"
    )

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
    http_request: Request,
    request: RunRequest,
    identity: AuthIdentity = Depends(require_procurement_identity),
) -> StreamingResponse:
    """Stream the agent response token by token (SSE-compatible)."""
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id if request.user_id != "default-user" else identity.subject

    correlation_id = get_correlation_id(http_request)
    logger.info(
        log_event(
            "procurement_stream_request",
            caller=identity.subject,
            role=identity.role,
            session_id=session_id,
            correlation_id=correlation_id,
        )
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
    normalized_prompt = (
        f"{normalized_prompt}\nCALLER_ROLE: {identity.role}\nCALLER_SUBJECT: {identity.subject}"
        f"\nCORRELATION_ID: {correlation_id}"
    )

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
