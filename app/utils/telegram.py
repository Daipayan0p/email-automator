import os
import requests


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

    message = "📩 EMAIL RULE MATCHED!\n\n"

    message += f"Subject: {subject}\n"

    if sender:
        message += f"From: {sender}\n"

    if rule_names:
        message += f"Rule(s): {', '.join(rule_names)}"

    try:

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message
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