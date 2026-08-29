from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import os
import json


# ============================================================
# PATHS
# ============================================================

# Project root = folder containing app/
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)

STATE_FILE = os.path.join(
    BASE_DIR,
    "state.json"
)


# ============================================================
# GMAIL CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

PROJECT_ID = "email-automator-506819"

TOPIC_NAME = "gmail-notifications"


# ============================================================
# GMAIL AUTHENTICATION
# ============================================================

def get_gmail_service():

    creds = None

    print("Looking for token at:")
    print(TOKEN_FILE)

    if os.path.exists(TOKEN_FILE):

        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    else:

        raise Exception(
            f"token.json not found at:\n{TOKEN_FILE}\n\n"
            "Run main.py first to authenticate Gmail."
        )

    # Refresh token if necessary

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

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


# ============================================================
# START GMAIL WATCH
# ============================================================

def start_gmail_watch():

    service = get_gmail_service()

    topic_name = (
        f"projects/{PROJECT_ID}"
        f"/topics/{TOPIC_NAME}"
    )

    request_body = {
        "topicName": topic_name
    }

    response = (
        service.users()
        .watch(
            userId="me",
            body=request_body
        )
        .execute()
    )

    history_id = response["historyId"]

    expiration = response.get(
        "expiration"
    )

    # ========================================================
    # SAVE HISTORY ID
    # ========================================================

    state = {
        "historyId": history_id
    }

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            state,
            file,
            indent=4
        )

    # ========================================================
    # RESULT
    # ========================================================

    print()
    print("=" * 50)
    print("GMAIL WATCH CONFIGURED")
    print("=" * 50)

    print(
        f"History ID: {history_id}"
    )

    if expiration:

        print(
            f"Expiration: {expiration}"
        )

    print(
        f"State saved to: {STATE_FILE}"
    )

    print("=" * 50)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    start_gmail_watch()