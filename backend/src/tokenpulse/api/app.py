"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from tokenpulse import __version__
from tokenpulse.api.routers import meta, teams, trends
from tokenpulse.logging import configure_logging, get_logger

log = get_logger("tokenpulse.api")


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="TokenPulse Backend API", version=__version__)

    app.include_router(meta.router)
    app.include_router(teams.router)
    app.include_router(trends.router)

    @app.exception_handler(ValueError)
    async def _value_error(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(LookupError)
    async def _lookup_error(_request: Request, exc: LookupError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    return app


app = create_app()
