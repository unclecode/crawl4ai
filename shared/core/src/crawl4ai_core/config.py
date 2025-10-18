"""Configuration management for Crawl4AI services."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Service configuration
    service_name: str = "crawl4ai-service"
    service_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Redis configuration
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_max_connections: int = 10

    # RabbitMQ configuration
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # Browser configuration
    browser_service_url: str = "http://localhost:8001"

    # Content scraping configuration
    scraping_service_url: str = "http://localhost:8002"

    # Extraction configuration
    extraction_service_url: str = "http://localhost:8003"

    # Filtering configuration
    filtering_service_url: str = "http://localhost:8004"

    # Database configuration
    database_url: Optional[str] = None

    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"

    # CORS configuration
    cors_origins: list[str] = ["*"]
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    # Security
    secret_key: str = "change-me-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
