"""Authentication helpers for Aura API endpoints."""

from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt


@dataclass
class AuthIdentity:
    subject: str
    role: str
    token_claims: dict


def _is_auth_enabled() -> bool:
    return os.getenv("AUTH_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _parse_bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not header.startswith(prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = header[len(prefix):].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def _decode_identity(token: str) -> AuthIdentity:
    secret = os.getenv("AUTH_JWT_SECRET", "").strip()
    algorithm = os.getenv("AUTH_JWT_ALGORITHM", "HS256").strip() or "HS256"
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AUTH_ENABLED requires AUTH_JWT_SECRET.",
        )

    try:
        claims = jwt.decode(token, secret, algorithms=[algorithm], options={"verify_aud": False})
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = str(claims.get("sub", "")).strip() or "unknown-user"

    role_claim = claims.get("role")
    if role_claim is None and isinstance(claims.get("roles"), list) and claims["roles"]:
        role_claim = claims["roles"][0]
    role = str(role_claim or "").strip()

    return AuthIdentity(subject=subject, role=role, token_claims=claims)


def require_procurement_identity(request: Request) -> AuthIdentity:
    """Return caller identity, enforcing JWT auth when AUTH_ENABLED=true."""
    if not _is_auth_enabled():
        return AuthIdentity(subject="anonymous", role="anonymous", token_claims={})

    token = _parse_bearer_token(request)
    identity = _decode_identity(token)

    allowed_roles_raw = os.getenv("AUTH_ALLOWED_ROLES", "procurement_runner,admin")
    allowed_roles = {item.strip() for item in allowed_roles_raw.split(",") if item.strip()}
    if identity.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Caller role '{identity.role or '<missing>'}' is not allowed.",
        )

    return identity
