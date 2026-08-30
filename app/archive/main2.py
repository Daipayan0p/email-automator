from flask import Flask, request

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import os
import json
import base64

import pandas as pd
from io import BytesIO


# ============================================================
# PATHS
# ============================================================

# Project root
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

RESULT_FILE = os.path.join(
    BASE_DIR,
    "results.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

SEARCH_FIELD = "Y5Z6X3W9"

app = Flask(__name__)


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

    if not creds:

        raise Exception(
            "token.json not found. "
            "Run main.py first to authenticate Gmail."
        )

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
# BASE64 DECODER
# ============================================================

def decode_data(data):

    return base64.urlsafe_b64decode(
        data.encode("UTF-8")
    )


# ============================================================
# GET HEADER
# ============================================================

def get_header(headers, name):

    return next(
        (
            h["value"]
            for h in headers
            if h["name"].lower() == name.lower()
        ),
        ""
    )


# ============================================================
# GET EMAIL BODY
# ============================================================

def get_email_body(payload):

    bodies = []

    # --------------------------------------------------------
    # Direct body
    # --------------------------------------------------------

    body_data = (
        payload
        .get("body", {})
        .get("data")
    )

    if body_data:

        try:

            body = decode_data(
                body_data
            ).decode(
                "utf-8",
                errors="replace"
            )

            bodies.append(body)

        except Exception:

            pass

    # --------------------------------------------------------
    # Multipart body
    # --------------------------------------------------------

    for part in payload.get(
        "parts",
        []
    ):

        mime_type = part.get(
            "mimeType",
            ""
        )

        part_data = (
            part
            .get("body", {})
            .get("data")
        )

        if part_data and mime_type in (
            "text/plain",
            "text/html"
        ):

            try:

                body = decode_data(
                    part_data
                ).decode(
                    "utf-8",
                    errors="replace"
                )

                bodies.append(body)

            except Exception:

                pass

        # ----------------------------------------------------
        # Nested parts
        # ----------------------------------------------------

        if part.get("parts"):

            nested_body = get_email_body(
                part
            )

            if nested_body:

                bodies.append(
                    nested_body
                )

    return "\n".join(bodies)


# ============================================================
# SEARCH EMAIL BODY
# ============================================================

def search_email_body(body):

    return (
        SEARCH_FIELD.lower()
        in body.lower()
    )


# ============================================================
# GET ATTACHMENT DATA
# ============================================================

def get_attachment_data(
    service,
    message_id,
    part
):

    attachment_id = (
        part
        .get("body", {})
        .get("attachmentId")
    )

    if not attachment_id:

        return None

    attachment = (
        service.users()
        .messages()
        .attachments()
        .get(
            userId="me",
            messageId=message_id,
            id=attachment_id
        )
        .execute()
    )

    data = attachment.get(
        "data"
    )

    if not data:

        return None

    return decode_data(data)


# ============================================================
# SEARCH EXCEL ATTACHMENT
# ============================================================

def search_excel_attachment(
    service,
    message_id,
    part
):

    filename = part.get(
        "filename",
        ""
    )

    if not filename.lower().endswith(
        (
            ".xlsx",
            ".xls"
        )
    ):

        return False

    excel_data = get_attachment_data(
        service,
        message_id,
        part
    )

    if not excel_data:

        return False

    try:

        # Excel stays in memory.
        # No Excel or CSV file is created.

        df = pd.read_excel(
            BytesIO(excel_data)
        )

        # Search every cell

        for column in df.columns:

            for value in df[column]:

                if SEARCH_FIELD.lower() in str(
                    value
                ).lower():

                    return True

    except Exception:

        return False

    return False


# ============================================================
# SEARCH ALL ATTACHMENTS
# ============================================================

def search_attachments(
    service,
    message_id,
    payload
):

    for part in payload.get(
        "parts",
        []
    ):

        # ----------------------------------------------------
        # Search Excel
        # ----------------------------------------------------

        if search_excel_attachment(
            service,
            message_id,
            part
        ):

            return True

        # ----------------------------------------------------
        # Search nested parts
        # ----------------------------------------------------

        if part.get("parts"):

            if search_attachments(
                service,
                message_id,
                part
            ):

                return True

    return False


# ============================================================
# FETCH EMAIL
# ============================================================

def fetch_email(
    service,
    message_id
):

    email = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full"
        )
        .execute()
    )

    payload = email.get(
        "payload",
        {}
    )

    headers = payload.get(
        "headers",
        []
    )

    sender = get_header(
        headers,
        "From"
    )

    subject = get_header(
        headers,
        "Subject"
    )

    body = get_email_body(
        payload
    )

    return {
        "id": message_id,
        "sender": sender,
        "subject": subject,
        "body": body,
        "payload": payload
    }


# ============================================================
# ANALYZE EMAIL
# ============================================================

