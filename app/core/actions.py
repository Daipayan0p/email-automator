# ============================================================
# ACTION ENGINE
# ============================================================

from .repository import save_email_result


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

        try:

            saved = save_email_result(
                email,
                [rule]
            )

            print(
                "💾 SAVE:",
                "SUCCESS" if saved else "ALREADY EXISTS"
            )

            results.append({
                "action": "save",
                "success": True,
                "already_exists": not saved
            })

        except Exception as e:

            print(
                "❌ SAVE FAILED:",
                str(e)
            )

            results.append({
                "action": "save",
                "success": False,
                "error": str(e)
            })


    # ========================================================
    # NOTIFY
    # ========================================================

    if actions.get(
        "notify",
        False
    ):

        try:

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

            results.append({
                "action": "notify",
                "success": True
            })

        except Exception as e:

            print(
                "❌ NOTIFY FAILED:",
                str(e)
            )

            results.append({
                "action": "notify",
                "success": False,
                "error": str(e)
            })


    # ========================================================
    # MARK AS READ
    # ========================================================

    if actions.get(
        "mark_as_read",
        False
    ):

        try:

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "removeLabelIds": [
                        "UNREAD"
                    ]
                }
            ).execute()

            print(
                "📖 MARK AS READ: SUCCESS"
            )

            results.append({
                "action": "mark_as_read",
                "success": True
            })

        except Exception as e:

            print(
                "❌ MARK AS READ FAILED:",
                str(e)
            )

            results.append({
                "action": "mark_as_read",
                "success": False,
                "error": str(e)
            })


    # ========================================================
    # MARK AS UNREAD
    # ========================================================

    if actions.get(
        "mark_as_unread",
        False
    ):

        try:

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "addLabelIds": [
                        "UNREAD"
                    ]
                }
            ).execute()

            print(
                "📕 MARK AS UNREAD: SUCCESS"
            )

            results.append({
                "action": "mark_as_unread",
                "success": True
            })

        except Exception as e:

            print(
                "❌ MARK AS UNREAD FAILED:",
                str(e)
            )

            results.append({
                "action": "mark_as_unread",
                "success": False,
                "error": str(e)
            })


    # ========================================================
    # STAR
    # ========================================================

    if actions.get(
        "star",
        False
    ):

        try:

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "addLabelIds": [
                        "STARRED"
                    ]
                }
            ).execute()

            print(
                "⭐ STAR: SUCCESS"
            )

            results.append({
                "action": "star",
                "success": True
            })

        except Exception as e:

            print(
                "❌ STAR FAILED:",
                str(e)
            )

            results.append({
                "action": "star",
                "success": False,
                "error": str(e)
            })


    # ========================================================
    # UNSTAR
    # ========================================================

    if actions.get(
        "unstar",
        False
    ):

        try:

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "removeLabelIds": [
                        "STARRED"
                    ]
                }
            ).execute()

            print(
                "☆ UNSTAR: SUCCESS"
            )

            results.append({
                "action": "unstar",
                "success": True
            })

        except Exception as e:

            print(
                "❌ UNSTAR FAILED:",
                str(e)
            )

            results.append({
                "action": "unstar",
                "success": False,
                "error": str(e)
            })


    # ========================================================
    # ARCHIVE
    # ========================================================

    if actions.get(
        "archive",
        False
    ):

        try:

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "removeLabelIds": [
                        "INBOX"
                    ]
                }
            ).execute()

            print(
                "📥 ARCHIVE: SUCCESS"
            )

            results.append({
                "action": "archive",
                "success": True
            })

        except Exception as e:

            print(
                "❌ ARCHIVE FAILED:",
                str(e)
            )

            results.append({
                "action": "archive",
                "success": False,
                "error": str(e)
            })


    # ========================================================
    # KEEP IN INBOX
    # ========================================================

    if actions.get(
        "keep_in_inbox",
        False
    ):

        try:

            service.users().messages().modify(
                userId="me",
                id=email["id"],
                body={
                    "addLabelIds": [
                        "INBOX"
                    ]
                }
            ).execute()

            print(
                "📨 KEEP IN INBOX: SUCCESS"
            )

            results.append({
                "action": "keep_in_inbox",
                "success": True
            })

        except Exception as e:

            print(
                "❌ KEEP IN INBOX FAILED:",
                str(e)
            )

            results.append({
                "action": "keep_in_inbox",
                "success": False,
                "error": str(e)
            })


    # ========================================================
    # ADD LABEL
    # ========================================================

    label_name = actions.get(
        "add_label"
    )

    if label_name:

        try:

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

            print(
                f"🏷️ LABEL '{label_name}': SUCCESS"
            )

            results.append({
                "action": "add_label",
                "label": label_name,
                "success": True
            })

        except Exception as e:

            print(
                f"❌ ADD LABEL FAILED: {e}"
            )

            results.append({
                "action": "add_label",
                "label": label_name,
                "success": False,
                "error": str(e)
            })


    # ========================================================
    # RETURN RESULTS
    # ========================================================

    return results