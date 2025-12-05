"""
South Australia PlanSA Portal Scraper
PlanSA is the centralized planning portal for ALL South Australian councils.
One scraper covers the entire state (~20 councils).
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import logging

from src.config.councils import CouncilConfig
from src.scrapers.base.adapter import CouncilAdapter, PortalHealth, RawRecord, ScrapeMode
from src.scrapers.base.browser import BrowserManager


logger = logging.getLogger(__name__)


# PlanSA portal URL
PLAN_SA_URL = "https://plan.sa.gov.au"
PLAN_SA_SEARCH = f"{PLAN_SA_URL}/public-register"


# SA council mapping
SA_COUNCIL_MAP = {
    "ONKAPARINGA": "City of Onkaparinga",
    "SALISBURY": "City of Salisbury",
    "PORT_ADELAIDE_ENFIELD": "City of Port Adelaide Enfield",
    "CHARLES_STURT": "City of Charles Sturt",
    "TEA_TREE_GULLY": "City of Tea Tree Gully",
    "PLAYFORD": "City of Playford",
    "MARION": "City of Marion",
    "WEST_TORRENS": "City of West Torrens",
    "CAMPBELLTOWN_SA": "City of Campbelltown",
    "BURNSIDE": "City of Burnside",
    "MOUNT_BARKER": "Mount Barker District Council",
    "ADELAIDE_HILLS": "Adelaide Hills Council",
    "UNLEY": "City of Unley",
    "NORWOOD": "City of Norwood Payneham St Peters",
    "ALEXANDRINA": "Alexandrina Council",
    "MOUNT_GAMBIER": "City of Mount Gambier",
    "BAROSSA": "The Barossa Council",
    "GAWLER": "Town of Gawler",
    "MURRAY_BRIDGE": "Rural City of Murray Bridge",
    "PROSPECT": "City of Prospect",
    "WHYALLA": "City of Whyalla",
    "ADELAIDE": "City of Adelaide",
}


class SAPlanSAAdapter(CouncilAdapter):
    """
    Scraper for South Australia's PlanSA portal.
    This centralized portal covers ALL SA councils with one scraper.
    """

    SUPPORTED_COUNCILS = list(SA_COUNCIL_MAP.keys())

    def __init__(self, council_config: CouncilConfig):
        super().__init__(council_config)
        self.portal_url = PLAN_SA_URL
        self.search_url = PLAN_SA_SEARCH
        self.council_name = SA_COUNCIL_MAP.get(council_config.code)

    async def get_portal_status(self) -> PortalHealth:
        """Check if PlanSA portal is accessible."""
        start_time = datetime.utcnow()

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.search_url)

                    if await browser.wait_for_selector(page, "form, .search, input", timeout=15000):
                        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        return PortalHealth(
                            is_healthy=True,
                            message="PlanSA portal accessible",
                            response_time_ms=response_time,
                        )

                    return PortalHealth(
                        is_healthy=False,
                        message="PlanSA portal form not found",
                    )

        except Exception as e:
            return PortalHealth(
                is_healthy=False,
                message=str(e),
                error_type=type(e).__name__,
            )

    async def scrape_active(self) -> list[RawRecord]:
        """Scrape active development applications from PlanSA."""
        self._log_scrape_start(ScrapeMode.ACTIVE)

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.search_url)
                    await asyncio.sleep(2)

                    # Select council
                    if self.council_name:
                        await self._select_council(page)

                    # Set date range
                    end_date = date.today()
                    start_date = end_date - timedelta(days=90)
                    await self._set_date_range(page, start_date, end_date)

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
                    await browser.goto(page, self.search_url)
                    await asyncio.sleep(2)

                    if self.council_name:
                        await self._select_council(page)

                    await self._set_date_range(page, start_date, end_date)
                    await self._submit_search(page)
                    await asyncio.sleep(3)

                    records = await self._scrape_all_pages(page, browser)

        except Exception as e:
            self._log_error("Failed to scrape historical applications", e)

        self._log_scrape_complete(ScrapeMode.HISTORICAL, len(records))
        return records

    async def _select_council(self, page) -> None:
        """Select council from dropdown."""
        selectors = [
            "select[name*='council']",
            "select[name*='authority']",
            "#council",
            "#relevantAuthority",
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

        for sel, val in [
            ("#dateFrom, input[name*='from']", start_date),
            ("#dateTo, input[name*='to']", end_date),
        ]:
            try:
                el = await page.query_selector(sel)
                if el:
                    await el.fill(val.strftime(date_format))
            except Exception:
                continue

    async def _submit_search(self, page) -> None:
        """Submit search form."""
        for selector in ["button[type='submit']", "input[type='submit']", ".search-btn"]:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    return
            except Exception:
                continue

    async def _extract_results(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Extract search results."""
        records = []

        try:
            await browser.wait_for_selector(page, "table, .results", timeout=10000)

            table_data = await browser.get_table_data(page, "table")

            for row in table_data:
                mapped = self._map_plan_sa_row(row)
                if mapped.get("da_number") or mapped.get("address"):
                    records.append(self._create_record(data=mapped, source_url=page.url))

        except Exception as e:
            logger.error(f"Failed to extract PlanSA results: {e}")

        return records

    def _map_plan_sa_row(self, row: dict) -> dict:
        """Map PlanSA table row to schema."""
        mapping = {
            "Application ID": "da_number",
            "Application Number": "da_number",
            "ID": "da_number",
            "Address": "address",
            "Property Address": "address",
            "Site Address": "address",
            "Description": "description",
            "Proposal": "description",
            "Status": "status",
            "Stage": "status",
            "Lodged Date": "lodged_date",
            "Date Lodged": "lodged_date",
            "Decision Date": "determined_date",
            "Decision": "decision",
            "Relevant Authority": "council_name",
            "Council": "council_name",
        }

        result = {}
        for header, value in row.items():
            if header.strip() in mapping:
                result[mapping[header.strip()]] = value
            else:
                result[header] = value

        return result

    async def _scrape_all_pages(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Scrape all pages with pagination."""
        all_records = []
        page_num = 1

        while page_num <= 100:
            records = await self._extract_results(page, browser)
            if not records:
                break

            all_records.extend(records)

            next_link = await page.query_selector(".next:not(.disabled), a:has-text('Next')")
            if next_link:
                await next_link.click()
                await asyncio.sleep(2)
                page_num += 1
            else:
                break

        return all_records