def analyze_email(
    service,
    email
):

    # --------------------------------------------------------
    # Search email body
    # --------------------------------------------------------

    body_match = search_email_body(
        email["body"]
    )

    # --------------------------------------------------------
    # Search Excel attachments
    # --------------------------------------------------------

    attachment_match = search_attachments(
        service,
        email["id"],
        email["payload"]
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return (
        body_match
        or attachment_match
    )


# ============================================================
# SAVE MATCH TO JSON
# ============================================================

def save_result(email):

    result = {
        "id": email["id"],
        "sender": email["sender"],
        "subject": email["subject"],
        "match": SEARCH_FIELD
    }

    results = []

    # --------------------------------------------------------
    # Read existing results
    # --------------------------------------------------------

    if os.path.exists(RESULT_FILE):

        try:

            with open(
                RESULT_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                results = json.load(file)

        except Exception:

            results = []

    # --------------------------------------------------------
    # Prevent duplicate entries
    # --------------------------------------------------------

    existing_ids = {
        item.get("id")
        for item in results
    }

    if email["id"] not in existing_ids:

        results.append(
            result
        )

        # ----------------------------------------------------
        # Save only when there is a match
        # ----------------------------------------------------

        with open(
            RESULT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                results,
                file,
                indent=4,
                ensure_ascii=False
            )


# ============================================================
# PROCESS NEW EMAIL
# ============================================================

def process_new_email(
    message_id
):

    service = get_gmail_service()

    email = fetch_email(
        service,
        message_id
    )

    matched = analyze_email(
        service,
        email
    )

    # --------------------------------------------------------
    # ONLY DO SOMETHING IF MATCHED
    # --------------------------------------------------------

    if matched:

        save_result(
            email
        )

        print()
        print("=" * 50)
        print("MATCH FOUND")
        print("=" * 50)

        print(
            f"From: {email['sender']}"
        )

        print(
            f"Subject: {email['subject']}"
        )

        print(
            f"Matched: {SEARCH_FIELD}"
        )

        print("=" * 50)


# ============================================================
# LOAD STATE
# ============================================================

def load_state():

    if not os.path.exists(STATE_FILE):

        return None

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            state = json.load(file)

        return state.get(
            "historyId"
        )

    except Exception:

        return None


# ============================================================
# SAVE STATE
# ============================================================

def save_state(history_id):

    state = {
        "historyId": str(history_id)
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


# ============================================================
# GMAIL HISTORY
# ============================================================

def process_gmail_history(
    service,
    start_history_id,
    new_history_id
):

    if not start_history_id:

        # We don't have a previous state.
        # Save the current notification ID and wait
        # for the next notification.

        save_state(
            new_history_id
        )

        return

    message_ids = set()

    current_history_id = start_history_id

    try:

        while True:

            response = (
                service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=current_history_id,
                    historyTypes=[
                        "messageAdded"
                    ]
                )
                .execute()
            )

            history = response.get(
                "history",
                []
            )

            # ------------------------------------------------
            # Find newly added messages
            # ------------------------------------------------

            for history_item in history:

                added_messages = (
                    history_item.get(
                        "messagesAdded",
                        []
                    )
                )

                for item in added_messages:

                    message = item.get(
                        "message",
                        {}
                    )

                    message_id = message.get(
                        "id"
                    )

                    if message_id:

                        message_ids.add(
                            message_id
                        )

            # ------------------------------------------------
            # Pagination
            # ------------------------------------------------

            next_page_token = response.get(
                "nextPageToken"
            )

            if not next_page_token:

                break

            # Gmail history pagination uses the next page
            # token while keeping the same start history ID.

            response = (
                service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=start_history_id,
                    historyTypes=[
                        "messageAdded"
                    ],
                    pageToken=next_page_token
                )
                .execute()
            )

            history = response.get(
                "history",
                []
            )

            for history_item in history:

                added_messages = (
                    history_item.get(
                        "messagesAdded",
                        []
                    )
                )

                for item in added_messages:

                    message = item.get(
                        "message",
                        {}
                    )

                    message_id = message.get(
                        "id"
                    )

                    if message_id:

                        message_ids.add(
                            message_id
                        )

            break

    except Exception:

        # Don't update state if Gmail history
        # could not be processed.
        raise

    # --------------------------------------------------------
    # Process each new message
    # --------------------------------------------------------

    for message_id in message_ids:

        try:

            process_new_email(
                message_id
            )

        except Exception:

            # One bad email should not crash
            # the entire webhook.

            pass

    # --------------------------------------------------------
    # IMPORTANT:
    # Update state AFTER processing.
    # --------------------------------------------------------

    save_state(
        new_history_id
    )


# ============================================================
# PUB/SUB WEBHOOK
# ============================================================

@app.route(
    "/pubsub",
    methods=["POST"]
)
def pubsub():

    envelope = request.get_json(
        silent=True
    )

    if not envelope:

        return "Bad Request", 400

    message = envelope.get(
        "message"
    )

    if not message:

        return "No message", 400

    encoded_data = message.get(
        "data"
    )

    if not encoded_data:

        return "No data", 400

    try:

        decoded_data = base64.b64decode(
            encoded_data
        ).decode(
            "utf-8"
        )

        notification = json.loads(
            decoded_data
        )

    except Exception:

        return "Invalid data", 400

    # --------------------------------------------------------
    # Gmail notification history ID
    # --------------------------------------------------------

    new_history_id = notification.get(
        "historyId"
    )

    if not new_history_id:

        return "No historyId", 400

    # --------------------------------------------------------
    # Previous history ID
    # --------------------------------------------------------

    old_history_id = load_state()

    try:

        service = get_gmail_service()

        process_gmail_history(
            service,
            old_history_id,
            new_history_id
        )

    except Exception:

        return "Processing failed", 500

    # --------------------------------------------------------
    # Tell Pub/Sub we successfully handled it
    # --------------------------------------------------------

    return "OK", 200


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def health():

    return "Email Automator is running"


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    # No startup output from our application.

    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False
    )