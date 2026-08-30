from app.core.gmail import get_gmail_service
from app.core.engine import process_email
from app.core.database import init_database
from app.core.repository import get_email_by_id


# ============================================================
# CONFIGURATION
# ============================================================

MESSAGE_ID = "1a0531b895fc6cd4"


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_database()


# ============================================================
# CONNECT TO GMAIL
# ============================================================

service = get_gmail_service()


# ============================================================
# PROCESS EMAIL
# ============================================================

result = process_email(
    service,
    MESSAGE_ID
)


# ============================================================
# PRINT ENGINE RESULT
# ============================================================

print()
print("=" * 60)
print("RULE ENGINE RESULT")
print("=" * 60)

print(
    "Matched:",
    result["matched"]
)

print(
    "Saved:",
    result["saved"]
)

print(
    "Email:",
    result["email"]["subject"]
)

print()
print("Matching rules:")

for rule in result["matching_rules"]:

    print(
        f"  ✓ {rule['name']}"
    )

print()
print(
    "Attachments:",
    len(
        result["email"].get(
            "attachments",
            []
        )
    )
)

print("=" * 60)


# ============================================================
# CHECK DATABASE
# ============================================================

print()
print("=" * 60)
print("DATABASE CHECK")
print("=" * 60)

saved_email = get_email_by_id(
    MESSAGE_ID
)

if saved_email:

    print("✓ Email found in database")

    print(
        "  Subject:",
        saved_email["subject"]
    )

    print(
        "  Sender:",
        saved_email["sender"]
    )

else:

    print(
        "✗ Email NOT found in database"
    )

print("=" * 60)