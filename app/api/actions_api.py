from fastapi import APIRouter, HTTPException

from app.repositories.email_repository import get_action_history


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/actions",
    tags=["Action History"]
)


# ============================================================
# GET ACTION HISTORY FOR EMAIL
# ============================================================

@router.get("/email/{email_id}")
def get_email_action_history(email_id: str):

    history = get_action_history(email_id)

    return {
        "email_id": email_id,
        "count": len(history),
        "actions": history
    }
