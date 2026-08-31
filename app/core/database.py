import sqlite3

from app.config import DATABASE_FILE


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


    # ========================================================
    # EMAILS
    # ========================================================

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


    # ========================================================
    # ATTACHMENTS
    # ========================================================

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


    # ========================================================
    # RULES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (

            id TEXT PRIMARY KEY,

            name TEXT NOT NULL,

            enabled INTEGER NOT NULL
                DEFAULT 1,

            mode TEXT NOT NULL
                DEFAULT 'CONDITIONAL',

            priority INTEGER NOT NULL
                DEFAULT 0,

            conditions TEXT NOT NULL
                DEFAULT '{}',

            actions TEXT NOT NULL
                DEFAULT '{}',

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # ========================================================
    # EMAIL ↔ RULE MATCHES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_rule_matches (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            email_id TEXT NOT NULL,

            rule_id TEXT NOT NULL,

            matched_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            UNIQUE (
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


    # ========================================================
    # ACTION EXECUTIONS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_executions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            email_id TEXT NOT NULL,

            rule_id TEXT NOT NULL,

            action TEXT NOT NULL,

            status TEXT NOT NULL,

            error TEXT,

            executed_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

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


    # ========================================================
    # OAUTH TOKENS
    #
    # Replaces:
    #
    #     token.json
    #
    # For now this is single-user.
    # Later we can add user_id.
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oauth_tokens (

            id INTEGER PRIMARY KEY CHECK (id = 1),

            token TEXT NOT NULL,

            refresh_token TEXT,

            token_uri TEXT,

            client_id TEXT,

            client_secret TEXT,

            scopes TEXT,

            expiry TEXT,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # ========================================================
    # GMAIL STATE
    #
    # Replaces:
    #
    #     state.json
    #
    # Stores Gmail Pub/Sub history state.
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gmail_state (

            id INTEGER PRIMARY KEY CHECK (id = 1),

            history_id TEXT,

            watch_expiration TEXT,

            updated_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # ========================================================
    # OAUTH PKCE SESSIONS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oauth_sessions (

            state TEXT PRIMARY KEY,

            code_verifier TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # ========================================================
    # PUB/SUB NOTIFICATION QUEUE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pubsub_queue (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            notification_key TEXT NOT NULL UNIQUE,

            notification TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'pending',

            attempts INTEGER NOT NULL DEFAULT 0,

            available_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

            last_error TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # ========================================================
    # PROCESSED GMAIL MESSAGES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_messages (

            message_id TEXT PRIMARY KEY,

            status TEXT NOT NULL,

            attempts INTEGER NOT NULL DEFAULT 1,

            last_error TEXT,

            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # ========================================================
    # COMMIT
    # ========================================================

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
