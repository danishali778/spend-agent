from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import activity, analysis, cases, documents, health
from app.core.config import settings
from app.core.logging import configure_logging
from app.schemas.errors import ErrorResponse


def _error_response(status_code: int, *, code: str, message: str, details: dict | None = None) -> JSONResponse:
    payload = ErrorResponse(error={"code": code, "message": message, "details": details})
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(400, code="validation_error", message="Request validation failed", details={"errors": exc.errors()})

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
        return _error_response(400, code="bad_request", message=str(exc))

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict):
            return _error_response(exc.status_code, code=str(exc.detail.get("code", "http_error")), message=str(exc.detail.get("message", "Request failed")), details=exc.detail.get("details"))
        return _error_response(exc.status_code, code="http_error", message=str(exc.detail))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logging.getLogger("spendagent.backend").exception("Unhandled exception", exc_info=exc)
        return _error_response(500, code="internal_error", message="Internal server error")

    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(cases.router, prefix=settings.api_v1_prefix)
    app.include_router(documents.router, prefix=settings.api_v1_prefix)
    app.include_router(analysis.router, prefix=settings.api_v1_prefix)
    app.include_router(activity.router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
