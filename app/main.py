from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.watch import start_gmail_watch
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

        start_gmail_watch()

        print()
        print("✅ Gmail Pub/Sub watch started.")
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
app.include_router(rules_router)
app.include_router(actions_router)
app.include_router(emails_router)