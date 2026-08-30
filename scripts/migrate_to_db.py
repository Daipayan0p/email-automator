import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.auth_store import migrate_files_to_db
from app.core.database import init_database


if __name__ == "__main__":
    init_database()
    result = migrate_files_to_db()
    print("Token migrated:", result["token"])
    print("Gmail state migrated:", result["state"])
