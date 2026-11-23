from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from fastapi_sso.sso.base import OpenID, SSOLoginError
from fastapi_sso.sso.github import GithubSSO
from httpx import AsyncClient, HTTPError
from oauthlib.oauth2 import OAuth2Error
from pydantic import EmailStr, TypeAdapter, ValidationError

from app.config import settings

CALLBACK_PATH = "/auth/github/callback"
COOKIE_MAX_AGE = 600


class GitHubLogin(GithubSSO):
    uses_pkce = True

    async def openid_from_response(self, response: dict, session: AsyncClient | None = None) -> OpenID:
        email = None
        if session is not None:
            emails = await session.get(self.emails_endpoint)
            emails.raise_for_status()
            for entry in emails.json():
                if entry["primary"] and entry["verified"]:
                    email = entry["email"]
                    break
        return OpenID(
            provider=self.provider,
            id=str(response["id"]),
            email=email,
            display_name=response["login"],
            picture=response.get("avatar_url"),
        )


def github_sso() -> GitHubLogin:
    secret = settings.github_client_secret.get_secret_value()
    callback = settings.github_callback_url
    local_http = callback.scheme == "http" and callback.host in {"localhost", "127.0.0.1", "[::1]"}
    if not settings.github_client_id or not secret:
        raise HTTPException(503, "GitHub OAuth is not configured")
    if callback.scheme != "https" and not local_http:
        raise HTTPException(503, "GitHub callback must use HTTPS outside localhost")
    return GitHubLogin(settings.github_client_id, secret, redirect_uri=str(callback), allow_insecure_http=local_http)


async def github_redirect(sso: GitHubLogin) -> Response:
    async with sso:
        response = await sso.get_login_redirect()
    # Restrict the short-lived state and PKCE cookies to the callback.
    cookies = [value for key, value in response.raw_headers if key == b"set-cookie"]
    del response.headers["set-cookie"]
    for cookie in cookies:
        name, value = cookie.decode("latin-1").split(";", 1)[0].split("=", 1)
        response.set_cookie(
            name,
            value,
            max_age=COOKIE_MAX_AGE,
            path=CALLBACK_PATH,
            httponly=True,
            secure=not sso.allow_insecure_http,
            samesite="lax",
        )
    response.headers["Cache-Control"] = "no-store"
    return response


async def github_identity(request: Request, sso: Annotated[GitHubLogin, Depends(github_sso)]) -> OpenID:
    try:
        async with sso:
            identity = await sso.verify_and_process(request)
    except SSOLoginError as exc:
        raise HTTPException(401, "GitHub authorization failed") from exc
    except OAuth2Error as exc:
        raise HTTPException(401, "GitHub rejected the authorization code") from exc
    except (HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(502, "Invalid response from GitHub") from exc
    if identity is None or not identity.id or len(identity.id) > 64:
        raise HTTPException(401, "GitHub identity is missing")
    return identity


def verified_email(identity: OpenID) -> str:
    try:
        email = TypeAdapter(EmailStr).validate_python(identity.email)
    except ValidationError as exc:
        raise HTTPException(403, "A verified primary GitHub email is required") from exc
    if len(email) > 255:
        raise HTTPException(403, "GitHub email exceeds the supported length")
    return email
