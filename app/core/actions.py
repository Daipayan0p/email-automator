# ============================================================
# ACTION ENGINE
# ============================================================

from .repository import (
    save_email_result,
    log_action_execution
)


# ============================================================
# FIND OR CREATE GMAIL LABEL
# ============================================================

def get_or_create_label(
    service,
    label_name
):

    labels_response = (
        service.users()
        .labels()
        .list(
            userId="me"
        )
        .execute()
    )

    labels = labels_response.get(
        "labels",
        []
    )

    # --------------------------------------------------------
    # Find existing label
    # --------------------------------------------------------

    for label in labels:

        if (
            label.get("name", "").lower()
            == str(label_name).lower()
        ):

            return label.get("id")

    # --------------------------------------------------------
    # Create label
    # --------------------------------------------------------

    created_label = (
        service.users()
        .labels()
        .create(
            userId="me",
            body={
                "name": label_name
            }
        )
        .execute()
    )

    return created_label.get("id")


# ============================================================
# RUN ONE ACTION
# ============================================================

def run_action(
    email,
    rule,
    action_name,
    function
):

    try:

        # ----------------------------------------------------
        # Execute actual action
        # ----------------------------------------------------

        function()

        # ----------------------------------------------------
        # Log success
        # ----------------------------------------------------

        log_action_execution(
            email["id"],
            rule.get("id"),
            action_name,
            "SUCCESS"
        )

        print(
            f"✅ {action_name}: SUCCESS"
        )

        return {
            "action": action_name,
            "success": True
        }

    except Exception as e:

        # ----------------------------------------------------
        # Log failure
        # ----------------------------------------------------

        try:

            log_action_execution(
                email["id"],
                rule.get("id"),
                action_name,
                "FAILED",
                str(e)
            )

        except Exception as log_error:

            print(
                "⚠️ Failed to log action error:",
                log_error
            )

        print(
            f"❌ {action_name}: FAILED - {e}"
        )

        return {
            "action": action_name,
            "success": False,
            "error": str(e)
        }


# ============================================================
# EXECUTE ACTIONS
# ============================================================

def execute_actions(
    service,
    email,
    rule
):

    actions = rule.get(
        "actions",
        {}
    )

    results = []


    # ========================================================
    # SAVE
    # ========================================================

    if actions.get(
        "save",
        False
    ):

        def save():

            saved = save_email_result(
                email,
                [rule]
            )

            print(
                "💾 SAVE:",
                "NEW EMAIL SAVED"
                if saved
                else "ALREADY EXISTS"
            )

        result = run_action(
            email,
            rule,
            "save",
            save
        )

        results.append(result)


    # ========================================================
    # NOTIFY
    # ========================================================

    if actions.get(
        "notify",
        False
    ):

        def notify():

            print()
            print("=" * 50)
            print("🔔 EMAIL NOTIFICATION")
            print("=" * 50)

            print(
                "Rule:",
                rule.get(
                    "name",
                    ""
                )
            )

            print(
                "Priority:",
                rule.get(
                    "priority",
                    0
                )
            )

            print(
                "From:",
                email.get(
                    "sender",
                    ""
                )
            )

            print(
                "Subject:",
                email.get(
                    "subject",
                    ""
                )
            )

            print("=" * 50)

        result = run_action(
            email,
            rule,
            "notify",
            notify
        )

        results.append(result)


    # ========================================================
    # MARK AS READ
    # ========================================================

    if actions.get(
        "mark_as_read",
        False
    ):

        def mark_as_read():

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "removeLabelIds": [
                        "UNREAD"
                    ]
                }
            ).execute()

        result = run_action(
            email,
            rule,
            "mark_as_read",
            mark_as_read
        )

        results.append(result)


    # ========================================================
    # MARK AS UNREAD
    # ========================================================

    if actions.get(
        "mark_as_unread",
        False
    ):

        def mark_as_unread():

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "addLabelIds": [
                        "UNREAD"
                    ]
                }
            ).execute()

        result = run_action(
            email,
            rule,
            "mark_as_unread",
            mark_as_unread
        )

        results.append(result)


    # ========================================================
    # STAR
    # ========================================================

    if actions.get(
        "star",
        False
    ):

        def star():

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "addLabelIds": [
                        "STARRED"
                    ]
                }
            ).execute()

        result = run_action(
            email,
            rule,
            "star",
            star
        )

        results.append(result)


    # ========================================================
    # UNSTAR
    # ========================================================

    if actions.get(
        "unstar",
        False
    ):

        def unstar():

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "removeLabelIds": [
                        "STARRED"
                    ]
                }
            ).execute()

        result = run_action(
            email,
            rule,
            "unstar",
            unstar
        )

        results.append(result)


    # ========================================================
    # ARCHIVE
    # ========================================================

    if actions.get(
        "archive",
        False
    ):

        def archive():

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "removeLabelIds": [
                        "INBOX"
                    ]
                }
            ).execute()

        result = run_action(
            email,
            rule,
            "archive",
            archive
        )

        results.append(result)


    # ========================================================
    # KEEP IN INBOX
    # ========================================================

    if actions.get(
        "keep_in_inbox",
        False
    ):

        def keep_in_inbox():

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "addLabelIds": [
                        "INBOX"
                    ]
                }
            ).execute()

        result = run_action(
            email,
            rule,
            "keep_in_inbox",
            keep_in_inbox
        )

        results.append(result)


    # ========================================================
    # ADD LABEL
    # ========================================================

    label_name = actions.get(
        "add_label"
    )

    if label_name:

        def add_label():

            label_id = get_or_create_label(
                service,
                label_name
            )

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "addLabelIds": [
                        label_id
                    ]
                }
            ).execute()

        result = run_action(
            email,
            rule,
            "add_label",
            add_label
        )

        # Add label name to result
        result["label"] = label_name

        results.append(result)


    # ========================================================
    # RETURN RESULTS
    # ========================================================

    return results