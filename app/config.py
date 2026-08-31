import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_FILE = os.getenv(
    "DATABASE_FILE",
    os.path.join(BASE_DIR, "email_automator.db")
)
CREDENTIALS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_FILE",
    os.path.join(BASE_DIR, "credentials.json")
)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "email-automator-506819")
GMAIL_PUBSUB_TOPIC = os.getenv("GMAIL_PUBSUB_TOPIC", "gmail-notifications")
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI",
    "http://localhost:8080/auth/google/callback"
)

API_KEY = os.getenv("API_KEY")
PUBSUB_TOKEN = os.getenv("PUBSUB_TOKEN")
