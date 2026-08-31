from app.core.database import init_database
from app.repositories.email_repository import get_action_history


# ============================================================
# CONFIGURATION
# ============================================================

EMAIL_ID = "1a053d6143db6018"

# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_database()


# ============================================================
# GET ACTION HISTORY
# ============================================================

history = get_action_history(
    EMAIL_ID
)


# ============================================================
# PRINT HISTORY
# ============================================================

print()
print("=" * 60)
print("ACTION HISTORY")
print("=" * 60)

if not history:

    print("No action history found.")

else:

    for item in history:

        print()
        print(
            "Action:",
            item["action"]
        )

        print(
            "Rule:",
            item["rule_id"]
        )

        print(
            "Status:",
            item["status"]
        )

        print(
            "Error:",
            item["error"]
        )

        print(
            "Executed:",
            item["executed_at"]
        )

print()
print("=" * 60)
