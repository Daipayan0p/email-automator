import json
import os


# ============================================================
# PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

RULES_FILE = os.path.join(
    BASE_DIR,
    "rules.json"
)


# ============================================================
# LOAD RULES
# ============================================================

def load_rules():

    if not os.path.exists(RULES_FILE):
        return []

    try:

        with open(
            RULES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return []


# ============================================================
# SAVE RULES
# ============================================================

def save_rules(rules):

    with open(
        RULES_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            rules,
            file,
            indent=4
        )


# ============================================================
# CHECK TEXT CONDITION
# ============================================================

def text_matches(
    value,
    expected
):

    if not expected:
        return True

    if not value:
        return False

    return expected.lower() in value.lower()


# ============================================================
# CHECK ONE RULE
# ============================================================

def matches_rule(
    email,
    rule
):

    if not rule.get(
        "enabled",
        True
    ):

        return False

    mode = rule.get(
        "mode",
        "CONDITIONAL"
    )

    # --------------------------------------------------------
    # Rule that matches every email
    # --------------------------------------------------------

    if mode == "ALL_EMAILS":
        return True

    conditions = rule.get(
        "conditions",
        {}
    )

    # --------------------------------------------------------
    # Sender
    # --------------------------------------------------------

    if conditions.get("sender"):

        if not text_matches(
            email.get("sender", ""),
            conditions["sender"]
        ):

            return False

    # --------------------------------------------------------
    # Recipient
    # --------------------------------------------------------

    if conditions.get("recipient"):

        if not text_matches(
            email.get("recipient", ""),
            conditions["recipient"]
        ):

            return False

    # --------------------------------------------------------
    # Subject
    # --------------------------------------------------------

    if conditions.get("subject"):

        if not text_matches(
            email.get("subject", ""),
            conditions["subject"]
        ):

            return False

    # --------------------------------------------------------
    # Body
    # --------------------------------------------------------

    if conditions.get("body"):

        if not text_matches(
            email.get("body", ""),
            conditions["body"]
        ):

            return False

    # --------------------------------------------------------
    # General query
    #
    # This searches the email body.
    # Attachment searching is handled by the core engine.
    # --------------------------------------------------------

    if conditions.get("query"):

        query = conditions["query"].lower()

        body = email.get(
            "body",
            ""
        ).lower()

        subject = email.get(
            "subject",
            ""
        ).lower()

        sender = email.get(
            "sender",
            ""
        ).lower()

        if (
            query not in body
            and query not in subject
            and query not in sender
        ):

            return False

    # --------------------------------------------------------
    # Has attachment
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Attachment filename
    # --------------------------------------------------------

    if conditions.get(
        "attachment_filename"
    ):

        expected_filename = (
            conditions[
                "attachment_filename"
            ]
        ).lower()

        found = False

        for attachment in email.get(
            "attachments",
            []
        ):

            filename = attachment.get(
                "filename",
                ""
            ).lower()

            if expected_filename in filename:

                found = True
                break

        if not found:
            return False

    # --------------------------------------------------------
    # Attachment type
    # --------------------------------------------------------

    if conditions.get(
        "attachment_type"
    ):

        expected_type = (
            conditions[
                "attachment_type"
            ]
        ).lower()

        found = False

        for attachment in email.get(
            "attachments",
            []
        ):

            filename = attachment.get(
                "filename",
                ""
            ).lower()

            mime_type = attachment.get(
                "mime_type",
                ""
            ).lower()

            if (
                expected_type in filename
                or expected_type in mime_type
            ):

                found = True
                break

        if not found:
            return False

    # --------------------------------------------------------
    # Unread
    # --------------------------------------------------------

    if conditions.get(
        "is_unread"
    ) is not None:

        if (
            email.get("is_unread", False)
            != conditions["is_unread"]
        ):

            return False

    # --------------------------------------------------------
    # Starred
    # --------------------------------------------------------

    if conditions.get(
        "is_starred"
    ) is not None:

        if (
            email.get("is_starred", False)
            != conditions["is_starred"]
        ):

            return False

    # --------------------------------------------------------
    # Gmail label
    # --------------------------------------------------------

    if conditions.get("label"):

        expected_label = (
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

    # --------------------------------------------------------
    # All conditions passed
    # --------------------------------------------------------

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

            matches.append(
                rule
            )

    return matches