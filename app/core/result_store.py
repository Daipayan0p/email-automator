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

RESULT_FILE = os.path.join(
    BASE_DIR,
    "results.json"
)


# ============================================================
# LOAD RESULTS
# ============================================================

def load_results():

    if not os.path.exists(RESULT_FILE):
        return []

    try:

        with open(
            RESULT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

        return data.get(
            "results",
            []
        )

    except Exception:

        return []


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(results):

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            {
                "results": results
            },
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# SAVE MATCH
# ============================================================

def save_match(
    email,
    matching_rules,
    attachment_results=None,
    body_match=False
):

    if attachment_results is None:
        attachment_results = []

    results = load_results()

    # --------------------------------------------------------
    # Prevent duplicate emails
    # --------------------------------------------------------

    for existing in results:

        if existing.get(
            "id"
        ) == email.get("id"):

            return False

    # --------------------------------------------------------
    # Build result
    # --------------------------------------------------------

    result = {

        "id":
            email.get("id"),

        "thread_id":
            email.get("thread_id"),

        "sender":
            email.get("sender", ""),

        "recipient":
            email.get("recipient", ""),

        "cc":
            email.get("cc", ""),

        "bcc":
            email.get("bcc", ""),

        "subject":
            email.get("subject", ""),

        "date":
            email.get("date", ""),

        "snippet":
            email.get("snippet", ""),

        "labels":
            email.get("labels", []),

        "is_unread":
            email.get(
                "is_unread",
                False
            ),

        "is_starred":
            email.get(
                "is_starred",
                False
            ),

        "attachments":
            email.get(
                "attachments",
                []
            ),

        "body_match":
            body_match,

        "attachment_match":
            len(
                attachment_results
            ) > 0,

        "attachment_results":
            attachment_results,

        "matching_rules": [

            {
                "id":
                    rule.get("id"),

                "name":
                    rule.get("name")

            }

            for rule in matching_rules

        ]

    }

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    results.append(result)

    save_results(results)

    return True