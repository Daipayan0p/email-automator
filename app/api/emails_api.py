from fastapi import APIRouter, Depends, HTTPException

from app.repositories.email_repository import (
    get_all_emails,
    get_email_by_id,
    delete_email

)
from app.core.security import verify_api_key


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/emails",
    tags=["Emails"],
    dependencies=[Depends(verify_api_key)]
)


# ============================================================
# GET ALL EMAILS
# ============================================================

@router.get("/")
def get_emails():

    emails = get_all_emails()

    return {
        "count": len(emails),
        "emails": emails
    }


# ============================================================
# GET EMAIL BY ID
# ============================================================

@router.get("/{email_id}")
def get_email(email_id: str):

    email = get_email_by_id(
        email_id
    )

    if email is None:

        raise HTTPException(
            status_code=404,
            detail="Email not found"
        )

    return email

# ============================================================
# DELETE EMAIL
# ============================================================

@router.delete("/{email_id}")
def delete_email_endpoint(email_id: str):

    deleted = delete_email(
        email_id
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Email not found"
        )

    return {
        "message": "Email deleted successfully",
        "email_id": email_id
    }
