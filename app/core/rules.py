import json

from .database import get_connection


# ============================================================
# LOAD RULES FROM DATABASE
# ============================================================

def load_rules():
    """
    Load all enabled rules from SQLite.

    Rules are stored in the database as:
        - id
        - name
        - enabled
        - mode
        - priority
        - conditions
        - actions
    """

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
                actions
            FROM rules
            WHERE enabled = 1
            ORDER BY priority DESC
        """)

        rows = cursor.fetchall()

        rules = []

        for row in rows:

            rule = dict(row)

            # ------------------------------------------------
            # Convert SQLite values back to Python values
            # ------------------------------------------------

            rule["enabled"] = bool(
                rule.get("enabled", 1)
            )

            # Conditions are stored as JSON
            try:
                rule["conditions"] = json.loads(
                    rule.get("conditions") or "{}"
                )
            except json.JSONDecodeError:
                rule["conditions"] = {}

            # Actions are stored as JSON
            try:
                rule["actions"] = json.loads(
                    rule.get("actions") or "{}"
                )
            except json.JSONDecodeError:
                rule["actions"] = {}

            # Priority
            try:
                rule["priority"] = int(
                    rule.get("priority", 0)
                )
            except (TypeError, ValueError):
                rule["priority"] = 0

            rules.append(rule)

        return rules

    finally:
        connection.close()


# ============================================================
# GET RULE PRIORITY
# ============================================================

def get_rule_priority(rule):

    try:
        return int(
            rule.get(
                "priority",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return 0


# ============================================================
# TEXT MATCH
# ============================================================

def text_matches(
    value,
    expected
):

    if not expected:
        return True

    if not value:
        return False

    return (
        str(expected).lower()
        in str(value).lower()
    )


# ============================================================
# CHECK ONE RULE
# ============================================================

def matches_rule(
    email,
    rule
):

    if not isinstance(
        rule,
        dict
    ):
        return False

    # --------------------------------------------------------
    # Disabled rule
    # --------------------------------------------------------

    if not rule.get(
        "enabled",
        True
    ):
        return False

    # --------------------------------------------------------
    # Rule mode
    # --------------------------------------------------------

    mode = str(
        rule.get(
            "mode",
            "CONDITIONAL"
        )
    ).upper()

    # --------------------------------------------------------
    # Match every email
    # --------------------------------------------------------

    if mode == "ALL_EMAILS":
        return True

    # --------------------------------------------------------
    # Unknown mode
    # --------------------------------------------------------

    if mode != "CONDITIONAL":
        return False

    conditions = rule.get(
        "conditions",
        {}
    )

    if not isinstance(
        conditions,
        dict
    ):
        return False

    # ========================================================
    # SENDER
    # ========================================================

    if conditions.get("sender"):

        if not text_matches(
            email.get("sender", ""),
            conditions["sender"]
        ):
            return False

    # ========================================================
    # RECIPIENT
    # ========================================================

    if conditions.get("recipient"):

        if not text_matches(
            email.get("recipient", ""),
            conditions["recipient"]
        ):
            return False

    # ========================================================
    # CC
    # ========================================================

    if conditions.get("cc"):

        if not text_matches(
            email.get("cc", ""),
            conditions["cc"]
        ):
            return False

    # ========================================================
    # BCC
    # ========================================================

    if conditions.get("bcc"):

        if not text_matches(
            email.get("bcc", ""),
            conditions["bcc"]
        ):
            return False

    # ========================================================
    # SUBJECT
    # ========================================================

    if conditions.get("subject"):

        if not text_matches(
            email.get("subject", ""),
            conditions["subject"]
        ):
            return False

    # ========================================================
    # BODY
    # ========================================================

    if conditions.get("body"):

        if not text_matches(
            email.get("body", ""),
            conditions["body"]
        ):
            return False

    # ========================================================
    # GENERAL QUERY
    # ========================================================

    if conditions.get("query"):

        query = str(
            conditions["query"]
        ).lower()

        searchable_text = " ".join([
            str(email.get("sender", "")),
            str(email.get("recipient", "")),
            str(email.get("cc", "")),
            str(email.get("bcc", "")),
            str(email.get("subject", "")),
            str(email.get("body", "")),
            str(email.get("snippet", ""))
        ]).lower()

        if query not in searchable_text:
            return False

    # ========================================================
    # HAS ATTACHMENT
    # ========================================================

    if conditions.get(
        "has_attachment"
    ) is not None:

        has_attachment = (
            len(
                email.get(
                    "attachments",
                    []
                )
            ) > 0
        )

        if (
            has_attachment
            != conditions["has_attachment"]
        ):
            return False

    # ========================================================
    # ATTACHMENT FILENAME
    # ========================================================

    if conditions.get(
        "attachment_filename"
    ):

        expected_filename = str(
            conditions[
                "attachment_filename"
            ]
        ).lower()

        found = False

        for attachment in email.get(
            "attachments",
            []
        ):

            filename = str(
                attachment.get(
                    "filename",
                    ""
                )
            ).lower()

            if expected_filename in filename:
                found = True
                break

        if not found:
            return False

    # ========================================================
    # ATTACHMENT TYPE
    # ========================================================

    if conditions.get(
        "attachment_type"
    ):

        expected_type = str(
            conditions[
                "attachment_type"
            ]
        ).lower()

        found = False

        for attachment in email.get(
            "attachments",
            []
        ):

            filename = str(
                attachment.get(
                    "filename",
                    ""
                )
            ).lower()

            mime_type = str(
                attachment.get(
                    "mime_type",
                    ""
                )
            ).lower()

            if (
                expected_type in filename
                or expected_type in mime_type
            ):
                found = True
                break

        if not found:
            return False

    # ========================================================
    # UNREAD
    # ========================================================

    if conditions.get(
        "is_unread"
    ) is not None:

        if (
            email.get(
                "is_unread",
                False
            )
            != conditions["is_unread"]
        ):
            return False

    # ========================================================
    # STARRED
    # ========================================================

    if conditions.get(
        "is_starred"
    ) is not None:

        if (
            email.get(
                "is_starred",
                False
            )
            != conditions["is_starred"]
        ):
            return False

    # ========================================================
    # GMAIL LABEL
    # ========================================================

    if conditions.get("label"):

        expected_label = str(
            conditions["label"]
        ).upper()

        labels = [
            str(label).upper()
            for label in email.get(
                "labels",
                []
            )
        ]

        if expected_label not in labels:
            return False

    # ========================================================
    # ALL CONDITIONS PASSED
    # ========================================================

    return True


# ============================================================
# FIND MATCHING RULES
# ============================================================

def find_matching_rules(
    email
):

    rules = load_rules()

    matches = []

    for rule in rules:

        if matches_rule(
            email,
            rule
        ):
            matches.append(rule)

    return matches