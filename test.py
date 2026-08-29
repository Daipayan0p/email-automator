from app.core.gmail import get_gmail_service
from app.core.engine import process_email


service = get_gmail_service()


MESSAGE_ID = "1a04ec7f09e3f5d2"


result = process_email(
    service,
    MESSAGE_ID
)


print()
print("=" * 60)
print("RULE ENGINE RESULT")
print("=" * 60)

print(
    "Matched:",
    result["matched"]
)

print(
    "Email:",
    result["email"]["subject"]
)

print(
    "Matching rules:"
)

for rule in result["matching_rules"]:

    print(
        f"  ✓ {rule['name']}"
    )

print("=" * 60)