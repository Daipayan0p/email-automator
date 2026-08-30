from app.core.auth_store import save_state
from app.core.gmail import get_gmail_service


PROJECT_ID = "email-automator-506819"
TOPIC_NAME = "gmail-notifications"


def start_gmail_watch():
    service = get_gmail_service()
    topic_name = f"projects/{PROJECT_ID}/topics/{TOPIC_NAME}"

    response = (
        service.users()
        .watch(
            userId="me",
            body={"topicName": topic_name}
        )
        .execute()
    )

    history_id = response["historyId"]
    expiration = response.get("expiration")
    save_state(history_id, expiration)

    print("Gmail Pub/Sub watch configured.")
    print(f"History ID: {history_id}")
    if expiration:
        print(f"Expiration: {expiration}")

    return response


if __name__ == "__main__":
    start_gmail_watch()
