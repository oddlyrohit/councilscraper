"""
Base Council Adapter Interface
All council scrapers must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, AsyncIterator
import asyncio
import logging

from src.config import settings
from src.config.councils import CouncilConfig


logger = logging.getLogger(__name__)


class ScrapeMode(str, Enum):
    """Scraping mode."""
    ACTIVE = "active"  # Current/recent applications
    HISTORICAL = "historical"  # Historical backfill


@dataclass
class PortalHealth:
    """Portal health status."""
    is_healthy: bool
    message: str = ""
    response_time_ms: Optional[int] = None
    last_checked: datetime = field(default_factory=datetime.utcnow)
    error_type: Optional[str] = None


@dataclass
class RawRecord:
    """Raw scraped record."""
    data: dict
    source_url: str
    scraped_at: datetime = field(default_factory=datetime.utcnow)


class CouncilAdapter(ABC):
    """
    Abstract base class for council scrapers.
    Each council portal type or individual council implements this interface.
    """

    def __init__(self, council_config: CouncilConfig):
        """
        Initialize the adapter.

        Args:
            council_config: Council configuration
        """
        self.config = council_config
        self.council_code = council_config.code
        self.portal_url = council_config.portal_url or ""
        self.rate_limit = settings.scraper_rate_limit_seconds
        self.timeout = settings.scraper_timeout_seconds
        self.max_retries = settings.scraper_max_retries
        self._last_request_time: Optional[datetime] = None

    @property
    def name(self) -> str:
        """Get adapter name."""
        return f"{self.__class__.__name__}({self.council_code})"

    # -------------------------------------------------------------------------
    # Abstract Methods - Must be implemented by subclasses
    # -------------------------------------------------------------------------

    @abstractmethod
    async def scrape_active(self) -> list[RawRecord]:
        """
        Scrape currently active development applications.
        These are applications that are:
        - Recently lodged
        - Under assessment
        - On exhibition
        - Recently determined

        Returns:
            List of raw scraped records
        """
        pass

    @abstractmethod
    async def scrape_historical(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[RawRecord]:
        """
        Scrape historical development applications.

        Args:
            start_date: Start of date range (defaults to 1 year ago)
            end_date: End of date range (defaults to today)

        Returns:
            List of raw scraped records
        """
        pass

    @abstractmethod
    async def get_portal_status(self) -> PortalHealth:
        """
        Check if the council portal is accessible and healthy.

        Returns:
            PortalHealth status
        """
        pass

    # -------------------------------------------------------------------------
    # Optional Methods - Can be overridden by subclasses
    # -------------------------------------------------------------------------

    async def scrape_application(self, da_number: str) -> Optional[RawRecord]:
        """
        Scrape a single application by DA number.
        Override this for portals that support direct lookup.

        Args:
            da_number: Development application number

        Returns:
            Raw record or None if not found
        """
        raise NotImplementedError(
            f"{self.name} does not support single application lookup"
        )

    async def scrape_paginated(
        self,
        mode: ScrapeMode = ScrapeMode.ACTIVE,
    ) -> AsyncIterator[RawRecord]:
        """
        Scrape with pagination, yielding records as they're found.
        Override for memory-efficient scraping of large result sets.

        Args:
            mode: Scraping mode (active or historical)

        Yields:
            Raw records one at a time
        """
        if mode == ScrapeMode.ACTIVE:
            records = await self.scrape_active()
        else:
            records = await self.scrape_historical()

        for record in records:
            yield record

    def get_search_url(self, **params) -> str:
        """
        Build search URL with parameters.
        Override to customize URL building.

        Args:
            **params: Search parameters

        Returns:
            Full URL string
        """
        return self.portal_url

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self._last_request_time:
            elapsed = (datetime.utcnow() - self._last_request_time).total_seconds()
            if elapsed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - elapsed)
        self._last_request_time = datetime.utcnow()

    async def _retry_with_backoff(
        self,
        coro,
        max_retries: Optional[int] = None,
        base_delay: float = 1.0,
    ):
        """
        Retry a coroutine with exponential backoff.

        Args:
            coro: Coroutine to retry
            max_retries: Maximum retry attempts
            base_delay: Base delay between retries

        Returns:
            Result of the coroutine
        """
        max_retries = max_retries or self.max_retries
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return await coro
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"{self.name}: Attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{self.name}: All {max_retries + 1} attempts failed")

        raise last_error

    def _create_record(self, data: dict, source_url: str) -> RawRecord:
        """Create a RawRecord from scraped data."""
        return RawRecord(
            data=data,
            source_url=source_url,
            scraped_at=datetime.utcnow(),
        )

    def _log_scrape_start(self, mode: ScrapeMode) -> None:
        """Log scrape operation start."""
        logger.info(f"{self.name}: Starting {mode.value} scrape")

    def _log_scrape_complete(self, mode: ScrapeMode, count: int) -> None:
        """Log scrape operation completion."""
        logger.info(f"{self.name}: Completed {mode.value} scrape - {count} records")

    def _log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log an error."""
        if error:
            logger.error(f"{self.name}: {message} - {error}")
        else:
            logger.error(f"{self.name}: {message}")


class MultiCouncilAdapter(CouncilAdapter):
    """
    Base class for adapters that handle multiple councils with the same portal type.
    Examples: NSW ePlanning (many NSW councils), VIC SPEAR (many VIC councils)
    """

    # Subclasses should define which councils this adapter supports
    SUPPORTED_COUNCILS: list[str] = []

    @classmethod
    def supports_council(cls, council_code: str) -> bool:
        """Check if this adapter supports a given council."""
        return council_code in cls.SUPPORTED_COUNCILS

    @classmethod
    def get_supported_councils(cls) -> list[str]:
        """Get list of supported council codes."""
        return cls.SUPPORTED_COUNCILS
