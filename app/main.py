import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.errors import (
    http_exception_handler,
    unexpected_exception_handler,
    validation_exception_handler,
)
from app.db.session import SessionLocal
from app.routers import admin, ai, auth, demo, health, issues, locations, notifications, profile
from app.services.lifecycle import auto_close_resolved_issues


async def _auto_close_loop():
    if settings.database_url.startswith("sqlite"):
        return
    while True:
        db = SessionLocal()
        try:
            auto_close_resolved_issues(db)
        finally:
            db.close()
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_auto_close_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version="1.0.0",
    description="HostelFix hostel issue reporting API.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unexpected_exception_handler)


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if (
            request.method in {"POST", "PATCH", "PUT", "DELETE"}
            and not request.url.path.startswith(settings.api_prefix + "/auth/")
            and not (settings.environment != "production" and request.headers.get("X-User-Id"))
        ):
            cookie = request.cookies.get("hf_csrf")
            header = request.headers.get("X-CSRF-Token")
            if not cookie or cookie != header:
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    {"error": {"code": "CSRF_FAILED", "message": "CSRF validation failed"}},
                    status_code=403,
                )
        return await call_next(request)


app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    ai.router,
    health.router,
    locations.router,
    issues.router,
    notifications.router,
    admin.router,
    profile.router,
    demo.router,
):
    app.include_router(router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
def root():
    return {"name": settings.app_name, "docs": "/docs", "openapi": "/openapi.json"}
