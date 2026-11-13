import logging
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_payload(code: str, message: str, details=None):
    return {"error": {"code": code, "message": message, "details": details}}


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = {
        400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND",
        409: "CONFLICT", 422: "VALIDATION_ERROR", 429: "RATE_LIMITED", 503: "SERVICE_UNAVAILABLE",
        504: "UPSTREAM_TIMEOUT",
    }.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
    return JSONResponse(status_code=exc.status_code, content=error_payload(code, message))


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for item in exc.errors():
        location = [str(part) for part in item.get("loc", []) if part not in ("body", "query", "path")]
        details.append({
            "field": ".".join(location) or "request",
            "message": item.get("msg", "Invalid value"),
        })
    message = details[0]["message"] if len(details) == 1 else "Please correct the highlighted fields."
    return JSONResponse(status_code=422, content=error_payload("VALIDATION_ERROR", message, details))


async def unexpected_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).error(
        "Unhandled API exception", exc_info=(type(exc), exc, exc.__traceback__)
    )
    return JSONResponse(
        status_code=500,
        content=error_payload("INTERNAL_SERVER_ERROR", "An unexpected error occurred."),
    )
