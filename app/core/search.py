from .gmail import decode_body
from .attachments import search_attachments


# ============================================================
# GET HEADER
# ============================================================

def get_header(
    headers,
    name
):

    return next(
        (
            h["value"]
            for h in headers
            if h["name"].lower() == name.lower()
        ),
        ""
    )


# ============================================================
# EXTRACT EMAIL BODY
# ============================================================

def extract_body(payload):

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

            bodies.append(
                decode_body(
                    body_data
                ).decode(
                    "utf-8",
                    errors="replace"
                )
            )

        except Exception:
            pass

    # --------------------------------------------------------
    # MIME parts
    # --------------------------------------------------------

    for part in payload.get(
        "parts",
        []
    ):

        part_data = (
            part
            .get("body", {})
            .get("data")
        )

        if part_data:

            try:

                bodies.append(
                    decode_body(
                        part_data
                    ).decode(
                        "utf-8",
                        errors="replace"
                    )
                )

            except Exception:
                pass

        # ----------------------------------------------------
        # Nested MIME parts
        # ----------------------------------------------------

        if part.get("parts"):

            nested = extract_body(
                part
            )

            if nested:

                bodies.append(
                    nested
                )

    return "\n".join(
        bodies
    )


# ============================================================
# EXTRACT ATTACHMENT INFORMATION
# ============================================================

def extract_attachments(
    payload
):

    attachments = []

    def process_parts(parts):

        for part in parts:

            filename = part.get(
                "filename",
                ""
            )

            body = part.get(
                "body",
                {}
            )

            # ------------------------------------------------
            # Attachment found
            # ------------------------------------------------

            if filename:

                attachments.append({

                    "filename":
                        filename,

                    "mime_type":
                        part.get(
                            "mimeType",
                            ""
                        ),

                    "size":
                        body.get(
                            "size",
                            0
                        ),

                    "attachment_id":
                        body.get(
                            "attachmentId"
                        )

                })

            # ------------------------------------------------
            # Nested parts
            # ------------------------------------------------

            nested_parts = part.get(
                "parts",
                []
            )

            if nested_parts:

                process_parts(
                    nested_parts
                )

    process_parts(
        payload.get(
            "parts",
            []
        )
    )

    return attachments


# ============================================================
# FETCH ONE EMAIL
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

    label_ids = email.get(
        "labelIds",
        []
    )

    return {

        "id":
            message_id,

        "thread_id":
            email.get(
                "threadId"
            ),

        "sender":
            get_header(
                headers,
                "From"
            ),

        "recipient":
            get_header(
                headers,
                "To"
            ),

        "cc":
            get_header(
                headers,
                "Cc"
            ),

        "bcc":
            get_header(
                headers,
                "Bcc"
            ),

        "subject":
            get_header(
                headers,
                "Subject"
            ),

        "date":
            get_header(
                headers,
                "Date"
            ),

        "body":
            extract_body(
                payload
            ),

        "snippet":
            email.get(
                "snippet",
                ""
            ),

        "labels":
            label_ids,

        "is_unread":
            "UNREAD" in label_ids,

        "is_starred":
            "STARRED" in label_ids,

        "attachments":
            extract_attachments(
                payload
            ),

        # Keep payload internally available
        # for attachment searching.
        "payload":
            payload

    }


# ============================================================
# ANALYZE EMAIL
# ============================================================

def analyze_email(
    service,
    email,
    query
):

    if not query:

        return {

            "matched": True,

            "body_match": False,

            "attachment_match": False,

            "attachment_results": []

        }

    # --------------------------------------------------------
    # Search email body
    # --------------------------------------------------------

    body = email.get(
        "body",
        ""
    )

    body_match = (
        query.lower()
        in body.lower()
    )

    # --------------------------------------------------------
    # Search all attachments
    # --------------------------------------------------------

    attachment_results = search_attachments(
        service,
        email["id"],
        email["payload"],
        query
    )

    attachment_match = (
        len(attachment_results) > 0
    )

    # --------------------------------------------------------
    # Final analysis
    # --------------------------------------------------------

    return {

        "matched": (
            body_match
            or attachment_match
        ),

        "body_match":
            body_match,

        "attachment_match":
            attachment_match,

        "attachment_results":
            attachment_results

    }