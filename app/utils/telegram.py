import os
from html import escape

import requests


def _telegram_value(value, limit=240):
    value = " ".join(str(value or "").split())
    return escape(value[:limit])


def send_telegram_notification(subject, rule_names, sender=None):
    """
    Send a Telegram notification when an email matches a rule.
    """

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    # Telegram is not configured
    if not bot_token or not chat_id:
        print("Telegram notification skipped: credentials not configured")
        return False

    rules = ", ".join(
        str(rule_name)
        for rule_name in rule_names
        if rule_name
    )

    message_lines = [
        "<b>Email rule matched</b>",
        f"<b>From:</b> {_telegram_value(sender) or 'Unknown'}",
        f"<b>Subject:</b> {_telegram_value(subject) or 'No subject'}",
    ]

    if rules:
        message_lines.append(
            f"<b>Rule:</b> {_telegram_value(rules)}"
        )

    message = "\n".join(message_lines)

    try:

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            },
            timeout=10
        )

        response.raise_for_status()

        print("Telegram notification sent!")

        return True

    except Exception as e:

        print(
            "Telegram notification failed:",
            str(e)
        )

        return False
