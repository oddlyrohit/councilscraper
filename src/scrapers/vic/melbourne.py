"""
City of Melbourne Scraper
Custom scraper for Melbourne's planning applications portal.
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import logging

from src.config.councils import CouncilConfig
from src.scrapers.base.adapter import CouncilAdapter, PortalHealth, RawRecord, ScrapeMode
from src.scrapers.base.browser import BrowserManager


logger = logging.getLogger(__name__)


class MelbourneCityAdapter(CouncilAdapter):
    """
    Scraper for City of Melbourne's planning applications.
    Melbourne uses a Civica-based system with its own portal.
    """

    PORTAL_URL = "https://www.melbourne.vic.gov.au/building-and-development/property-information/planning-building-registers/Pages/search-planning-register.aspx"

    def __init__(self, council_config: CouncilConfig):
        super().__init__(council_config)
        self.portal_url = self.PORTAL_URL

    async def get_portal_status(self) -> PortalHealth:
        """Check if Melbourne's planning portal is accessible."""
        start_time = datetime.utcnow()

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.portal_url)

                    if await browser.wait_for_selector(page, "form, .search, input", timeout=15000):
                        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        return PortalHealth(
                            is_healthy=True,
                            message="Melbourne portal accessible",
                            response_time_ms=response_time,
                        )

                    return PortalHealth(
                        is_healthy=False,
                        message="Melbourne portal form not found",
                    )

        except Exception as e:
            return PortalHealth(
                is_healthy=False,
                message=str(e),
                error_type=type(e).__name__,
            )

    async def scrape_active(self) -> list[RawRecord]:
        """Scrape active planning applications from Melbourne."""
        self._log_scrape_start(ScrapeMode.ACTIVE)

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.portal_url)
                    await asyncio.sleep(2)

                    # Set search parameters for recent applications
                    end_date = date.today()
                    start_date = end_date - timedelta(days=90)

                    # Melbourne portal typically has date inputs
                    await self._set_date_range(page, start_date, end_date)

                    # Submit search
                    await self._submit_search(page)
                    await asyncio.sleep(3)

                    # Extract results
                    records = await self._extract_results(page, browser)

        except Exception as e:
            self._log_error("Failed to scrape active applications", e)

        self._log_scrape_complete(ScrapeMode.ACTIVE, len(records))
        return records

    async def scrape_historical(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[RawRecord]:
        """Scrape historical planning applications from Melbourne."""
        self._log_scrape_start(ScrapeMode.HISTORICAL)

        if not start_date:
            start_date = date.today() - timedelta(days=365)
        if not end_date:
            end_date = date.today()

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.portal_url)
                    await asyncio.sleep(2)

                    await self._set_date_range(page, start_date, end_date)
                    await self._submit_search(page)
                    await asyncio.sleep(3)

                    # Handle pagination
                    records = await self._scrape_all_pages(page, browser)

        except Exception as e:
            self._log_error("Failed to scrape historical applications", e)

        self._log_scrape_complete(ScrapeMode.HISTORICAL, len(records))
        return records

    async def _set_date_range(self, page, start_date: date, end_date: date) -> None:
        """Set date range in search form."""
        date_format = "%d/%m/%Y"

        # Try various selector patterns
        start_selectors = [
            "input[name*='fromDate']",
            "input[name*='startDate']",
            "input[id*='from']",
            "#dateFrom",
        ]

        end_selectors = [
            "input[name*='toDate']",
            "input[name*='endDate']",
            "input[id*='to']",
            "#dateTo",
        ]

        for selector in start_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await element.fill(start_date.strftime(date_format))
                    break
            except Exception:
                continue

        for selector in end_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await element.fill(end_date.strftime(date_format))
                    break
            except Exception:
                continue

    async def _submit_search(self, page) -> None:
        """Submit the search form."""
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            ".search-btn",
            "#searchButton",
            "button:has-text('Search')",
        ]

        for selector in submit_selectors:
            try:
                button = await page.query_selector(selector)
                if button:
                    await button.click()
                    return
            except Exception:
                continue

    async def _extract_results(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Extract planning application results."""
        records = []

        try:
            await browser.wait_for_selector(page, "table, .results, .applications-list")

            # Try table extraction
            table_data = await browser.get_table_data(page, "table")

            for row in table_data:
                record_data = self._map_melbourne_row(row)
                if record_data.get("da_number") or record_data.get("address"):
                    records.append(self._create_record(
                        data=record_data,
                        source_url=page.url,
                    ))

            # Alternative: list-based results
            if not records:
                items = await page.query_selector_all(".application-item, .result-item")
                for item in items:
                    data = await self._parse_item(item)
                    if data.get("da_number"):
                        records.append(self._create_record(
                            data=data,
                            source_url=page.url,
                        ))

        except Exception as e:
            logger.error(f"Failed to extract Melbourne results: {e}")

        return records

    def _map_melbourne_row(self, row: dict) -> dict:
        """Map Melbourne table row to our schema."""
        mapping = {
            "Application Number": "da_number",
            "Application No": "da_number",
            "Permit Number": "da_number",
            "Address": "address",
            "Property": "address",
            "Location": "address",
            "Description": "description",
            "Proposal": "description",
            "Status": "status",
            "Current Status": "status",
            "Decision": "decision",
            "Date Lodged": "lodged_date",
            "Lodged": "lodged_date",
            "Decision Date": "determined_date",
            "Cost": "estimated_cost",
        }

        result = {}
        for header, value in row.items():
            normalized = header.strip()
            if normalized in mapping:
                result[mapping[normalized]] = value
            else:
                result[normalized] = value

        return result

    async def _parse_item(self, item) -> dict:
        """Parse a single result item element."""
        data = {}

        field_selectors = [
            ("da_number", ".app-number, .permit-number, .reference"),
            ("address", ".address, .location, .property"),
            ("description", ".description, .proposal"),
            ("status", ".status"),
        ]

        for field_name, selector in field_selectors:
            try:
                element = await item.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        data[field_name] = text.strip()
            except Exception:
                continue

        return data

    async def _scrape_all_pages(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Scrape all pages with pagination."""
        all_records = []
        page_num = 1

        while True:
            records = await self._extract_results(page, browser)
            if not records:
                break

            all_records.extend(records)

            # Look for next page
            next_link = await page.query_selector(
                "a.next, .pagination .next, a:has-text('Next'), a:has-text('»')"
            )

            if next_link and not await self._is_disabled(next_link):
                await next_link.click()
                await asyncio.sleep(2)
                page_num += 1
            else:
                break

            if page_num > 50:
                break

        return all_records

    async def _is_disabled(self, element) -> bool:
        """Check if element is disabled."""
        disabled = await element.get_attribute("disabled")
        if disabled:
            return True

        class_attr = await element.get_attribute("class") or ""
        return "disabled" in class_attr
