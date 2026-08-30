# ============================================================
# GMAIL PUB/SUB WATCH
# ============================================================

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
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

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json"
)

STATE_FILE = os.path.join(
    BASE_DIR,
    "state.json"
)


# ============================================================
# GMAIL CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]

PROJECT_ID = "email-automator-506819"

TOPIC_NAME = "gmail-notifications"


# ============================================================
# GMAIL AUTHENTICATION
# ============================================================

def get_gmail_service():

    creds = None

    print()
    print("=" * 60)
    print("GMAIL AUTHENTICATION")
    print("=" * 60)

    print(
        "Looking for token at:"
    )

    print(
        TOKEN_FILE
    )


    # ========================================================
    # LOAD EXISTING TOKEN
    # ========================================================

    if os.path.exists(TOKEN_FILE):

        print(
            "Existing token found."
        )

        try:

            creds = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES
            )

        except Exception as e:

            print(
                "⚠️ Could not load token:"
            )

            print(
                str(e)
            )

            creds = None


    # ========================================================
    # REFRESH TOKEN
    # ========================================================

    if creds and creds.expired:

        if creds.refresh_token:

            print(
                "Token expired. Refreshing..."
            )

            try:

                creds.refresh(
                    Request()
                )

                print(
                    "✅ Token refreshed."
                )

            except Exception as e:

                print(
                    "⚠️ Token refresh failed:"
                )

                print(
                    str(e)
                )

                creds = None

        else:

            print(
                "⚠️ Token expired and has no refresh token."
            )

            creds = None


    # ========================================================
    # NEW AUTHENTICATION
    # ========================================================

    if not creds or not creds.valid:

        print()
        print(
            "🔐 Gmail authentication required."
        )


        # ----------------------------------------------------
        # Check credentials.json
        # ----------------------------------------------------

        if not os.path.exists(
            CREDENTIALS_FILE
        ):

            raise FileNotFoundError(
                "\ncredentials.json not found at:\n"
                f"{CREDENTIALS_FILE}\n\n"
                "Place your Google OAuth credentials.json "
                "in the project root."
            )


        # ----------------------------------------------------
        # Start OAuth
        # ----------------------------------------------------

        print(
            "Starting Google OAuth..."
        )

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )

        creds = flow.run_local_server(
            port=0
        )


        # ----------------------------------------------------
        # Save token
        # ----------------------------------------------------

        with open(
            TOKEN_FILE,
            "w",
            encoding="utf-8"
        ) as token:

            token.write(
                creds.to_json()
            )

        print(
            "✅ New token created."
        )

        print(
            f"Token saved to: {TOKEN_FILE}"
        )


    # ========================================================
    # BUILD GMAIL SERVICE
    # ========================================================

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    print(
        "✅ Gmail service ready."
    )

    print("=" * 60)

    return service


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


    print()
    print(
        "Starting Gmail Pub/Sub watch..."
    )


    response = (
        service.users()
        .watch(
            userId="me",
            body=request_body
        )
        .execute()
    )


    history_id = response[
        "historyId"
    ]

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
    print("=" * 60)
    print("GMAIL WATCH CONFIGURED")
    print("=" * 60)

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

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    start_gmail_watch()