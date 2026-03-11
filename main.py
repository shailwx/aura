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
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agents.architect import architect
from tools.intent_tools import (
    build_clarification_message,
    build_structured_procurement_prompt,
    parse_procurement_intent,
)

load_dotenv()

# ── ADK wiring ────────────────────────────────────────────────────────────────

APP_NAME = os.getenv("APP_NAME", "aura")
_session_service = InMemorySessionService()

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
async def run_procurement(request: RunRequest) -> RunResponse:
    """Submit a natural language procurement request to the Aura agent pipeline."""
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id

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
async def run_procurement_stream(request: RunRequest) -> StreamingResponse:
    """Stream the agent response token by token (SSE-compatible)."""
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id

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
