import hashlib
import json
from datetime import datetime, timedelta, timezone

from .database import get_connection


def notification_key(envelope, notification):
    message_id = envelope.get("message", {}).get("messageId")
    if message_id:
        return str(message_id)

    payload = json.dumps(notification, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def enqueue_notification(envelope, notification):
    connection = get_connection()

    try:
        key = notification_key(envelope, notification)
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO pubsub_queue (notification_key, notification)
            VALUES (?, ?)
            """,
            (key, json.dumps(notification)),
        )
        connection.commit()
        return cursor.rowcount == 1
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def claim_next_notification():
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT id, notification, attempts
            FROM pubsub_queue
            WHERE status = 'pending'
              AND available_at <= CURRENT_TIMESTAMP
            ORDER BY id
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            connection.rollback()
            return None

        connection.execute(
            """
            UPDATE pubsub_queue
            SET status = 'processing',
                attempts = attempts + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (row["id"],),
        )
        connection.commit()

        return {
            "id": row["id"],
            "notification": json.loads(row["notification"]),
            "attempts": row["attempts"] + 1,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def complete_notification(queue_id):
    _update_notification(queue_id, "complete", None)


def retry_notification(queue_id, error, delay_seconds):
    connection = get_connection()

    try:
        available_at = (
            datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        ).strftime("%Y-%m-%d %H:%M:%S")
        connection.execute(
            """
            UPDATE pubsub_queue
            SET status = 'pending', last_error = ?,
                available_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (str(error), available_at, queue_id),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def fail_notification(queue_id, error):
    _update_notification(queue_id, "failed", str(error))


def _update_notification(queue_id, status, error):
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE pubsub_queue
            SET status = ?, last_error = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, error, queue_id),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def claim_message(message_id):
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute(
            """
            SELECT status, updated_at
            FROM processed_messages
            WHERE message_id = ?
            """,
            (message_id,),
        ).fetchone()

        if existing and existing["status"] == "complete":
            connection.rollback()
            return False

        if existing and existing["status"] == "processing":
            updated_at = datetime.strptime(
                existing["updated_at"],
                "%Y-%m-%d %H:%M:%S"
            )
            stale = updated_at < datetime.utcnow() - timedelta(minutes=10)
            if not stale:
                connection.rollback()
                return False

        if existing:
            connection.execute(
                """
                UPDATE processed_messages
                SET status = 'processing', attempts = attempts + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE message_id = ?
                """,
                (message_id,),
            )
        else:
            connection.execute(
                """
                INSERT INTO processed_messages (message_id, status)
                VALUES (?, 'processing')
                """,
                (message_id,),
            )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def complete_message(message_id):
    _update_message(message_id, "complete", None)


def fail_message(message_id, error):
    _update_message(message_id, "failed", str(error))


def _update_message(message_id, status, error):
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE processed_messages
            SET status = ?, last_error = ?, updated_at = CURRENT_TIMESTAMP
            WHERE message_id = ?
            """,
            (status, error, message_id),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def recover_stale_notifications(max_age_minutes=10):
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE pubsub_queue
            SET status = 'pending', updated_at = CURRENT_TIMESTAMP
            WHERE status = 'processing'
              AND updated_at < datetime('now', ?)
            """,
            (f"-{max_age_minutes} minutes",),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
