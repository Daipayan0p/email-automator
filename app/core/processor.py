from .gmail import get_gmail_service
from .search import fetch_email, analyze_email


def process_email(
    message_id,
    query
):

    service = get_gmail_service()

    email = fetch_email(
        service,
        message_id
    )

    analysis = analyze_email(
        service,
        email,
        query
    )

    return {
        "id": email["id"],
        "sender": email["sender"],
        "subject": email["subject"],
        "date": email["date"],
        "matched": analysis["matched"],
        "body_match": analysis["body_match"],
        "attachment_match": analysis["attachment_match"]
    }