from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.gmail import get_gmail_service
from app.core.engine import process_email
from app.core.query_builder import build_gmail_query
from app.core.pubsub import decode_pubsub_message, validate_notification
from app.core.queue import enqueue_notification
from app.services.pubsub_worker import wake_pubsub_worker

router = APIRouter()


# ============================================================
# SEARCH REQUEST
# ============================================================

class SearchRequest(BaseModel):

    # --------------------------------------------------------
    # Free-text search
    # --------------------------------------------------------

    query: Optional[str] = None

    # --------------------------------------------------------
    # Date range
    # --------------------------------------------------------

    from_date: Optional[str] = None

    to_date: Optional[str] = None

    # --------------------------------------------------------
    # People
    # --------------------------------------------------------

    sender: Optional[str] = None

    recipient: Optional[str] = None

    # --------------------------------------------------------
    # Subject
    # --------------------------------------------------------

    subject: Optional[str] = None

    # --------------------------------------------------------
    # Attachments
    # --------------------------------------------------------

    has_attachment: Optional[bool] = None

    # --------------------------------------------------------
    # Read / unread
    # --------------------------------------------------------

    is_unread: Optional[bool] = None

    # --------------------------------------------------------
    # Starred
    # --------------------------------------------------------

    is_starred: Optional[bool] = None

    # --------------------------------------------------------
    # Gmail labels
    # --------------------------------------------------------

    label: Optional[str] = None

    # --------------------------------------------------------
    # Gmail folder
    # --------------------------------------------------------

    folder: Optional[str] = None

    # --------------------------------------------------------
    # Email size
    # --------------------------------------------------------

    larger_than: Optional[int] = Field(
        default=None,
        ge=0
    )

    smaller_than: Optional[int] = Field(
        default=None,
        ge=0
    )

    # --------------------------------------------------------
    # Advanced Gmail query
    # --------------------------------------------------------

    raw_query: Optional[str] = None

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

    max_results: int = Field(
        default=50,
        ge=1,
        le=500
    )

    page_token: Optional[str] = None


# ============================================================
# HEALTH CHECK
# ============================================================

@router.get("/health")
def health():

    return {
        "status": "ok"
    }


# ============================================================
# GET SINGLE EMAIL
# ============================================================

@router.get("/emails/{message_id}")
def get_email(
    message_id: str
):

    try:

        service = get_gmail_service()

        result = process_email(
            service,
            message_id
        )

        email = result["email"]

        return {

            "id":
                email["id"],

            "thread_id":
                email["thread_id"],

            "sender":
                email["sender"],

            "recipient":
                email["recipient"],

            "cc":
                email["cc"],

            "bcc":
                email["bcc"],

            "subject":
                email["subject"],

            "date":
                email["date"],

            "snippet":
                email["snippet"],

            "labels":
                email["labels"],

            "is_unread":
                email["is_unread"],

            "is_starred":
                email["is_starred"],

            "attachments":
                email["attachments"],

            "body":
                email["body"]

        }

    except Exception as e:

        if "not authenticated" in str(e).lower():
            raise HTTPException(
                status_code=401,
                detail="Gmail not authenticated. Call GET /auth/google/login first."
            )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# SEARCH EMAILS
# ============================================================

@router.post("/search")
def search_emails(
    request: SearchRequest
):

    try:

        # ====================================================
        # BUILD GMAIL QUERY
        # ====================================================

        gmail_query = build_gmail_query(

            query=request.query,

            from_date=request.from_date,

            to_date=request.to_date,

            sender=request.sender,

            recipient=request.recipient,

            subject=request.subject,

            has_attachment=request.has_attachment,

            is_unread=request.is_unread,

            is_starred=request.is_starred,

            label=request.label,

            folder=request.folder,

            larger_than=request.larger_than,

            smaller_than=request.smaller_than,

            raw_query=request.raw_query

        )

        # ====================================================
        # CONNECT TO GMAIL
        # ====================================================

        service = get_gmail_service()

        # ====================================================
        # BUILD GMAIL API REQUEST
        # ====================================================

        search_request = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=gmail_query,
                maxResults=request.max_results
            )
        )

        # ====================================================
        # PAGINATION
        # ====================================================

        if request.page_token:

            search_request = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    q=gmail_query,
                    maxResults=request.max_results,
                    pageToken=request.page_token
                )
            )

        # ====================================================
        # EXECUTE GMAIL SEARCH
        # ====================================================

        response = search_request.execute()

        messages = response.get(
            "messages",
            []
        )

        # ====================================================
        # PROCESS EMAILS
        # ====================================================

        results = []

        for message in messages:

            # ------------------------------------------------
            # Central engine handles fetching + analysis
            # ------------------------------------------------

            result = process_email(

                service,

                message["id"],

                request.query

            )

            email = result["email"]

            matched = result["matched"]

            body_match = result[
                "body_match"
            ]

            attachment_match = result[
                "attachment_match"
            ]

            attachment_results = result[
                "attachment_results"
            ]

            # ------------------------------------------------
            # Add only matching emails
            # ------------------------------------------------

            if matched:

                results.append({

                    "id":
                        email["id"],

                    "thread_id":
                        email["thread_id"],

                    "sender":
                        email["sender"],

                    "recipient":
                        email["recipient"],

                    "cc":
                        email["cc"],

                    "bcc":
                        email["bcc"],

                    "subject":
                        email["subject"],

                    "date":
                        email["date"],

                    "snippet":
                        email["snippet"],

                    "labels":
                        email["labels"],

                    "is_unread":
                        email["is_unread"],

                    "is_starred":
                        email["is_starred"],

                    "attachments":
                        email["attachments"],

                    "body_match":
                        body_match,

                    "attachment_match":
                        attachment_match,

                    "attachment_results":
                        attachment_results

                })

        # ====================================================
        # PAGINATION TOKEN
        # ====================================================

        next_page_token = response.get(
            "nextPageToken"
        )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {

            "gmail_query":
                gmail_query,

            "count":
                len(results),

            "next_page_token":
                next_page_token,

            "results":
                results

        }

    except Exception as e:

        if "not authenticated" in str(e).lower():
            raise HTTPException(
                status_code=401,
                detail="Gmail not authenticated. Call GET /auth/google/login first."
            )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/pubsub")
async def pubsub_webhook(
    body: dict
):

    try:
        notification = decode_pubsub_message(body)
        validate_notification(notification)
        queued = enqueue_notification(body, notification)
        wake_pubsub_worker()

        return {
            "status": "ok",
            "queued": queued
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Pub/Sub notification: {e}"
        )
