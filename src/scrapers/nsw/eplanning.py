"""
NSW ePlanning Portal Scraper
Handles councils using the NSW Planning Portal (planningportal.nsw.gov.au)
Covers approximately 50+ NSW councils
"""

import asyncio
import re
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urlencode, urljoin
import logging

from src.config.councils import CouncilConfig
from src.scrapers.base.adapter import CouncilAdapter, PortalHealth, RawRecord, ScrapeMode
from src.scrapers.base.browser import BrowserManager


logger = logging.getLogger(__name__)


# NSW Planning Portal API endpoints
NSW_PORTAL_BASE = "https://www.planningportal.nsw.gov.au"
NSW_API_BASE = "https://api.apps1.nsw.gov.au/eplanning/data/v0"


# Council codes to LGA identifiers mapping
COUNCIL_LGA_MAP = {
    "BLACKTOWN": "10500",
    "CANTERBURY_BANKSTOWN": "11520",
    "CENTRAL_COAST": "12380",
    "PARRAMATTA": "15990",
    "NORTHERN_BEACHES": "15350",
    "CUMBERLAND": "12850",
    "SUTHERLAND": "17640",
    "LIVERPOOL": "14900",
    "PENRITH": "16350",
    "FAIRFIELD": "13310",
    "WOLLONGONG": "18450",
    "LAKE_MACQUARIE": "14650",
    "INNER_WEST": "14170",
    "THE_HILLS": "17420",
    "CAMPBELLTOWN_NSW": "11720",
    "BAYSIDE_NSW": "10550",
    "NEWCASTLE": "15900",
    "GEORGES_RIVER": "13800",
    "HORNSBY": "14000",
    "RANDWICK": "16550",
    "CAMDEN": "11600",
    # Add more mappings as needed
}


