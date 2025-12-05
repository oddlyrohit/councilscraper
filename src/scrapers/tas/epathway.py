"""
Tasmania ePathway Portal Scraper
Many Tasmanian councils use the ePathway system.
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import logging

from src.config.councils import CouncilConfig
from src.scrapers.base.adapter import CouncilAdapter, PortalHealth, RawRecord, ScrapeMode
from src.scrapers.base.browser import BrowserManager


logger = logging.getLogger(__name__)


TAS_COUNCIL_PORTALS = {
    "LAUNCESTON": "https://eservices.launceston.tas.gov.au/ePathway/",
    "HOBART": "https://epathway.hobartcity.com.au/ePathway/",
    "CLARENCE": "https://epathway.ccc.tas.gov.au/ePathway/",
    "GLENORCHY": "https://epathway.gcc.tas.gov.au/ePathway/",
    "KINGBOROUGH": "https://epathway.kingborough.tas.gov.au/ePathway/",
}


class TASEPathwayAdapter(CouncilAdapter):
    """Scraper for Tasmanian councils using ePathway."""

    SUPPORTED_COUNCILS = list(TAS_COUNCIL_PORTALS.keys())

    def __init__(self, council_config: CouncilConfig):
        super().__init__(council_config)
        self.portal_url = TAS_COUNCIL_PORTALS.get(council_config.code, "")

    async def get_portal_status(self) -> PortalHealth:
        """Check portal accessibility."""
        if not self.portal_url:
            return PortalHealth(is_healthy=False, message="No portal URL configured")

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

        if not self.portal_url:
            return records

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, f"{self.portal_url}Production/Web/GeneralEnquiry/EnquiryLists.aspx")
                    await asyncio.sleep(2)

                    # ePathway has a specific structure
                    await self._select_enquiry_type(page, "Development Applications")
                    await asyncio.sleep(1)

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

        if not self.portal_url:
            return records

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, f"{self.portal_url}Production/Web/GeneralEnquiry/EnquirySummaryView.aspx")
                    await asyncio.sleep(2)

                    records = await self._extract_results(page, browser)

        except Exception as e:
            self._log_error("Failed to scrape historical applications", e)

        self._log_scrape_complete(ScrapeMode.HISTORICAL, len(records))
        return records

    async def _select_enquiry_type(self, page, enquiry_type: str) -> None:
        """Select enquiry type in ePathway."""
        try:
            await page.select_option("#ctl00_MainBodyContent_ddlType", label=enquiry_type)
        except Exception:
            pass

    async def _extract_results(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Extract results from ePathway."""
        records = []

        try:
            await browser.wait_for_selector(page, "table, .grid", timeout=10000)

            rows = await page.query_selector_all("table.grid tr, table tbody tr")
            headers = []

            for i, row in enumerate(rows):
                cells = await row.query_selector_all("th, td")

                if i == 0 or not headers:
                    for cell in cells:
                        text = await cell.text_content()
                        headers.append(text.strip() if text else "")
                    continue

                row_data = {}
                for j, cell in enumerate(cells):
                    if j < len(headers):
                        text = await cell.text_content()
                        row_data[headers[j]] = text.strip() if text else ""

                if row_data:
                    mapped = self._map_epathway_row(row_data)
                    if mapped.get("da_number"):
                        records.append(self._create_record(data=mapped, source_url=page.url))

        except Exception as e:
            logger.error(f"Failed to extract ePathway results: {e}")

        return records

    def _map_epathway_row(self, row: dict) -> dict:
        """Map ePathway row to schema."""
        mapping = {
            "Application Number": "da_number",
            "Application No": "da_number",
            "Application": "da_number",
            "Address": "address",
            "Property Address": "address",
            "Location": "address",
            "Description": "description",
            "Proposal": "description",
            "Status": "status",
            "Lodged": "lodged_date",
            "Lodged Date": "lodged_date",
            "Decision": "decision",
            "Decision Date": "determined_date",
        }

        result = {}
        for header, value in row.items():
            if header in mapping:
                result[mapping[header]] = value
            else:
                result[header] = value

        return result
