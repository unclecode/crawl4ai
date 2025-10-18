"""Content scraping service main application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from crawl4ai_core.config import get_settings

from .api import router

logger = logging.getLogger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Crawl4AI Content Scraping Service",
        description="Content scraping microservice for extracting data from HTML",
        version="0.1.0",
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
        return {"status": "healthy", "service": "content-scraping-service"}

    return app


def main():
    """Run the service."""
    import uvicorn

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    uvicorn.run(
        "content_scraping_service.main:create_app",
        factory=True,
        host=settings.api_host,
        port=8002,  # Different port for this service
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
