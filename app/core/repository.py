import json

from .database import get_connection


# ============================================================
# SAVE EMAIL + ATTACHMENTS + RULE MATCHES
# ============================================================

def save_email_result(
    email,
    matching_rules
):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        email_id = email.get("id")

        # ----------------------------------------------------
        # Check if email already exists
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM emails
            WHERE id = ?
        """, (
            email_id,
        ))

        existing_email = cursor.fetchone()

        # ----------------------------------------------------
        # Duplicate email
        # ----------------------------------------------------

        if existing_email:
            return False

        # ----------------------------------------------------
        # Save email
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO emails (
                id,
                thread_id,
                sender,
                recipient,
                cc,
                bcc,
                subject,
                date,
                body,
                snippet,
                labels,
                is_unread,
                is_starred
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email_id,
            email.get("thread_id"),
            email.get("sender", ""),
            email.get("recipient", ""),
            email.get("cc", ""),
            email.get("bcc", ""),
            email.get("subject", ""),
            email.get("date", ""),
            email.get("body", ""),
            email.get("snippet", ""),
            json.dumps(
                email.get(
                    "labels",
                    []
                )
            ),
            int(
                email.get(
                    "is_unread",
                    False
                )
            ),
            int(
                email.get(
                    "is_starred",
                    False
                )
            )
        ))

        # ----------------------------------------------------
        # Save attachments
        # ----------------------------------------------------

        for attachment in email.get(
            "attachments",
            []
        ):

            cursor.execute("""
                INSERT INTO attachments (
                    email_id,
                    filename,
                    mime_type,
                    size,
                    attachment_id
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                email_id,
                attachment.get(
                    "filename",
                    ""
                ),
                attachment.get(
                    "mime_type",
                    ""
                ),
                attachment.get(
                    "size",
                    0
                ),
                attachment.get(
                    "attachment_id"
                )
            ))

        # ----------------------------------------------------
        # Save matching rules
        # ----------------------------------------------------

        for rule in matching_rules:

            rule_id = rule.get("id")

            if not rule_id:
                continue

            # ------------------------------------------------
            # Save rule
            # ------------------------------------------------

            cursor.execute("""
                INSERT INTO rules (
                    id,
                    name,
                    enabled,
                    mode,
                    conditions
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    enabled = excluded.enabled,
                    mode = excluded.mode,
                    conditions = excluded.conditions
            """, (
                rule_id,
                rule.get(
                    "name",
                    ""
                ),
                int(
                    rule.get(
                        "enabled",
                        True
                    )
                ),
                rule.get(
                    "mode",
                    "CONDITIONAL"
                ),
                json.dumps(
                    rule.get(
                        "conditions",
                        {}
                    )
                )
            ))

            # ------------------------------------------------
            # Save email ↔ rule relationship
            # ------------------------------------------------

            cursor.execute("""
                INSERT OR IGNORE INTO email_rule_matches (
                    email_id,
                    rule_id
                )
                VALUES (?, ?)
            """, (
                email_id,
                rule_id
            ))

        # ----------------------------------------------------
        # Commit everything
        # ----------------------------------------------------

        connection.commit()

        return True

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# GET EMAIL BY ID
# ============================================================

def get_email_by_id(
    email_id
):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM emails
            WHERE id = ?
        """, (
            email_id,
        ))

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:

        connection.close()

# ============================================================
# LOG ACTION EXECUTION
# ============================================================

def log_action_execution(
    email_id,
    rule_id,
    action,
    status,
    error=None
):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO action_executions (
                email_id,
                rule_id,
                action,
                status,
                error
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            email_id,
            rule_id,
            action,
            status,
            error
        ))

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ============================================================
# GET ACTION HISTORY FOR EMAIL
# ============================================================

def get_action_history(email_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM action_executions
            WHERE email_id = ?
            ORDER BY executed_at ASC
        """, (
            email_id,
        ))

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()

# ============================================================
# GET ALL SAVED EMAILS
# ============================================================

def get_all_emails():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM emails
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()

# ============================================================
# DELETE EMAIL
# ============================================================

def delete_email(email_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # Check email exists
        cursor.execute("""
            SELECT id
            FROM emails
            WHERE id = ?
        """, (email_id,))

        email = cursor.fetchone()

        if email is None:
            return False

        # Delete attachments
        cursor.execute("""
            DELETE FROM attachments
            WHERE email_id = ?
        """, (email_id,))

        # Delete rule matches
        cursor.execute("""
            DELETE FROM email_rule_matches
            WHERE email_id = ?
        """, (email_id,))

        # Delete action history
        cursor.execute("""
            DELETE FROM action_executions
            WHERE email_id = ?
        """, (email_id,))

        # Delete email
        cursor.execute("""
            DELETE FROM emails
            WHERE id = ?
        """, (email_id,))

        connection.commit()

        return True

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()