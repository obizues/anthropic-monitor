from __future__ import annotations

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from config.loader import get_secrets

_UNPROTECTED = {"/health", "/unsubscribe"}


async def verify_api_key(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
    if request.url.path in _UNPROTECTED or request.url.path.startswith("/docs"):
        return await call_next(request)
    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if key != get_secrets().config_api_key:
        return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
    return await call_next(request)