class NSWEPlanningAdapter(CouncilAdapter):
    """
    Scraper for NSW Planning Portal.
    This portal provides a unified interface for many NSW councils.
    """

    # Supported councils
    SUPPORTED_COUNCILS = list(COUNCIL_LGA_MAP.keys())

    def __init__(self, council_config: CouncilConfig):
        super().__init__(council_config)
        self.portal_url = NSW_PORTAL_BASE
        self.api_base = NSW_API_BASE
        self.lga_id = COUNCIL_LGA_MAP.get(council_config.code)

    async def get_portal_status(self) -> PortalHealth:
        """Check if the NSW Planning Portal is accessible."""
        start_time = datetime.utcnow()

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, f"{self.portal_url}/datracking")

                    # Check for key elements
                    if await browser.wait_for_selector(page, "input[type='text']", timeout=10000):
                        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        return PortalHealth(
                            is_healthy=True,
                            message="Portal accessible",
                            response_time_ms=response_time,
                        )

                    return PortalHealth(
                        is_healthy=False,
                        message="Portal elements not found",
                    )

        except Exception as e:
            return PortalHealth(
                is_healthy=False,
                message=str(e),
                error_type=type(e).__name__,
            )

    async def scrape_active(self) -> list[RawRecord]:
        """Scrape active DAs from NSW Planning Portal."""
        self._log_scrape_start(ScrapeMode.ACTIVE)

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    # Navigate to DA tracking page
                    search_url = self._build_search_url(
                        status="Under Assessment",
                        date_range_days=90,
                    )

                    await browser.goto(page, search_url)
                    await asyncio.sleep(2)  # Wait for dynamic content

                    # Try to extract data from the page
                    records = await self._extract_applications(page, browser)

                    # Also get recently determined
                    determined_url = self._build_search_url(
                        status="Determined",
                        date_range_days=30,
                    )
                    await browser.goto(page, determined_url)
                    await asyncio.sleep(2)

                    determined_records = await self._extract_applications(page, browser)
                    records.extend(determined_records)

        except Exception as e:
            self._log_error("Failed to scrape active applications", e)

        self._log_scrape_complete(ScrapeMode.ACTIVE, len(records))
        return records

    async def scrape_historical(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[RawRecord]:
        """Scrape historical DAs from NSW Planning Portal."""
        self._log_scrape_start(ScrapeMode.HISTORICAL)

        if not start_date:
            start_date = date.today() - timedelta(days=365)
        if not end_date:
            end_date = date.today()

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    # Search with date range
                    search_url = self._build_search_url(
                        start_date=start_date,
                        end_date=end_date,
                    )

                    await browser.goto(page, search_url)
                    await asyncio.sleep(2)

                    # Handle pagination
                    page_num = 1
                    while True:
                        page_records = await self._extract_applications(page, browser)
                        if not page_records:
                            break

                        records.extend(page_records)

                        # Check for next page
                        next_button = await page.query_selector(".pagination .next:not(.disabled)")
                        if next_button:
                            await next_button.click()
                            await asyncio.sleep(1)
                            page_num += 1
                        else:
                            break

                        # Safety limit
                        if page_num > 100:
                            break

        except Exception as e:
            self._log_error("Failed to scrape historical applications", e)

        self._log_scrape_complete(ScrapeMode.HISTORICAL, len(records))
        return records

    def _build_search_url(
        self,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        date_range_days: Optional[int] = None,
    ) -> str:
        """Build search URL with parameters."""
        base_url = f"{self.portal_url}/datracking"

        params = {}

        if self.lga_id:
            params["council"] = self.lga_id

        if status:
            params["status"] = status

        if date_range_days:
            end = date.today()
            start = end - timedelta(days=date_range_days)
            params["fromDate"] = start.strftime("%Y-%m-%d")
            params["toDate"] = end.strftime("%Y-%m-%d")
        elif start_date or end_date:
            if start_date:
                params["fromDate"] = start_date.strftime("%Y-%m-%d")
            if end_date:
                params["toDate"] = end_date.strftime("%Y-%m-%d")

        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url

    async def _extract_applications(
        self,
        page,
        browser: BrowserManager,
    ) -> list[RawRecord]:
        """Extract DA data from search results page."""
        records = []

        try:
            # Wait for results table
            await browser.wait_for_selector(page, ".da-results, .search-results, table")

            # Try table-based results
            rows = await page.query_selector_all("table tbody tr, .da-result-item")

            for row in rows:
                try:
                    record_data = await self._parse_result_row(row)
                    if record_data and record_data.get("da_number"):
                        records.append(self._create_record(
                            data=record_data,
                            source_url=page.url,
                        ))
                except Exception as e:
                    logger.debug(f"Failed to parse row: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to extract applications: {e}")

        return records

    async def _parse_result_row(self, row) -> dict:
        """Parse a single result row into a record dict."""
        data = {}

        try:
            # Try common selectors for NSW portal
            cells = await row.query_selector_all("td")

            if cells and len(cells) >= 3:
                # Typical structure: DA Number, Address, Description, Status, Date
                data["da_number"] = await self._get_cell_text(cells[0])
                data["address"] = await self._get_cell_text(cells[1])
                data["description"] = await self._get_cell_text(cells[2])

                if len(cells) > 3:
                    data["status"] = await self._get_cell_text(cells[3])
                if len(cells) > 4:
                    data["lodged_date"] = await self._get_cell_text(cells[4])

                # Get detail link if available
                link = await row.query_selector("a[href*='application']")
                if link:
                    href = await link.get_attribute("href")
                    if href:
                        data["detail_url"] = urljoin(self.portal_url, href)

            # Alternative: Card-style layout
            else:
                da_el = await row.query_selector(".da-number, .application-number")
                if da_el:
                    data["da_number"] = await da_el.text_content()

                addr_el = await row.query_selector(".address, .property-address")
                if addr_el:
                    data["address"] = await addr_el.text_content()

                desc_el = await row.query_selector(".description, .proposal")
                if desc_el:
                    data["description"] = await desc_el.text_content()

                status_el = await row.query_selector(".status")
                if status_el:
                    data["status"] = await status_el.text_content()

        except Exception as e:
            logger.debug(f"Error parsing row: {e}")

        # Clean up values
        return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}

    async def _get_cell_text(self, cell) -> str:
        """Get text content from a table cell."""
        text = await cell.text_content()
        return text.strip() if text else ""

    async def scrape_application(self, da_number: str) -> Optional[RawRecord]:
        """Scrape a single application by DA number."""
        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    # Search for specific DA
                    search_url = f"{self.portal_url}/datracking?applicationNumber={da_number}"
                    await browser.goto(page, search_url)
                    await asyncio.sleep(2)

                    records = await self._extract_applications(page, browser)
                    if records:
                        return records[0]

        except Exception as e:
            self._log_error(f"Failed to scrape application {da_number}", e)

        return None
