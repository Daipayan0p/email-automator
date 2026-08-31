from fastapi import APIRouter, Depends, HTTPException

from app.repositories.email_repository import get_action_history
from app.core.security import verify_api_key


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/actions",
    tags=["Action History"],
    dependencies=[Depends(verify_api_key)]
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
