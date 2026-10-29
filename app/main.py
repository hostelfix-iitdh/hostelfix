from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.errors import http_exception_handler, validation_exception_handler, unexpected_exception_handler
from app.routers import health, locations, issues, notifications, admin

app = FastAPI(title=settings.app_name, version="1.0.0",
              description="HostelFix hostel issue reporting API. Authentication is development-only in MS-3.",
              docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
                   allow_methods=["GET","POST","PATCH","DELETE","OPTIONS"], allow_headers=["*"])
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unexpected_exception_handler)
for router in (health.router, locations.router, issues.router, notifications.router, admin.router):
    app.include_router(router, prefix=settings.api_prefix)

@app.get("/", include_in_schema=False)
def root():
    return {"name": settings.app_name, "docs": "/docs", "openapi": "/openapi.json"}
