from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import os
import base64


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)


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

    creds = None

    if os.path.exists(TOKEN_FILE):

        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    else:

        raise Exception(
            f"token.json not found at:\n{TOKEN_FILE}"
        )

    # --------------------------------------------------------
    # Refresh token if necessary
    # --------------------------------------------------------

    if creds.expired and creds.refresh_token:

        creds.refresh(Request())

        with open(
            TOKEN_FILE,
            "w",
            encoding="utf-8"
        ) as token:

            token.write(
                creds.to_json()
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