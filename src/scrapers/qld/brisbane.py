"""
Brisbane City Council Scraper
Custom scraper for Brisbane's development application portal.
Brisbane is Australia's largest LGA by population (1.35M).
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import logging

from src.config.councils import CouncilConfig
from src.scrapers.base.adapter import CouncilAdapter, PortalHealth, RawRecord, ScrapeMode
from src.scrapers.base.browser import BrowserManager


logger = logging.getLogger(__name__)


class BrisbaneCityAdapter(CouncilAdapter):
    """
    Scraper for Brisbane City Council's DA portal.
    Brisbane uses a custom Development.i implementation.
    """

    PORTAL_URL = "https://developmenti.brisbane.qld.gov.au/masterview/modules/ApplicationMaster/default.aspx"
    SEARCH_URL = "https://developmenti.brisbane.qld.gov.au/masterview/modules/ApplicationMaster/applicationSearch.aspx"

    def __init__(self, council_config: CouncilConfig):
        super().__init__(council_config)
        self.portal_url = self.PORTAL_URL
        self.search_url = self.SEARCH_URL

    async def get_portal_status(self) -> PortalHealth:
        """Check if Brisbane's portal is accessible."""
        start_time = datetime.utcnow()

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.search_url)

                    if await browser.wait_for_selector(page, "form, input, #searchForm", timeout=15000):
                        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        return PortalHealth(
                            is_healthy=True,
                            message="Brisbane portal accessible",
                            response_time_ms=response_time,
                        )

                    return PortalHealth(
                        is_healthy=False,
                        message="Brisbane portal form not found",
                    )

        except Exception as e:
            return PortalHealth(
                is_healthy=False,
                message=str(e),
                error_type=type(e).__name__,
            )

    async def scrape_active(self) -> list[RawRecord]:
        """Scrape active development applications from Brisbane."""
        self._log_scrape_start(ScrapeMode.ACTIVE)

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.search_url)
                    await asyncio.sleep(2)

                    # Brisbane portal typically requires specific search
                    end_date = date.today()
                    start_date = end_date - timedelta(days=90)

                    await self._configure_search(page, start_date, end_date)

                    # Search for applications in progress
                    await self._submit_search(page)
                    await asyncio.sleep(3)

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
        """Scrape historical development applications from Brisbane."""
        self._log_scrape_start(ScrapeMode.HISTORICAL)

        if not start_date:
            start_date = date.today() - timedelta(days=365)
        if not end_date:
            end_date = date.today()

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.search_url)
                    await asyncio.sleep(2)

                    await self._configure_search(page, start_date, end_date)
                    await self._submit_search(page)
                    await asyncio.sleep(3)

                    records = await self._scrape_all_pages(page, browser)

        except Exception as e:
            self._log_error("Failed to scrape historical applications", e)

        self._log_scrape_complete(ScrapeMode.HISTORICAL, len(records))
        return records

    async def _configure_search(
        self,
        page,
        start_date: date,
        end_date: date,
    ) -> None:
        """Configure search parameters on Brisbane portal."""
        date_format = "%d/%m/%Y"

        # Date fields - Brisbane uses specific IDs
        date_selectors = {
            "start": [
                "#ctl00_cphContent_txtLodgementDateFrom",
                "#txtLodgementDateFrom",
                "input[name*='LodgementDateFrom']",
                "input[name*='DateFrom']",
            ],
            "end": [
                "#ctl00_cphContent_txtLodgementDateTo",
                "#txtLodgementDateTo",
                "input[name*='LodgementDateTo']",
                "input[name*='DateTo']",
            ],
        }

        for selector in date_selectors["start"]:
            try:
                el = await page.query_selector(selector)
                if el:
                    await el.fill(start_date.strftime(date_format))
                    break
            except Exception:
                continue

        for selector in date_selectors["end"]:
            try:
                el = await page.query_selector(selector)
                if el:
                    await el.fill(end_date.strftime(date_format))
                    break
            except Exception:
                continue

    async def _submit_search(self, page) -> None:
        """Submit search form."""
        selectors = [
            "#ctl00_cphContent_btnSearch",
            "#btnSearch",
            "input[type='submit'][value*='Search']",
            "button[type='submit']",
            ".search-button",
        ]

        for selector in selectors:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    return
            except Exception:
                continue

    async def _extract_results(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Extract search results from Brisbane portal."""
        records = []

        try:
            # Wait for results grid
            await browser.wait_for_selector(
                page,
                "#ctl00_cphContent_gvResults, table.results, .grid-view",
                timeout=10000,
            )

            # Brisbane uses ASP.NET GridView
            rows = await page.query_selector_all(
                "#ctl00_cphContent_gvResults tr, table.results tbody tr"
            )

            headers = []
            for i, row in enumerate(rows):
                cells = await row.query_selector_all("th, td")

                if i == 0:
                    # Header row
                    for cell in cells:
                        text = await cell.text_content()
                        headers.append(text.strip() if text else "")
                else:
                    # Data row
                    row_data = {}
                    for j, cell in enumerate(cells):
                        if j < len(headers):
                            text = await cell.text_content()
                            row_data[headers[j]] = text.strip() if text else ""

                            # Check for links (application detail page)
                            link = await cell.query_selector("a")
                            if link and headers[j] in ["Application Number", "Application No"]:
                                href = await link.get_attribute("href")
                                if href:
                                    row_data["detail_url"] = href

                    if row_data:
                        mapped_data = self._map_brisbane_row(row_data)
                        if mapped_data.get("da_number"):
                            records.append(self._create_record(
                                data=mapped_data,
                                source_url=page.url,
                            ))

        except Exception as e:
            logger.error(f"Failed to extract Brisbane results: {e}")

        return records

    def _map_brisbane_row(self, row: dict) -> dict:
        """Map Brisbane table row to schema."""
        mapping = {
            "Application Number": "da_number",
            "Application No": "da_number",
            "Application Reference": "da_number",
            "Address": "address",
            "Property Address": "address",
            "Site Address": "address",
            "Property": "address",
            "Description": "description",
            "Proposal": "description",
            "Development Description": "description",
            "Status": "status",
            "Current Status": "status",
            "Stage": "status",
            "Lodgement Date": "lodged_date",
            "Date Lodged": "lodged_date",
            "Lodged": "lodged_date",
            "Decision Date": "determined_date",
            "Date Decided": "determined_date",
            "Decision": "decision",
            "Outcome": "decision",
            "Estimated Cost": "estimated_cost",
            "Est Cost": "estimated_cost",
            "Value": "estimated_cost",
            "Applicant": "applicant_name",
        }

        result = {}
        for header, value in row.items():
            if not header:
                continue
            if header in mapping:
                result[mapping[header]] = value
            else:
                result[header] = value

        return result

    async def _scrape_all_pages(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Scrape all pages with ASP.NET pagination."""
        all_records = []
        page_num = 1
        max_pages = 100

        while page_num <= max_pages:
            records = await self._extract_results(page, browser)
            if not records:
                break

            all_records.extend(records)

            # ASP.NET GridView pagination
            next_link = await page.query_selector(
                ".pagination a:has-text('Next'), "
                "a.pager-next, "
                "a[href*='Page$Next'], "
                "#ctl00_cphContent_gvResults a:has-text('>')"
            )

            if next_link:
                is_disabled = await next_link.get_attribute("disabled")
                if is_disabled:
                    break

                await next_link.click()
                await asyncio.sleep(2)
                page_num += 1
            else:
                break

        return all_records
