"""
Queensland Development.i Portal Scraper
Handles councils using the QLD Development.i system.
Covers many Queensland councils through a centralized portal.
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import logging

from src.config.councils import CouncilConfig
from src.scrapers.base.adapter import CouncilAdapter, PortalHealth, RawRecord, ScrapeMode
from src.scrapers.base.browser import BrowserManager


logger = logging.getLogger(__name__)


# Development.i portal
DEVELOPMENT_I_BASE = "https://developmenti.dsdip.qld.gov.au"


# QLD council mapping to Development.i identifiers
QLD_COUNCIL_MAP = {
    "GOLD_COAST": "Gold Coast",
    "MORETON_BAY": "Moreton Bay",
    "LOGAN": "Logan",
    "SUNSHINE_COAST": "Sunshine Coast",
    "IPSWICH": "Ipswich",
    "TOWNSVILLE": "Townsville",
    "TOOWOOMBA": "Toowoomba",
    "CAIRNS": "Cairns",
    "REDLAND": "Redland",
    "MACKAY": "Mackay",
    "FRASER_COAST": "Fraser Coast",
    "BUNDABERG": "Bundaberg",
    "ROCKHAMPTON": "Rockhampton",
    "GLADSTONE": "Gladstone",
    "NOOSA": "Noosa",
    "GYMPIE": "Gympie",
    "SCENIC_RIM": "Scenic Rim",
    "LOCKYER_VALLEY": "Lockyer Valley",
    "LIVINGSTONE": "Livingstone",
    "WESTERN_DOWNS": "Western Downs",
    "SOUTH_BURNETT": "South Burnett",
    "CENTRAL_HIGHLANDS": "Central Highlands",
    "CASSOWARY_COAST": "Cassowary Coast",
    "SOMERSET": "Somerset",
    "TABLELANDS": "Tablelands",
    "ISAAC": "Isaac",
    "BURDEKIN": "Burdekin",
}


class QLDDevelopmentIAdapter(CouncilAdapter):
    """
    Scraper for Queensland's Development.i portal.
    Covers many QLD councils through a single scraper.
    """

    SUPPORTED_COUNCILS = list(QLD_COUNCIL_MAP.keys())

    def __init__(self, council_config: CouncilConfig):
        super().__init__(council_config)
        self.portal_url = DEVELOPMENT_I_BASE
        self.council_name = QLD_COUNCIL_MAP.get(council_config.code)

    async def get_portal_status(self) -> PortalHealth:
        """Check if Development.i portal is accessible."""
        start_time = datetime.utcnow()

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, f"{self.portal_url}/public-search")

                    if await browser.wait_for_selector(page, "form, .search, input", timeout=15000):
                        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        return PortalHealth(
                            is_healthy=True,
                            message="Development.i portal accessible",
                            response_time_ms=response_time,
                        )

                    return PortalHealth(
                        is_healthy=False,
                        message="Development.i portal form not found",
                    )

        except Exception as e:
            return PortalHealth(
                is_healthy=False,
                message=str(e),
                error_type=type(e).__name__,
            )

    async def scrape_active(self) -> list[RawRecord]:
        """Scrape active development applications from Development.i."""
        self._log_scrape_start(ScrapeMode.ACTIVE)

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    search_url = f"{self.portal_url}/public-search"
                    await browser.goto(page, search_url)
                    await asyncio.sleep(2)

                    # Select council
                    if self.council_name:
                        await self._select_council(page)

                    # Set date range
                    end_date = date.today()
                    start_date = end_date - timedelta(days=90)
                    await self._set_date_range(page, start_date, end_date)

                    # Search for applications in assessment
                    await self._select_status(page, "In Assessment")
                    await self._submit_search(page)

                    in_assessment = await self._extract_results(page, browser)
                    records.extend(in_assessment)

                    # Also get recently decided
                    await browser.goto(page, search_url)
                    await asyncio.sleep(2)

                    if self.council_name:
                        await self._select_council(page)

                    recent_start = end_date - timedelta(days=30)
                    await self._set_date_range(page, recent_start, end_date)
                    await self._select_status(page, "Decision Made")
                    await self._submit_search(page)

                    decided = await self._extract_results(page, browser)
                    records.extend(decided)

        except Exception as e:
            self._log_error("Failed to scrape active applications", e)

        self._log_scrape_complete(ScrapeMode.ACTIVE, len(records))
        return records

    async def scrape_historical(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[RawRecord]:
        """Scrape historical development applications."""
        self._log_scrape_start(ScrapeMode.HISTORICAL)

        if not start_date:
            start_date = date.today() - timedelta(days=365)
        if not end_date:
            end_date = date.today()

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    search_url = f"{self.portal_url}/public-search"
                    await browser.goto(page, search_url)
                    await asyncio.sleep(2)

                    if self.council_name:
                        await self._select_council(page)

                    await self._set_date_range(page, start_date, end_date)
                    await self._submit_search(page)

                    records = await self._scrape_all_pages(page, browser)

        except Exception as e:
            self._log_error("Failed to scrape historical applications", e)

        self._log_scrape_complete(ScrapeMode.HISTORICAL, len(records))
        return records

    async def _select_council(self, page) -> None:
        """Select council in search form."""
        selectors = [
            "select[name*='council']",
            "select[name*='lga']",
            "#council",
            ".council-select",
        ]

        for selector in selectors:
            try:
                await page.select_option(selector, label=self.council_name)
                await asyncio.sleep(0.5)
                return
            except Exception:
                continue

    async def _set_date_range(self, page, start_date: date, end_date: date) -> None:
        """Set date range in search form."""
        date_format = "%d/%m/%Y"

        start_selectors = ["#dateFrom", "input[name*='from']", "input[name*='start']"]
        end_selectors = ["#dateTo", "input[name*='to']", "input[name*='end']"]

        for selector in start_selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    await el.fill(start_date.strftime(date_format))
                    break
            except Exception:
                continue

        for selector in end_selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    await el.fill(end_date.strftime(date_format))
                    break
            except Exception:
                continue

    async def _select_status(self, page, status: str) -> None:
        """Select application status."""
        selectors = ["#status", "select[name*='status']"]

        for selector in selectors:
            try:
                await page.select_option(selector, label=status)
                return
            except Exception:
                continue

    async def _submit_search(self, page) -> None:
        """Submit search form."""
        selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "#search",
            ".search-btn",
        ]

        for selector in selectors:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    await asyncio.sleep(3)
                    return
            except Exception:
                continue

    async def _extract_results(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Extract search results."""
        records = []

        try:
            await browser.wait_for_selector(page, "table, .results")

            table_data = await browser.get_table_data(page, "table")

            for row in table_data:
                record_data = self._map_development_i_row(row)
                if record_data.get("da_number") or record_data.get("address"):
                    records.append(self._create_record(
                        data=record_data,
                        source_url=page.url,
                    ))

        except Exception as e:
            logger.error(f"Failed to extract Development.i results: {e}")

        return records

    def _map_development_i_row(self, row: dict) -> dict:
        """Map Development.i table row to schema."""
        mapping = {
            "Application Number": "da_number",
            "Application Reference": "da_number",
            "Reference Number": "da_number",
            "Property Address": "address",
            "Site Address": "address",
            "Address": "address",
            "Description": "description",
            "Proposal Description": "description",
            "Development Description": "description",
            "Status": "status",
            "Application Status": "status",
            "Stage": "status",
            "Lodgement Date": "lodged_date",
            "Date Lodged": "lodged_date",
            "Decision Date": "determined_date",
            "Decision": "decision",
            "Outcome": "decision",
            "Estimated Cost": "estimated_cost",
            "Value": "estimated_cost",
            "Council": "council_name",
            "Local Government": "council_name",
        }

        result = {}
        for header, value in row.items():
            normalized = header.strip()
            if normalized in mapping:
                result[mapping[normalized]] = value
            else:
                result[normalized] = value

        return result

    async def _scrape_all_pages(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Scrape all pages with pagination."""
        all_records = []
        page_num = 1

        while True:
            records = await self._extract_results(page, browser)
            if not records:
                break

            all_records.extend(records)

            next_link = await page.query_selector(
                ".next:not(.disabled), a:has-text('Next')"
            )

            if next_link:
                await next_link.click()
                await asyncio.sleep(2)
                page_num += 1
            else:
                break

            if page_num > 100:
                break

        return all_records
