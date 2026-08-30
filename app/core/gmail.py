from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import base64
import json

from .auth_store import load_token, save_token


# ============================================================
# GMAIL CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]


# ============================================================
# GMAIL AUTHENTICATION
# ============================================================

def get_gmail_service():

    token_data = load_token()

    if not token_data:
        raise Exception(
            "Gmail not authenticated. Call GET /auth/google/login first."
        )

    creds = Credentials.from_authorized_user_info(
        token_data,
        SCOPES
    )

    # --------------------------------------------------------
    # Refresh token if necessary
    # --------------------------------------------------------

    if creds.expired and creds.refresh_token:

        creds.refresh(Request())

        save_token(
            json.loads(creds.to_json())
        )

    # --------------------------------------------------------
    # Gmail API service
    # --------------------------------------------------------

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


# ============================================================
# DECODE GMAIL BODY / ATTACHMENT
# ============================================================

def decode_body(data):

    return base64.urlsafe_b64decode(
        data.encode("UTF-8")
    )
