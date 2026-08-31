import base64
import json

from googleapiclient.errors import HttpError

from app.repositories.email_repository import email_exists
from .auth_store import load_history_id, save_state_if_newer
from .engine import process_email
from .gmail import get_gmail_service
from .queue import claim_message, complete_message, fail_message


def decode_pubsub_message(body):
    message = body.get("message")
    if not message:
        raise ValueError("Pub/Sub message missing")

    encoded_data = message.get("data")
    if not encoded_data:
        raise ValueError("Pub/Sub message data missing")

    try:
        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
        return json.loads(decoded_data)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Invalid Pub/Sub message data") from error


def validate_notification(notification):
    history_id = notification.get("historyId")
    if not history_id:
        raise ValueError("Gmail notification does not contain historyId")

    try:
        int(history_id)
    except (TypeError, ValueError) as error:
        raise ValueError("Gmail notification historyId is invalid") from error

    return str(history_id)


def get_new_message_ids(service, start_history_id):
    message_ids = []
    page_token = None

    while True:
        request_args = {
            "userId": "me",
            "startHistoryId": start_history_id,
            "historyTypes": ["messageAdded"],
        }
        if page_token:
            request_args["pageToken"] = page_token

        response = service.users().history().list(**request_args).execute()

        for history_item in response.get("history", []):
            for message_added in history_item.get("messagesAdded", []):
                message_id = message_added.get("message", {}).get("id")
                if message_id:
                    message_ids.append(message_id)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return list(dict.fromkeys(message_ids))


def recover_history_baseline(service):
    profile = service.users().get(userId="me").execute()
    history_id = profile.get("historyId")
    if not history_id:
        raise RuntimeError("Gmail profile did not return a historyId")

    save_state_if_newer(history_id)
    print(f"Recovered Gmail history baseline at {history_id}.")
    return history_id


def is_history_expired(error):
    return isinstance(error, HttpError) and error.resp.status == 404


def process_notification(notification):
    notification_history_id = validate_notification(notification)
    previous_history_id = load_history_id()

    if (
        previous_history_id is not None
        and int(notification_history_id) <= int(previous_history_id)
    ):
        return {
            "status": "ignored",
            "reason": "notification is older than the stored history ID",
            "processed": 0,
            "matched": 0,
        }

    service = get_gmail_service()

    if previous_history_id is None:
        save_state_if_newer(notification_history_id)
        return {
            "status": "initialized",
            "processed": 0,
            "matched": 0,
        }

    try:
        message_ids = get_new_message_ids(service, previous_history_id)
    except HttpError as error:
        if is_history_expired(error):
            recover_history_baseline(service)
            return {
                "status": "history_recovered",
                "processed": 0,
                "matched": 0,
            }
        raise

    processed = 0
    matched = 0
    results = []

    for message_id in message_ids:
        if email_exists(message_id) or not claim_message(message_id):
            results.append({"message_id": message_id, "status": "skipped"})
            continue

        try:
            result = process_email(service, message_id)
            processed += 1
            matched += int(result["matched"])
            complete_message(message_id)
            results.append({
                "message_id": message_id,
                "matched": result["matched"],
                "saved": result.get("saved", False),
            })
        except Exception as error:
            if isinstance(error, HttpError) and error.resp.status == 404:
                complete_message(message_id)
                results.append({
                    "message_id": message_id,
                    "status": "skipped",
                    "reason": "message no longer exists",
                })
                continue

            fail_message(message_id, error)
            raise

    # This is atomic and can never move the baseline backwards.
    save_state_if_newer(notification_history_id)
    return {
        "status": "processed",
        "processed": processed,
        "matched": matched,
        "message_ids": message_ids,
        "results": results,
    }


def process_pubsub_notification(body):
    """Compatibility helper for callers that still process synchronously."""
    return process_notification(decode_pubsub_message(body))
