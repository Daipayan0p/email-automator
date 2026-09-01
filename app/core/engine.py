# ============================================================
# EMAIL PROCESSING ENGINE
# ============================================================

from .search import (
    fetch_email,
    analyze_email
)

from .rules import (
    load_rules,
    matches_rule,
    get_rule_priority
)

from .attachments import (
    search_attachments
)

from .actions import (
    execute_actions
)
from ..utils.telegram import send_telegram_notification

# ============================================================
# ACTION CONFLICT GROUPS
# ============================================================

# Actions in the same group conflict with each other.
#
# Example:
#
# mark_as_read
# mark_as_unread
#
# Only the highest-priority rule gets to decide.

CONFLICT_GROUPS = {

    "read_state": {
        "mark_as_read",
        "mark_as_unread"
    },

    "star_state": {
        "star",
        "unstar"
    },

    "inbox_state": {
        "archive",
        "keep_in_inbox"
    }
}


# ============================================================
# GET CONFLICT GROUP
# ============================================================

def get_conflict_group(
    action_name
):

    for group_name, actions in CONFLICT_GROUPS.items():

        if action_name in actions:
            return group_name

    return None


# ============================================================
# RESOLVE ACTION CONFLICTS
# ============================================================

def resolve_action_conflicts(
    matching_rules
):

    """
    Resolve conflicts between matching rules.

    Rules are sorted by priority.

    Higher priority wins only when two actions
    belong to the same conflict group.

    Non-conflicting actions are preserved.
    """

    # --------------------------------------------------------
    # Highest priority first
    # --------------------------------------------------------

    sorted_rules = sorted(
        matching_rules,
        key=get_rule_priority,
        reverse=True
    )

    selected_actions = []

    claimed_conflicts = set()

    # --------------------------------------------------------
    # Process each rule
    # --------------------------------------------------------

    for rule in sorted_rules:

        actions = rule.get(
            "actions",
            {}
        )

        if not isinstance(
            actions,
            dict
        ):
            continue

        priority = get_rule_priority(
            rule
        )

        rule_id = rule.get(
            "id"
        )

        rule_name = rule.get(
            "name",
            ""
        )

        # ----------------------------------------------------
        # Process every action
        # ----------------------------------------------------

        for action_name, action_value in actions.items():

            # ------------------------------------------------
            # Ignore disabled actions
            # ------------------------------------------------

            if not action_value:
                continue

            # Telegram is a notification setting, not a Gmail action.
            if action_name == "telegram_alert":
                continue

            # ------------------------------------------------
            # Label actions are always additive
            # ------------------------------------------------

            if action_name == "add_label":

                selected_actions.append({
                    "rule": rule,
                    "action": action_name,
                    "value": action_value,
                    "priority": priority
                })

                continue

            # ------------------------------------------------
            # Find conflict group
            # ------------------------------------------------

            conflict_group = get_conflict_group(
                action_name
            )

            # ------------------------------------------------
            # Non-conflicting action
            # ------------------------------------------------

            if conflict_group is None:

                selected_actions.append({
                    "rule": rule,
                    "action": action_name,
                    "value": action_value,
                    "priority": priority
                })

                continue

            # ------------------------------------------------
            # Conflicting action
            # ------------------------------------------------

            if conflict_group in claimed_conflicts:

                print(
                    f"⚠️ CONFLICT SKIPPED: "
                    f"{rule_name} -> {action_name} "
                    f"(priority {priority})"
                )

                continue

            # ------------------------------------------------
            # Highest-priority action wins
            # ------------------------------------------------

            claimed_conflicts.add(
                conflict_group
            )

            selected_actions.append({
                "rule": rule,
                "action": action_name,
                "value": action_value,
                "priority": priority
            })

    return selected_actions


# ============================================================
# PROCESS ONE EMAIL
# ============================================================

