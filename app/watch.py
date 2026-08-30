"""Compatibility entry point for the Gmail watch service."""

from app.services.gmail_watch import start_gmail_watch


if __name__ == "__main__":
    start_gmail_watch()
