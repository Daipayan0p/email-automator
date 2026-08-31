import json
import os

# Google may return previously granted compatible Gmail scopes together with
# the requested scope. oauthlib otherwise treats that response as a failure.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

from fastapi import APIRouter, Depends, HTTPException
from google_auth_oauthlib.flow import Flow

from app.core.auth_store import (
    consume_oauth_session,
    delete_token,
    load_token,
    save_oauth_session,
    save_token,
)
from app.config import CREDENTIALS_FILE, OAUTH_REDIRECT_URI
from app.core.gmail import SCOPES
from app.services.gmail_watch import start_gmail_watch
from app.core.security import verify_api_key


router = APIRouter(prefix="/auth", tags=["Auth"])


def get_redirect_uri():
    return OAUTH_REDIRECT_URI


def create_flow():
    if not os.path.exists(CREDENTIALS_FILE):
        raise HTTPException(
            status_code=500,
            detail="OAuth credentials.json is not configured."
        )

    return Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=get_redirect_uri()
    )


@router.get("/google/login", dependencies=[Depends(verify_api_key)])
def google_login():
    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true"
    )

    if not flow.code_verifier:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth did not generate a PKCE code verifier."
        )

    save_oauth_session(state, flow.code_verifier)
    return {"authorization_url": authorization_url}


@router.get("/google/callback")
def google_callback(code: str, state: str):
    flow = create_flow()
    code_verifier = consume_oauth_session(state)

    if not code_verifier:
        raise HTTPException(
            status_code=400,
            detail="OAuth session expired or invalid. Start authentication again."
        )

    try:
        flow.code_verifier = code_verifier
        flow.fetch_token(code=code)
        save_token(json.loads(flow.credentials.to_json()))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {error}")

    watch_started = False
    watch_error = None

    try:
        start_gmail_watch()
        watch_started = True
    except Exception as error:
        watch_error = str(error)

    response = {
        "status": "authenticated",
        "watch_started": watch_started
    }
    if watch_error:
        response["watch_error"] = watch_error
    return response


@router.get("/status", dependencies=[Depends(verify_api_key)])
def auth_status():
    token = load_token()
    return {
        "authenticated": token is not None,
        "expiry": token.get("expiry") if token else None
    }


@router.delete("/google", dependencies=[Depends(verify_api_key)])
def disconnect_google():
    delete_token()
    return {"status": "disconnected"}
