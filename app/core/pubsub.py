import base64
import json

from .auth_store import load_history_id, save_state
from .gmail import get_gmail_service
from .engine import process_email


# ============================================================
# DECODE PUB/SUB MESSAGE
# ============================================================

def decode_pubsub_message(body):

    """
    Google Pub/Sub push format:

    {
        "message": {
            "data": "base64..."
        },
        "subscription": "..."
    }
    """

    message = body.get(
        "message"
    )

    if not message:
        raise ValueError(
            "Pub/Sub message missing"
        )

    encoded_data = message.get(
        "data"
    )

    if not encoded_data:
        raise ValueError(
            "Pub/Sub message data missing"
        )

    decoded_data = base64.b64decode(
        encoded_data
    ).decode(
        "utf-8"
    )

    return json.loads(
        decoded_data
    )


# ============================================================
# GET NEW GMAIL MESSAGE IDS
# ============================================================

def get_new_message_ids(
    service,
    start_history_id
):

    message_ids = []

    page_token = None

    while True:

        request = (
            service.users()
            .history()
            .list(
                userId="me",
                startHistoryId=start_history_id,
                historyTypes=[
                    "messageAdded"
                ]
            )
        )

        if page_token:

            request = (
                service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=start_history_id,
                    historyTypes=[
                        "messageAdded"
                    ],
                    pageToken=page_token
                )
            )

        response = request.execute()

        history = response.get(
            "history",
            []
        )

        for history_item in history:

            for message_added in history_item.get(
                "messagesAdded",
                []
            ):

                message = message_added.get(
                    "message",
                    {}
                )

                message_id = message.get(
                    "id"
                )

                if message_id:

                    message_ids.append(
                        message_id
                    )

        page_token = response.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return list(
        dict.fromkeys(
            message_ids
        )
    )


# ============================================================
# PROCESS PUB/SUB NOTIFICATION
# ============================================================

def process_pubsub_notification(
    body
):

    # --------------------------------------------------------
    # Decode notification
    # --------------------------------------------------------

    notification = decode_pubsub_message(
        body
    )

    notification_history_id = notification.get(
        "historyId"
    )

    if not notification_history_id:

        raise ValueError(
            "Gmail notification does not contain historyId"
        )

    print()
    print("=" * 60)
    print("GMAIL PUB/SUB NOTIFICATION")
    print("=" * 60)

    print(
        "New History ID:",
        notification_history_id
    )

    # --------------------------------------------------------
    # Load previous history ID
    # --------------------------------------------------------

    previous_history_id = load_history_id()

    print(
        "Previous History ID:",
        previous_history_id
    )

    # --------------------------------------------------------
    # Connect Gmail
    # --------------------------------------------------------

    service = get_gmail_service()

    # --------------------------------------------------------
    # First notification
    #
    # If there is no previous history ID, we cannot safely
    # determine which messages are new.
    # --------------------------------------------------------

    if not previous_history_id:

        save_state(notification_history_id)

        print(
            "No previous history ID."
        )

        print(
            "History ID initialized."
        )

        print("=" * 60)

        return {
            "processed": 0,
            "matched": 0,
            "message_ids": []
        }

    # --------------------------------------------------------
    # Get new messages
    # --------------------------------------------------------

    message_ids = get_new_message_ids(
        service,
        previous_history_id
    )

    print(
        "New messages:",
        len(message_ids)
    )

    # --------------------------------------------------------
    # Process every new email
    # --------------------------------------------------------

    processed = 0
    matched = 0

    results = []

    for message_id in message_ids:

        try:

            print()
            print(
                "Processing:",
                message_id
            )

            result = process_email(
                service,
                message_id
            )

            processed += 1

            if result["matched"]:

                matched += 1

            matching_rules = [
                rule.get("name")
                for rule in result.get(
                    "matching_rules",
                    []
                )
            ]

            print(
                "Subject:",
                result["email"].get(
                    "subject",
                    ""
                )
            )

            print(
                "Matched:",
                result["matched"]
            )

            print(
                "Rules:",
                matching_rules
            )

            print(
                "Saved:",
                result.get(
                    "saved",
                    False
                )
            )

            results.append({

                "message_id":
                    message_id,

                "matched":
                    result["matched"],

                "saved":
                    result.get(
                        "saved",
                        False
                    ),

                "matching_rules":
                    matching_rules

            })

        except Exception as e:

            print(
                "Error processing",
                message_id,
                ":",
                str(e)
            )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Update history only after processing.
    # --------------------------------------------------------

    save_state(notification_history_id)

    print()
    print("=" * 60)
    print("PUB/SUB PROCESSING COMPLETE")
    print("=" * 60)

    print(
        "Processed:",
        processed
    )

    print(
        "Matched:",
        matched
    )

    print("=" * 60)

    return {

        "processed":
            processed,

        "matched":
            matched,

        "message_ids":
            message_ids,

        "results":
            results

    }
