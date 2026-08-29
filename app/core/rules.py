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

    return expected.lower() in str(value).lower()


# ============================================================
# CHECK ONE RULE
# ============================================================

def matches_rule(
    email,
    rule
):

    # --------------------------------------------------------
    # Disabled rule
    # --------------------------------------------------------

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
    # Match every email
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
    # CC
    # --------------------------------------------------------

    if conditions.get("cc"):

        if not text_matches(
            email.get("cc", ""),
            conditions["cc"]
        ):
            return False

    # --------------------------------------------------------
    # BCC
    # --------------------------------------------------------

    if conditions.get("bcc"):

        if not text_matches(
            email.get("bcc", ""),
            conditions["bcc"]
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
    # This checks:
    #   sender
    #   recipient
    #   subject
    #   body
    #
    # Attachment CONTENT is checked by engine.py
    # because rules.py doesn't have Gmail service access.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Attachment type
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Unread
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Starred
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Gmail label
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # All metadata conditions passed
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

            matches.append(rule)

    return matches