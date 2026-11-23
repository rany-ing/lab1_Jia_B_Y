from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Literal
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException

from app.config import settings

TokenKind = Literal["access", "refresh"]
ISSUER = "news-api"


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    session_id: UUID


def unauthorized() -> HTTPException:
    return HTTPException(401, "Invalid or expired credentials", headers={"WWW-Authenticate": "Bearer"})


def signing_key() -> str:
    key = settings.jwt_secret.get_secret_value()
    if len(key.encode()) < 32:
        raise HTTPException(503, "JWT signing is not configured")
    return key


def issue_token(user_id: int, session_id: UUID, kind: TokenKind, now: datetime, expires_at: datetime) -> str:
    claims = {
        "iss": ISSUER,
        "sub": str(user_id),
        "sid": str(session_id),
        "kind": kind,
        "iat": now,
        "exp": expires_at,
        "jti": str(uuid4()),
    }
    return jwt.encode(claims, signing_key(), algorithm="HS256")


def read_token(token: str, kind: TokenKind) -> TokenClaims:
    try:
        claims = jwt.decode(
            token,
            signing_key(),
            algorithms=["HS256"],
            issuer=ISSUER,
            options={"require": ["iss", "sub", "sid", "kind", "iat", "exp", "jti"]},
        )
        if claims["kind"] != kind:
            raise unauthorized()
        return TokenClaims(int(claims["sub"]), UUID(claims["sid"]))
    except (jwt.InvalidTokenError, ValueError, TypeError, AttributeError) as exc:
        raise unauthorized() from exc


def token_hash(token: str) -> str:
    return sha256(token.encode()).hexdigest()
