"""
Application Configuration Settings
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/council_da"
    database_url_sync: str = "postgresql://postgres:password@localhost:5432/council_da"
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # -------------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # -------------------------------------------------------------------------
    # API
    # -------------------------------------------------------------------------
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    api_secret_key: str = "change-me-in-production"
    api_rate_limit_per_minute: int = 60
    api_title: str = "Council Planning Data API"
    api_version: str = "1.0.0"

    # -------------------------------------------------------------------------
    # Supabase (for GNAF geocoding)
    # -------------------------------------------------------------------------
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    gnaf_table_name: str = "gnaf_addresses"

    # -------------------------------------------------------------------------
    # AI Services
    # -------------------------------------------------------------------------
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # -------------------------------------------------------------------------
    # Geocoding
    # -------------------------------------------------------------------------
    google_maps_api_key: Optional[str] = None
    geocoding_provider_priority: str = "gnaf_supabase,nominatim"  # Comma-separated

    # -------------------------------------------------------------------------
    # Scraping
    # -------------------------------------------------------------------------
    scraper_rate_limit_seconds: float = 1.0
    scraper_timeout_seconds: int = 30
    scraper_max_retries: int = 3
    scraper_headless: bool = True
    scraper_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # -------------------------------------------------------------------------
    # Proxy
    # -------------------------------------------------------------------------
    proxy_enabled: bool = False
    proxy_datacenter_url: Optional[str] = None
    proxy_residential_url: Optional[str] = None
    proxy_brightdata_url: Optional[str] = None

    # -------------------------------------------------------------------------
    # Storage
    # -------------------------------------------------------------------------
    raw_data_path: str = "./data/raw"
    processed_data_path: str = "./data/processed"
    cache_path: str = "./data/cache"
    mappings_cache_path: str = "./data/cache/mappings_cache.json"

    # -------------------------------------------------------------------------
    # Monitoring
    # -------------------------------------------------------------------------
    log_level: str = "INFO"
    sentry_dsn: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
