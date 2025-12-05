"""
Northern Territory Planning Scraper
NT has a centralized development application tracking system.
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import logging

from src.config.councils import CouncilConfig
from src.scrapers.base.adapter import CouncilAdapter, PortalHealth, RawRecord, ScrapeMode
from src.scrapers.base.browser import BrowserManager


logger = logging.getLogger(__name__)


class NTPlanningAdapter(CouncilAdapter):
    """Scraper for Northern Territory planning applications."""

    PORTAL_URL = "https://www.ntlis.nt.gov.au/planning/"

    def __init__(self, council_config: CouncilConfig):
        super().__init__(council_config)
        self.portal_url = self.PORTAL_URL

    async def get_portal_status(self) -> PortalHealth:
        """Check portal accessibility."""
        start_time = datetime.utcnow()
        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.portal_url)
                    response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    return PortalHealth(is_healthy=True, response_time_ms=response_time)
        except Exception as e:
            return PortalHealth(is_healthy=False, message=str(e), error_type=type(e).__name__)

    async def scrape_active(self) -> list[RawRecord]:
        """Scrape active applications."""
        self._log_scrape_start(ScrapeMode.ACTIVE)
        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.portal_url)
                    await asyncio.sleep(2)
                    records = await self._extract_results(page, browser)

        except Exception as e:
            self._log_error("Failed to scrape active applications", e)

        self._log_scrape_complete(ScrapeMode.ACTIVE, len(records))
        return records

    async def scrape_historical(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> list[RawRecord]:
        """Scrape historical applications."""
        self._log_scrape_start(ScrapeMode.HISTORICAL)
        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.portal_url)
                    await asyncio.sleep(2)
                    records = await self._extract_results(page, browser)

        except Exception as e:
            self._log_error("Failed to scrape historical applications", e)

        self._log_scrape_complete(ScrapeMode.HISTORICAL, len(records))
        return records

    async def _extract_results(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Extract results from NT planning portal."""
        records = []

        try:
            await browser.wait_for_selector(page, "table, .results", timeout=10000)
            table_data = await browser.get_table_data(page, "table")

            for row in table_data:
                if row.get("Application Number") or row.get("Address"):
                    records.append(self._create_record(data=row, source_url=page.url))

        except Exception as e:
            logger.error(f"Failed to extract NT results: {e}")

        return records
