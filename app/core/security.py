import hmac
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import API_KEY, PUBSUB_TOKEN


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    if API_KEY is None:
        raise HTTPException(
            status_code=500,
            detail="API_KEY is not configured on the server.",
        )

    if not api_key or not hmac.compare_digest(api_key, API_KEY):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )


def verify_pubsub_token(token: Optional[str]):
    if PUBSUB_TOKEN is None:
        raise HTTPException(
            status_code=503,
            detail="PUBSUB_TOKEN is not configured on the server.",
        )

    if not token or not hmac.compare_digest(token, PUBSUB_TOKEN):
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing Pub/Sub token.",
        )
