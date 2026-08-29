import sqlite3
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

DATABASE_FILE = os.path.join(
    BASE_DIR,
    "email_automator.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_database():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Emails
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (

            id TEXT PRIMARY KEY,

            thread_id TEXT,

            sender TEXT,

            recipient TEXT,

            cc TEXT,

            bcc TEXT,

            subject TEXT,

            date TEXT,

            body TEXT,

            snippet TEXT,

            labels TEXT,

            is_unread INTEGER,

            is_starred INTEGER,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # Attachments
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attachments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            email_id TEXT NOT NULL,

            filename TEXT,

            mime_type TEXT,

            size INTEGER,

            attachment_id TEXT,

            FOREIGN KEY (
                email_id
            )
            REFERENCES emails(id)
        )
    """)

    # --------------------------------------------------------
    # Rules
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (

            id TEXT PRIMARY KEY,

            name TEXT,

            enabled INTEGER,

            mode TEXT,

            conditions TEXT,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # Email ↔ Rule matches
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_rule_matches (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            email_id TEXT NOT NULL,

            rule_id TEXT NOT NULL,

            matched_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(
                email_id,
                rule_id
            ),

            FOREIGN KEY (
                email_id
            )
            REFERENCES emails(id),

            FOREIGN KEY (
                rule_id
            )
            REFERENCES rules(id)
        )
    """)

    connection.commit()

    connection.close()


# ============================================================
# STARTUP
# ============================================================

if __name__ == "__main__":

    init_database()

    print(
        "Database initialized:"
    )

    print(
        DATABASE_FILE
    )