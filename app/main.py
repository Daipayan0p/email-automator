from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.auth_store import load_token
from app.core.database import init_database
from app.api.routes import router
from app.watch import start_gmail_watch
from app.api.auth_api import router as auth_router
from app.api.rules_api import router as rules_router
from app.api.actions_api import router as actions_router
from app.api.emails_api import router as emails_router


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print()
    print("=" * 60)
    print("EMAIL AUTOMATOR STARTING")
    print("=" * 60)

    try:

        init_database()

        watch_started = False
        if load_token():
            try:
                start_gmail_watch()
                watch_started = True
            except Exception as error:
                print()
                print("Gmail watch startup failed:")
                print(error)
                print("The API will continue running.")

        else:
            print("Gmail not authenticated. Visit /auth/google/login.")

        if watch_started:
            print()
            print("Gmail Pub/Sub watch started.")
        print("=" * 60)

        yield

    except Exception as e:

        print()
        print("❌ Gmail startup failed:")
        print(e)
        print("=" * 60)

        raise

    finally:

        print()
        print("=" * 60)
        print("EMAIL AUTOMATOR SHUTTING DOWN")
        print("=" * 60)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Email Automator API",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(router)
app.include_router(auth_router)
app.include_router(rules_router)
app.include_router(actions_router)
app.include_router(emails_router)
