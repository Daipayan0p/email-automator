from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import os
import base64
import pandas as pd

from io import BytesIO
from datetime import datetime, timedelta


# ============================================================
# GMAIL CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]


# ============================================================
# USER CONFIGURATION
# ============================================================

# What you want to search for
searchField = "Y5Z6X3W9"


# Date range
# Format: DD-MM-YYYY

date_from = "27-08-2026"
date_to = "29-08-2026"


# Email selection mode
#
# "all"    -> all matching emails
# "top"    -> first N emails
# "last"   -> last N emails
# "custom" -> first N emails

email_mode = "all"

email_count = 10


# ============================================================
# GMAIL AUTHENTICATION
# ============================================================

def get_gmail_service():

    creds = None

    if os.path.exists("token.json"):

        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:

            creds.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        with open("token.json", "w") as token:

            token.write(
                creds.to_json()
            )

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


# ============================================================
# CREATE GMAIL DATE QUERY
# ============================================================

def create_gmail_date_query():

    start_date = datetime.strptime(
        date_from,
        "%d-%m-%Y"
    )

    end_date = datetime.strptime(
        date_to,
        "%d-%m-%Y"
    )

    # Gmail's after/before behavior can be easier to work
    # with by extending the boundaries slightly.

    gmail_start = (
        start_date - timedelta(days=1)
    ).strftime("%Y/%m/%d")

    gmail_end = (
        end_date + timedelta(days=1)
    ).strftime("%Y/%m/%d")

    return (
        f"after:{gmail_start} "
        f"before:{gmail_end}"
    )


# ============================================================
# BASE64 DECODER
# ============================================================

def decode_data(data):

    return base64.urlsafe_b64decode(
        data.encode("UTF-8")
    )


# ============================================================
# GET EMAIL BODY
# ============================================================

def get_email_body(payload):

    bodies = []

    # --------------------------------------------------------
    # Direct body
    # --------------------------------------------------------

    body_data = payload.get(
        "body",
        {}
    ).get(
        "data"
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
    # Nested parts
    # --------------------------------------------------------

    for part in payload.get(
        "parts",
        []
    ):

        mime_type = part.get(
            "mimeType",
            ""
        )

        part_body = part.get(
            "body",
            {}
        ).get(
            "data"
        )

        if part_body and mime_type in (
            "text/plain",
            "text/html"
        ):

            try:

                body = decode_data(
                    part_body
                ).decode(
                    "utf-8",
                    errors="replace"
                )

                bodies.append(body)

            except Exception:
                pass

        # Recursively search nested parts

        if part.get("parts"):

            nested_body = get_email_body(
                part
            )

            if nested_body:

                bodies.append(
                    nested_body
                )

    return "\n".join(
        bodies
    )


# ============================================================
# GET EMAIL HEADER
# ============================================================

def get_header(
    headers,
    name
):

    return next(
        (
            header["value"]
            for header in headers
            if header["name"].lower()
            == name.lower()
        ),
        ""
    )


# ============================================================
# GET EXCEL ATTACHMENT
# ============================================================

def get_excel_data(
    service,
    message_id,
    part
):

    filename = part.get(
        "filename",
        ""
    )

    attachment_id = (
        part.get(
            "body",
            {}
        ).get(
            "attachmentId"
        )
    )

    if not filename or not attachment_id:

        return None


    # Only process Excel files

    if not filename.lower().endswith(
        (
            ".xlsx",
            ".xls"
        )
    ):

        return None


    # Get attachment from Gmail

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


    # Return bytes.
    #
    # Nothing is saved to disk.

    return decode_data(
        data
    )


# ============================================================
# EXCEL → DATAFRAME
# ============================================================

def excel_to_dataframe(
    excel_data,
    original_filename
):

    try:

        # Keep Excel in memory

        excel_file = BytesIO(
            excel_data
        )

        # Read Excel directly into pandas

        df = pd.read_excel(
            excel_file
        )

        return df

    except Exception as e:

        print(
            f"Excel processing error "
            f"for {original_filename}: {e}"
        )

        return None


# ============================================================
# SEARCH DATAFRAME
# ============================================================

def search_dataframe(df):

    try:

        for column in df.columns:

            for value in df[column]:

                if searchField.lower() in str(
                    value
                ).lower():

                    return True

        return False

    except Exception as e:

        print(
            f"DataFrame search error: {e}"
        )

        return False


# ============================================================
# PROCESS EXCEL ATTACHMENTS
# ============================================================

def process_attachments(
    service,
    message_id,
    payload
):

    found = False

    # --------------------------------------------------------
    # Check every part
    # --------------------------------------------------------

    for part in payload.get(
        "parts",
        []
    ):

        filename = part.get(
            "filename",
            ""
        )

        # ----------------------------------------------------
        # Excel attachment
        # ----------------------------------------------------

        if filename.lower().endswith(
            (
                ".xlsx",
                ".xls"
            )
        ):

            excel_data = get_excel_data(
                service,
                message_id,
                part
            )

            if excel_data:

                # Convert directly to DataFrame.
                # NO CSV FILE IS CREATED.

                df = excel_to_dataframe(
                    excel_data,
                    filename
                )

                if df is not None:

                    if search_dataframe(df):

                        found = True

        # ----------------------------------------------------
        # Nested MIME parts
        # ----------------------------------------------------

        if part.get("parts"):

            nested_found = process_attachments(
                service,
                message_id,
                part
            )

            if nested_found:

                found = True

    return found


# ============================================================
# GET EMAILS
# ============================================================

def get_messages(service):

    gmail_query = create_gmail_date_query()

    messages = []

    page_token = None

    # --------------------------------------------------------
    # Get all matching emails
    # --------------------------------------------------------

    while True:

        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=gmail_query,
                maxResults=500,
                pageToken=page_token
            )
            .execute()
        )

        batch = response.get(
            "messages",
            []
        )

        messages.extend(
            batch
        )

        page_token = response.get(
            "nextPageToken"
        )

        if not page_token:

            break


    # --------------------------------------------------------
    # Select emails
    # --------------------------------------------------------

    if email_mode == "all":

        return messages

    elif email_mode == "top":

        return messages[
            :email_count
        ]

    elif email_mode == "last":

        return messages[
            -email_count:
        ]

    elif email_mode == "custom":

        return messages[
            :email_count
        ]

    else:

        raise ValueError(
            "email_mode must be "
            "'all', 'top', 'last', or 'custom'"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    service = get_gmail_service()

    messages = get_messages(
        service
    )

    print(
        f"Checking {len(messages)} emails..."
    )

    print()

    # --------------------------------------------------------
    # Process emails
    # --------------------------------------------------------

    for message in messages:

        message_id = message["id"]

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

        payload = email["payload"]

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

        # ====================================================
        # SEARCH EMAIL BODY
        # ====================================================

        body = get_email_body(
            payload
        )

        body_found = (
            searchField.lower()
            in body.lower()
        )

        # ====================================================
        # SEARCH EXCEL ATTACHMENTS
        # ====================================================

        attachment_found = process_attachments(
            service,
            message_id,
            payload
        )

        # ====================================================
        # ONLY PRINT MATCHES
        # ====================================================

        if body_found or attachment_found:

            print(
                f"From: {sender}"
            )

            print(
                f"Subject: {subject}"
            )

            print(
                f"FOUND: {searchField}"
            )

            print(
                "-" * 50
            )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()