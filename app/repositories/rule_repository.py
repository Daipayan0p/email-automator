import json

from app.core.database import get_connection


# ============================================================
# CREATE RULE
# ============================================================

def create_rule(rule):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO rules (
                id,
                name,
                enabled,
                mode,
                priority,
                conditions,
                actions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            rule["id"],
            rule.get("name", ""),
            int(rule.get("enabled", True)),
            rule.get("mode", "CONDITIONAL"),
            int(rule.get("priority", 0)),
            json.dumps(
                rule.get("conditions", {})
            ),
            json.dumps(
                rule.get("actions", {})
            )
        ))

        connection.commit()

        return get_rule_by_id(rule["id"])

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# GET ALL RULES
# ============================================================

def get_all_rules():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                enabled,
                mode,
                priority,
                conditions,
                actions,
                created_at
            FROM rules
            ORDER BY priority DESC
        """)

        rows = cursor.fetchall()

        rules = []

        for row in rows:

            rule = dict(row)

            rule["enabled"] = bool(
                rule["enabled"]
            )

            rule["conditions"] = json.loads(
                rule["conditions"] or "{}"
            )

            rule["actions"] = json.loads(
                rule["actions"] or "{}"
            )

            rules.append(rule)

        return rules

    finally:

        connection.close()


# ============================================================
# GET RULE BY ID
# ============================================================

def get_rule_by_id(rule_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                enabled,
                mode,
                priority,
                conditions,
                actions,
                created_at
            FROM rules
            WHERE id = ?
        """, (
            rule_id,
        ))

        row = cursor.fetchone()

        if row is None:
            return None

        rule = dict(row)

        rule["enabled"] = bool(
            rule["enabled"]
        )

        rule["conditions"] = json.loads(
            rule["conditions"] or "{}"
        )

        rule["actions"] = json.loads(
            rule["actions"] or "{}"
        )

        return rule

    finally:

        connection.close()


# ============================================================
# UPDATE RULE
# ============================================================

def update_rule(
    rule_id,
    rule
):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            UPDATE rules
            SET
                name = ?,
                enabled = ?,
                mode = ?,
                priority = ?,
                conditions = ?,
                actions = ?
            WHERE id = ?
        """, (
            rule.get("name", ""),
            int(rule.get("enabled", True)),
            rule.get(
                "mode",
                "CONDITIONAL"
            ),
            int(
                rule.get(
                    "priority",
                    0
                )
            ),
            json.dumps(
                rule.get(
                    "conditions",
                    {}
                )
            ),
            json.dumps(
                rule.get(
                    "actions",
                    {}
                )
            ),
            rule_id
        ))

        if cursor.rowcount == 0:
            return None

        connection.commit()

        return get_rule_by_id(rule_id)

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# DELETE RULE
# ============================================================

def delete_rule(rule_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # Remove rule matches first
        cursor.execute("""
            DELETE FROM email_rule_matches
            WHERE rule_id = ?
        """, (
            rule_id,
        ))

        # Remove action history
        cursor.execute("""
            DELETE FROM action_executions
            WHERE rule_id = ?
        """, (
            rule_id,
        ))

        # Delete rule
        cursor.execute("""
            DELETE FROM rules
            WHERE id = ?
        """, (
            rule_id,
        ))

        if cursor.rowcount == 0:
            connection.rollback()
            return False

        connection.commit()

        return True

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()
