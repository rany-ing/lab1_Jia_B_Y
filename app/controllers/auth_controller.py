from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi_sso.sso.base import OpenID

from app.auth.dependencies import CurrentUser, Db
from app.auth.github import CALLBACK_PATH, GitHubLogin, github_identity, github_redirect, github_sso
from app.auth.passwords import verify_password
from app.auth.tokens import signing_key, unauthorized
from app.schemas.auth import Login, RefreshToken, Register, SessionRead, TokenPair
from app.schemas.user import UserRead
from app.services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["Auth"])
GitHub = Annotated[GitHubLogin, Depends(github_sso)]


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: Register, db: Db):
    return user_service.create_user(db, payload)


@router.post("/login", response_model=TokenPair)
def login(payload: Login, request: Request, response: Response, db: Db):
    user = user_service.find_by_email(db, payload.email)
    password_hash = user.password_hash if user else None
    if not verify_password(payload.password.get_secret_value(), password_hash) or user is None:
        raise unauthorized()
    response.headers["Cache-Control"] = "no-store"
    return auth_service.start_session(db, user.id, request.headers.get("User-Agent"))


@router.get("/github/login")
async def github_login(sso: GitHub):
    signing_key()
    return await github_redirect(sso)


@router.get("/github/callback", response_model=TokenPair)
def github_callback(
    request: Request,
    response: Response,
    db: Db,
    identity: Annotated[OpenID, Depends(github_identity)],
):
    signing_key()
    user = user_service.get_or_create_github_user(db, identity)
    tokens = auth_service.start_session(db, user.id, request.headers.get("User-Agent"))
    response.headers["Cache-Control"] = "no-store"
    response.delete_cookie("sso_state", path=CALLBACK_PATH)
    response.delete_cookie("pkce_code_verifier", path=CALLBACK_PATH)
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshToken, response: Response, db: Db):
    response.headers["Cache-Control"] = "no-store"
    return auth_service.refresh(db, payload.refresh_token.get_secret_value())


@router.post("/logout", status_code=204)
def logout(payload: RefreshToken, db: Db):
    auth_service.logout(db, payload.refresh_token.get_secret_value())
    return Response(status_code=204)


@router.get("/sessions", response_model=list[SessionRead])
def sessions(user: CurrentUser, db: Db):
    return auth_service.list_sessions(db, user.id)
