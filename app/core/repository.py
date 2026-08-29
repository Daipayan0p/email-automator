import json

from .database import get_connection


# ============================================================
# SAVE EMAIL
# ============================================================

def save_email(email):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO emails (

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

        email.get("id"),

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

    connection.commit()

    connection.close()


# ============================================================
# SAVE ATTACHMENTS
# ============================================================

def save_attachments(email):

    connection = get_connection()

    cursor = connection.cursor()

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

            email.get("id"),

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

    connection.commit()

    connection.close()


# ============================================================
# SAVE RULE
# ============================================================

def save_rule(rule):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO rules (

            id,
            name,
            enabled,
            mode,
            conditions

        )
        VALUES (?, ?, ?, ?, ?)
    """, (

        rule.get("id"),

        rule.get("name"),

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

    connection.commit()

    connection.close()


# ============================================================
# SAVE EMAIL-RULE MATCH
# ============================================================

def save_rule_match(
    email_id,
    rule_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO
        email_rule_matches (

            email_id,
            rule_id

        )
        VALUES (?, ?)
    """, (

        email_id,
        rule_id

    ))

    connection.commit()

    connection.close()