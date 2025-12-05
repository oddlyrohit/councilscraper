"""
City of Sydney Scraper
Custom scraper for City of Sydney's DA tracking portal.
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urljoin
import logging

from src.config.councils import CouncilConfig
from src.scrapers.base.adapter import CouncilAdapter, PortalHealth, RawRecord, ScrapeMode
from src.scrapers.base.browser import BrowserManager


logger = logging.getLogger(__name__)


class SydneyCityAdapter(CouncilAdapter):
    """
    Scraper for City of Sydney's DA tracking system.
    Sydney has a custom portal at online.cityofsydney.nsw.gov.au
    """

    PORTAL_URL = "https://online.cityofsydney.nsw.gov.au/DA"

    def __init__(self, council_config: CouncilConfig):
        super().__init__(council_config)
        self.portal_url = self.PORTAL_URL

    async def get_portal_status(self) -> PortalHealth:
        """Check if the Sydney DA portal is accessible."""
        start_time = datetime.utcnow()

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.portal_url)

                    # Look for search form
                    if await browser.wait_for_selector(page, "form, .search-form", timeout=15000):
                        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        return PortalHealth(
                            is_healthy=True,
                            message="Sydney portal accessible",
                            response_time_ms=response_time,
                        )

                    return PortalHealth(
                        is_healthy=False,
                        message="Sydney portal search form not found",
                    )

        except Exception as e:
            return PortalHealth(
                is_healthy=False,
                message=str(e),
                error_type=type(e).__name__,
            )

    async def scrape_active(self) -> list[RawRecord]:
        """Scrape active DAs from City of Sydney."""
        self._log_scrape_start(ScrapeMode.ACTIVE)

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.portal_url)
                    await asyncio.sleep(2)

                    # Search for recent applications
                    # Sydney portal typically has a search by date range
                    end_date = date.today()
                    start_date = end_date - timedelta(days=90)

                    # Fill search form
                    date_from = await page.query_selector(
                        "input[name*='fromDate'], input[name*='DateFrom'], #fromDate"
                    )
                    if date_from:
                        await date_from.fill(start_date.strftime("%d/%m/%Y"))

                    date_to = await page.query_selector(
                        "input[name*='toDate'], input[name*='DateTo'], #toDate"
                    )
                    if date_to:
                        await date_to.fill(end_date.strftime("%d/%m/%Y"))

                    # Submit search
                    submit = await page.query_selector(
                        "button[type='submit'], input[type='submit'], .search-button"
                    )
                    if submit:
                        await submit.click()
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
        """Scrape historical DAs from City of Sydney."""
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

                    # Search with date range
                    await self._fill_date_range(page, start_date, end_date)

                    # Submit and get results
                    submit = await page.query_selector(
                        "button[type='submit'], input[type='submit']"
                    )
                    if submit:
                        await submit.click()
                        await asyncio.sleep(3)

                    # Handle pagination
                    all_records = await self._scrape_all_pages(page, browser)
                    records.extend(all_records)

        except Exception as e:
            self._log_error("Failed to scrape historical applications", e)

        self._log_scrape_complete(ScrapeMode.HISTORICAL, len(records))
        return records

    async def _fill_date_range(self, page, start_date: date, end_date: date) -> None:
        """Fill date range in search form."""
        selectors = [
            ("input[name*='fromDate']", start_date),
            ("input[name*='DateFrom']", start_date),
            ("#fromDate", start_date),
            ("input[name*='toDate']", end_date),
            ("input[name*='DateTo']", end_date),
            ("#toDate", end_date),
        ]

        for selector, date_value in selectors:
            element = await page.query_selector(selector)
            if element:
                await element.fill(date_value.strftime("%d/%m/%Y"))

    async def _extract_results(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Extract DA results from the page."""
        records = []

        try:
            # Wait for results
            await browser.wait_for_selector(page, "table, .results, .da-list")

            # Try table extraction
            table_data = await browser.get_table_data(page, "table")

            if table_data:
                for row in table_data:
                    record_data = self._map_table_row(row)
                    if record_data.get("da_number"):
                        records.append(self._create_record(
                            data=record_data,
                            source_url=page.url,
                        ))
            else:
                # Try alternative extraction
                items = await page.query_selector_all(".da-item, .result-row, tr[data-id]")

                for item in items:
                    data = await self._parse_result_item(item)
                    if data.get("da_number"):
                        records.append(self._create_record(
                            data=data,
                            source_url=page.url,
                        ))

        except Exception as e:
            logger.error(f"Failed to extract results: {e}")

        return records

    def _map_table_row(self, row: dict) -> dict:
        """Map table row headers to our schema."""
        mapping = {
            "Application Number": "da_number",
            "DA Number": "da_number",
            "Application No": "da_number",
            "Address": "address",
            "Property Address": "address",
            "Site Address": "address",
            "Description": "description",
            "Proposal": "description",
            "Development Description": "description",
            "Status": "status",
            "Application Status": "status",
            "Lodgement Date": "lodged_date",
            "Date Lodged": "lodged_date",
            "Lodged": "lodged_date",
            "Decision Date": "determined_date",
            "Determination Date": "determined_date",
            "Cost": "estimated_cost",
            "Estimated Cost": "estimated_cost",
        }

        result = {}
        for header, value in row.items():
            normalized_header = header.strip()
            if normalized_header in mapping:
                result[mapping[normalized_header]] = value
            else:
                # Include unmapped fields with original header
                result[normalized_header] = value

        return result

    async def _parse_result_item(self, item) -> dict:
        """Parse a single result item element."""
        data = {}

        # Common field selectors
        field_selectors = [
            ("da_number", ".da-number, .app-number, [data-field='number']"),
            ("address", ".address, .location, [data-field='address']"),
            ("description", ".description, .proposal, [data-field='description']"),
            ("status", ".status, [data-field='status']"),
            ("lodged_date", ".date, .lodged-date, [data-field='date']"),
        ]

        for field_name, selector in field_selectors:
            element = await item.query_selector(selector)
            if element:
                text = await element.text_content()
                if text:
                    data[field_name] = text.strip()

        return data

    async def _scrape_all_pages(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Scrape all pages of results."""
        all_records = []
        page_num = 1

        while True:
            records = await self._extract_results(page, browser)
            if not records:
                break

            all_records.extend(records)

            # Look for next page
            next_button = await page.query_selector(
                ".next:not(.disabled), a[rel='next'], .pagination-next"
            )

            if next_button:
                is_disabled = await next_button.get_attribute("disabled")
                if is_disabled:
                    break

                await next_button.click()
                await asyncio.sleep(2)
                page_num += 1
            else:
                break

            # Safety limit
            if page_num > 50:
                break

        return all_records
