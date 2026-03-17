from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlencode

import httpx

from .config import Settings
from .db import TokenRecord, utc_now


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class GoogleOAuthError(RuntimeError):
    pass


def is_google_configured(settings: Settings) -> bool:
    return bool(settings.google_client_id and settings.google_client_secret)


def build_google_auth_url(settings: Settings, state: str) -> str:
    if not is_google_configured(settings):
        raise GoogleOAuthError("Google OAuth is not configured.")

    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": settings.youtube_api_scope,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "state": state,
        }
    )
    return f"{GOOGLE_AUTH_URL}?{query}"


def exchange_code_for_token(settings: Settings, code: str) -> dict:
    if not is_google_configured(settings):
        raise GoogleOAuthError("Google OAuth is not configured.")

    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=30.0,
    )

    if response.status_code >= 400:
        raise GoogleOAuthError(response.text)

    payload = response.json()
    if "refresh_token" not in payload:
        raise GoogleOAuthError("Google did not return a refresh token.")

    return payload


def refresh_access_token(settings: Settings, token: TokenRecord) -> dict:
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": token.refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30.0,
    )

    if response.status_code >= 400:
        raise GoogleOAuthError(response.text)

    payload = response.json()
    payload["refresh_token"] = payload.get("refresh_token", token.refresh_token)
    payload["scope"] = payload.get("scope", token.scope)
    return payload


def build_token_values(payload: dict) -> tuple[str, str, str, str]:
    expires_at = (utc_now() + timedelta(seconds=int(payload.get("expires_in", 3600)))).isoformat()
    return (
        payload["access_token"],
        payload["refresh_token"],
        payload.get("scope", ""),
        expires_at,
    )
