"""Browser service main application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from crawl4ai_core.config import get_settings

from .api import router
from .browser_manager import BrowserManager

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Browser Service...")
    app.state.browser_manager = BrowserManager()
    await app.state.browser_manager.start()
    logger.info("Browser Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Browser Service...")
    await app.state.browser_manager.stop()
    logger.info("Browser Service stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Crawl4AI Browser Service",
        description="Browser management microservice for web scraping",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Include API router
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "service": "browser-service"}

    return app


def main():
    """Run the service."""
    import uvicorn

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    uvicorn.run(
        "browser_service.main:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
