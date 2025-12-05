"""
FastAPI Application Entry Point
Council Planning Data API
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.storage.database import init_db

from .routes import applications, councils, search, webhooks, admin, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.api_title,
        description="""
# Council Planning Data API

Unified API for Australian council Development Application data.
Aggregates DAs from 200+ councils into a single, standardized format.

## Features

- **Search Applications**: Query development applications across all councils
- **Geo Search**: Find applications near a location
- **Council Stats**: Get statistics and metadata for each council
- **Webhooks**: Subscribe to new DA notifications
- **Real-time Data**: Updated multiple times daily

## Authentication

All endpoints require an API key passed via the `X-API-Key` header.

## Rate Limits

Rate limits vary by subscription tier:
- Free: 60 requests/minute, 1000/day
- Pro: 300 requests/minute, 10000/day
- Enterprise: Custom limits
        """,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(applications.router, prefix="/api/v1", tags=["Applications"])
    app.include_router(councils.router, prefix="/api/v1", tags=["Councils"])
    app.include_router(search.router, prefix="/api/v1", tags=["Search"])
    app.include_router(webhooks.router, prefix="/api/v1", tags=["Webhooks"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc) if settings.api_debug else "An error occurred",
            },
        )

    return app


app = create_app()


def run():
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )


if __name__ == "__main__":
    run()
