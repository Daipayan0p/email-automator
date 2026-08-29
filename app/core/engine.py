from .search import (
    fetch_email,
    analyze_email
)

from .rules import (
    load_rules,
    matches_rule
)

from .attachments import (
    search_attachments
)

from .result_store import (
    save_match
)


# ============================================================
# CHECK RULE
# ============================================================

def rule_matches_email(
    service,
    email,
    rule
):

    # --------------------------------------------------------
    # Check normal conditions
    # --------------------------------------------------------

    if not matches_rule(
        email,
        rule
    ):
        return False, [], False

    conditions = rule.get(
        "conditions",
        {}
    )

    query = conditions.get(
        "query"
    )

    attachment_results = []

    body_match = False

    # --------------------------------------------------------
    # Search query
    # --------------------------------------------------------

    if query:

        query_lower = str(
            query
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

        body_match = (
            query_lower in searchable_text
        )

        # ----------------------------------------------------
        # Search attachments
        # ----------------------------------------------------

        attachment_results = search_attachments(
            service,
            email["id"],
            email["payload"],
            query
        )

        attachment_match = (
            len(attachment_results) > 0
        )

        # ----------------------------------------------------
        # Query must exist somewhere
        # ----------------------------------------------------

        if (
            not body_match
            and not attachment_match
        ):
            return False, [], False

    # --------------------------------------------------------
    # Rule matched
    # --------------------------------------------------------

    return (
        True,
        attachment_results,
        body_match
    )


# ============================================================
# PROCESS ONE EMAIL
# ============================================================

def process_email(
    service,
    message_id,
    query=None
):

    # --------------------------------------------------------
    # Fetch email
    # --------------------------------------------------------

    email = fetch_email(
        service,
        message_id
    )

    # ========================================================
    # MANUAL SEARCH MODE
    # ========================================================

    if query:

        analysis = analyze_email(
            service,
            email,
            query
        )

        return {

            "matched":
                analysis["matched"],

            "saved":
                False,

            "email":
                email,

            "body_match":
                analysis["body_match"],

            "attachment_match":
                analysis["attachment_match"],

            "attachment_results":
                analysis[
                    "attachment_results"
                ],

            "matching_rules":
                []

        }

    # ========================================================
    # AUTOMATIC RULE MODE
    # ========================================================

    rules = load_rules()

    matching_rules = []

    all_attachment_results = []

    overall_body_match = False

    # --------------------------------------------------------
    # Check every rule
    # --------------------------------------------------------

    for rule in rules:

        (
            matched,
            attachment_results,
            body_match
        ) = rule_matches_email(
            service,
            email,
            rule
        )

        if matched:

            matching_rules.append(
                rule
            )

            all_attachment_results.extend(
                attachment_results
            )

            if body_match:

                overall_body_match = True

    # --------------------------------------------------------
    # Overall match
    # --------------------------------------------------------

    matched = (
        len(matching_rules) > 0
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    saved = False

    if matched:

        saved = save_match(
            email=email,
            matching_rules=matching_rules,
            attachment_results=all_attachment_results,
            body_match=overall_body_match
        )

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "matched":
            matched,

        "saved":
            saved,

        "email":
            email,

        "body_match":
            overall_body_match,

        "attachment_match":
            len(
                all_attachment_results
            ) > 0,

        "attachment_results":
            all_attachment_results,

        "matching_rules":
            matching_rules

    }