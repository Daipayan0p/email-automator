import json

from .database import get_connection


def load_token():
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT token, refresh_token, token_uri, client_id,
                   client_secret, scopes, expiry
            FROM oauth_tokens
            WHERE id = 1
            """
        ).fetchone()

        if row is None:
            return None

        token = dict(row)
        token["scopes"] = json.loads(token["scopes"] or "[]")
        return token
    finally:
        connection.close()


def save_token(token_data):
    connection = get_connection()

    try:
        scopes = token_data.get("scopes", [])
        if isinstance(scopes, str):
            scopes = json.loads(scopes)

        connection.execute(
            """
            INSERT INTO oauth_tokens (
                id, token, refresh_token, token_uri, client_id,
                client_secret, scopes, expiry, updated_at
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                token = excluded.token,
                refresh_token = COALESCE(excluded.refresh_token, oauth_tokens.refresh_token),
                token_uri = excluded.token_uri,
                client_id = excluded.client_id,
                client_secret = excluded.client_secret,
                scopes = excluded.scopes,
                expiry = excluded.expiry,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                token_data.get("token"),
                token_data.get("refresh_token"),
                token_data.get("token_uri"),
                token_data.get("client_id"),
                token_data.get("client_secret"),
                json.dumps(scopes),
                token_data.get("expiry"),
            ),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def delete_token():
    connection = get_connection()

    try:
        connection.execute("DELETE FROM oauth_tokens WHERE id = 1")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def save_oauth_session(state, code_verifier):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT OR REPLACE INTO oauth_sessions (state, code_verifier)
            VALUES (?, ?)
            """,
            (state, code_verifier),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def consume_oauth_session(state):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT code_verifier
            FROM oauth_sessions
            WHERE state = ?
            """,
            (state,),
        ).fetchone()

        if row is None:
            return None

        connection.execute(
            "DELETE FROM oauth_sessions WHERE state = ?",
            (state,),
        )
        connection.commit()
        return row["code_verifier"]
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def load_state():
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT history_id, watch_expiration
            FROM gmail_state
            WHERE id = 1
            """
        ).fetchone()

        return dict(row) if row else None
    finally:
        connection.close()


def load_history_id():
    state = load_state()
    return state.get("history_id") if state else None


def save_state(history_id, watch_expiration=None):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO gmail_state (id, history_id, watch_expiration, updated_at)
            VALUES (1, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                history_id = excluded.history_id,
                watch_expiration = excluded.watch_expiration,
                updated_at = CURRENT_TIMESTAMP
            """,
            (str(history_id), watch_expiration),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def migrate_files_to_db(token_file="token.json", state_file="state.json"):
    migrated = {"token": False, "state": False}

    try:
        with open(token_file, "r", encoding="utf-8") as file:
            save_token(json.load(file))
        migrated["token"] = True
    except FileNotFoundError:
        pass

    try:
        with open(state_file, "r", encoding="utf-8") as file:
            state = json.load(file)
        history_id = state.get("historyId")
        if history_id:
            save_state(history_id)
            migrated["state"] = True
    except FileNotFoundError:
        pass

    return migrated
