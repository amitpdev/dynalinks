import logging
import secrets

from fastapi import HTTPException, Request, status

from app.config import settings

logger = logging.getLogger(__name__)

_API_KEY_HEADER = "X-API-Key"
_WARNED_UNSET = False


async def require_api_key(request: Request) -> None:
    """Enforce X-API-Key on admin endpoints.

    If settings.api_key is unset, the check is skipped — this is the rollout
    mode. A one-time warning is logged so the open state is visible in logs.
    Remove that branch once all callers send the header.
    """
    global _WARNED_UNSET
    if not settings.api_key:
        if not _WARNED_UNSET:
            logger.warning(
                "API_KEY is not set; admin endpoints are unauthenticated"
            )
            _WARNED_UNSET = True
        return

    provided = request.headers.get(_API_KEY_HEADER)
    if not provided or not secrets.compare_digest(provided, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": _API_KEY_HEADER},
        )
