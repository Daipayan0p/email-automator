from .search import (
    fetch_email,
    analyze_email
)


# ============================================================
# PROCESS ONE EMAIL
# ============================================================

def process_email(
    service,
    message_id,
    query=None
):
    """
    Central email processing engine.

    Used by:
        - Manual search
        - API
        - Gmail Pub/Sub watcher
        - Future mobile application
        - Future automation rules
    """

    # --------------------------------------------------------
    # Fetch email
    # --------------------------------------------------------

    email = fetch_email(
        service,
        message_id
    )

    # --------------------------------------------------------
    # If there is no query,
    # simply return the email.
    # --------------------------------------------------------

    if not query:

        return {

            "matched": True,

            "email": email,

            "body_match": False,

            "attachment_match": False,

            "attachment_results": []

        }

    # --------------------------------------------------------
    # Analyze email
    # --------------------------------------------------------

    analysis = analyze_email(
        service,
        email,
        query
    )

    # --------------------------------------------------------
    # Unified result
    # --------------------------------------------------------

    return {

        "matched":
            analysis["matched"],

        "email":
            email,

        "body_match":
            analysis["body_match"],

        "attachment_match":
            analysis["attachment_match"],

        "attachment_results":
            analysis["attachment_results"]

    }