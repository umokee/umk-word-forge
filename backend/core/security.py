import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings

logger = logging.getLogger("wordforge.security")

PUBLIC_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Enforces X-API-Key header on all /api/ routes.

    If API_KEY env var is empty — all requests pass through (localhost mode).
    Failed attempts are logged with client IP for fail2ban integration.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if not settings.API_KEY:
            return await call_next(request)

        if path in PUBLIC_PATHS:
            return await call_next(request)

        if not path.startswith("/api/"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "")

        if api_key != settings.API_KEY:
            client_ip = _get_client_ip(request)
            logger.warning("Invalid API key attempt from %s path=%s", client_ip, path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Real-IP")
    if forwarded:
        return forwarded
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