def process_email(
    service,
    message_id,
    query=None
):

    # ========================================================
    # FETCH EMAIL
    # ========================================================

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
                analysis["attachment_results"],

            "matching_rules":
                [],

            "actions":
                []
        }


    # ========================================================
    # AUTOMATIC RULE MODE
    # ========================================================

    rules = load_rules()

    matching_rules = []

    attachment_results = []

    body_match = False


    # ========================================================
    # CHECK EVERY RULE
    # ========================================================

    for rule in rules:

        # ----------------------------------------------------
        # Check normal conditions
        # ----------------------------------------------------

        if not matches_rule(
            email,
            rule,
            include_query=False
        ):
            continue

        conditions = rule.get(
            "conditions",
            {}
        )

        rule_query = conditions.get(
            "query"
        )


        # ====================================================
        # QUERY SEARCH
        # ====================================================

        if rule_query:

            query_lower = str(
                rule_query
            ).lower()


            # ------------------------------------------------
            # Search email content
            # ------------------------------------------------

            searchable_text = " ".join([
                str(email.get("sender", "")),
                str(email.get("recipient", "")),
                str(email.get("cc", "")),
                str(email.get("bcc", "")),
                str(email.get("subject", "")),
                str(email.get("body", "")),
                str(email.get("snippet", ""))
            ]).lower()


            current_body_match = (
                query_lower
                in searchable_text
            )


            # ------------------------------------------------
            # Search attachments
            # ------------------------------------------------

            current_attachment_results = (
                search_attachments(
                    service,
                    email["id"],
                    email["payload"],
                    rule_query
                )
            )


            current_attachment_match = (
                len(
                    current_attachment_results
                ) > 0
            )


            # ------------------------------------------------
            # Query not found
            # ------------------------------------------------

            if (
                not current_body_match
                and
                not current_attachment_match
            ):
                continue


            if current_body_match:

                body_match = True


            # ------------------------------------------------
            # Add unique attachment results
            # ------------------------------------------------

            for result in current_attachment_results:

                if result not in attachment_results:

                    attachment_results.append(
                        result
                    )


        # ====================================================
        # RULE MATCHED
        # ====================================================

        matching_rules.append(
            rule
        )


    # ========================================================
    # SORT RULES BY PRIORITY
    # ========================================================

    matching_rules.sort(
        key=get_rule_priority,
        reverse=True
    )


    # ========================================================
    # FINAL MATCH
    # ========================================================

    matched = (
        len(matching_rules) > 0
    )


    # ========================================================
    # RESOLVE ACTION CONFLICTS
    # ========================================================

    selected_actions = []

    telegram_enabled = any(
        rule.get("actions", {}).get("telegram_alert", False)
        for rule in matching_rules
        if isinstance(rule.get("actions", {}), dict)
    )

    if matched:

        selected_actions = resolve_action_conflicts(
            matching_rules
        )


    # ========================================================
    # EXECUTE SELECTED ACTIONS
    # ========================================================

    action_results = []

    saved = False


    for selected in selected_actions:

        rule = selected["rule"]

        action_name = selected["action"]

        priority = selected["priority"]


        # ----------------------------------------------------
        # Build a temporary rule containing ONLY this action
        # ----------------------------------------------------

        action_rule = dict(
            rule
        )

        action_rule["actions"] = {
            action_name:
                selected["value"]
        }


        print()
        print(
            "=" * 50
        )

        print(
            "EXECUTING ACTION"
        )

        print(
            "Rule:",
            rule.get(
                "name",
                ""
            )
        )

        print(
            "Priority:",
            priority
        )

        print(
            "Action:",
            action_name
        )

        print(
            "=" * 50
        )


        try:

            executed_actions = (
                execute_actions(
                    service,
                    email,
                    action_rule
                )
            )


            for action_result in executed_actions:

                action_results.append({

                    "rule_id":
                        rule.get(
                            "id"
                        ),

                    "rule_name":
                        rule.get(
                            "name",
                            ""
                        ),

                    "priority":
                        priority,

                    "action":
                        action_result.get(
                            "action"
                        ),

                    "result":
                        action_result

                })


                # ------------------------------------------------
                # Correct save status
                # ------------------------------------------------

                if (
                    action_result.get(
                        "action"
                    ) == "save"
                    and
                    action_result.get(
                        "success"
                    ) is True
                ):

                    saved = True


        except Exception as e:

            print()
            print(
                "❌ ACTION FAILED"
            )

            print(
                "Rule:",
                rule.get(
                    "name",
                    ""
                )
            )

            print(
                "Action:",
                action_name
            )

            print(
                "Error:",
                str(e)
            )


            action_results.append({

                "rule_id":
                    rule.get(
                        "id"
                    ),

                "rule_name":
                    rule.get(
                        "name",
                        ""
                    ),

                "priority":
                    priority,

                "action":
                    action_name,

                "result": {

                    "action":
                        action_name,

                    "success":
                        False,

                    "error":
                        str(e)

                }

            })

    # ========================================================
# TELEGRAM NOTIFICATION
# ========================================================

    if matched and telegram_enabled:

        rule_names = [
            rule.get("name", "Unnamed Rule")
            for rule in matching_rules
        ]

        send_telegram_notification(
            subject=email.get(
                "subject",
                "No Subject"
            ),
            sender=email.get(
                "sender",
                ""
            ),
            rule_names=rule_names
        )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "matched":
            matched,

        "saved":
            saved,

        "email":
            email,

        "body_match":
            body_match,

        "attachment_match":
            len(
                attachment_results
            ) > 0,

        "attachment_results":
            attachment_results,

        "matching_rules":
            matching_rules,

        "actions":
            action_results

    }
