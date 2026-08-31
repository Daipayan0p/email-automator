import threading
from google.auth.exceptions import TransportError
from requests.exceptions import RequestException

from app.core.pubsub import process_notification
from app.core.queue import (
    claim_next_notification,
    complete_notification,
    fail_notification,
    recover_stale_notifications,
    retry_notification,
)
from googleapiclient.errors import HttpError


MAX_ATTEMPTS = 5
_stop_event = threading.Event()
_wake_event = threading.Event()
_worker = None


def is_retryable_error(error):
    if isinstance(error, HttpError):
        return error.resp.status in {403, 429, 500, 502, 503, 504}

    status = getattr(getattr(error, "response", None), "status_code", None)
    if status is not None:
        return status in {408, 429, 500, 502, 503, 504}

    return isinstance(
        error,
        (
            TimeoutError,
            ConnectionError,
            OSError,
            TransportError,
            RequestException,
        )
    )


def _run():
    while not _stop_event.is_set():
        job = claim_next_notification()
        if job is None:
            _wake_event.wait(1)
            _wake_event.clear()
            continue

        try:
            process_notification(job["notification"])
            complete_notification(job["id"])
        except Exception as error:
            if is_retryable_error(error) and job["attempts"] < MAX_ATTEMPTS:
                delay = 2 ** (job["attempts"] - 1)
                retry_notification(job["id"], error, delay)
            else:
                fail_notification(job["id"], error)


def start_pubsub_worker():
    global _worker
    if _worker and _worker.is_alive():
        return

    recover_stale_notifications()
    _stop_event.clear()
    _worker = threading.Thread(
        target=_run,
        name="pubsub-worker",
        daemon=True,
    )
    _worker.start()


def wake_pubsub_worker():
    _wake_event.set()


def stop_pubsub_worker():
    _stop_event.set()
    _wake_event.set()
    if _worker and _worker.is_alive():
        _worker.join(timeout=5)
