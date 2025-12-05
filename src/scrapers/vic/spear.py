"""
Victoria SPEAR Portal Scraper
Handles councils using the SPEAR (Streamlined Planning through Electronic Applications and Referrals) system.
Covers approximately 50+ Victorian councils with a SINGLE scraper.
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urlencode
import logging

from src.config.councils import CouncilConfig
from src.scrapers.base.adapter import CouncilAdapter, PortalHealth, RawRecord, ScrapeMode
from src.scrapers.base.browser import BrowserManager


logger = logging.getLogger(__name__)


# SPEAR base URLs
SPEAR_PORTAL = "https://www.spear.land.vic.gov.au"
SPEAR_SEARCH = f"{SPEAR_PORTAL}/spear/pages/publicPlanningSearch.shtml"


# Council codes to SPEAR LGA identifiers
VIC_COUNCIL_LGA_MAP = {
    "CASEY": "Casey",
    "WYNDHAM": "Wyndham",
    "GREATER_GEELONG": "Greater Geelong",
    "HUME": "Hume",
    "WHITTLESEA": "Whittlesea",
    "BRIMBANK": "Brimbank",
    "MONASH": "Monash",
    "MELTON": "Melton",
    "BOROONDARA": "Boroondara",
    "MORELAND": "Merri-bek",
    "GREATER_DANDENONG": "Greater Dandenong",
    "KNOX": "Knox",
    "DAREBIN": "Darebin",
    "FRANKSTON": "Frankston",
    "MOONEE_VALLEY": "Moonee Valley",
    "BALLARAT": "Ballarat",
    "BENDIGO": "Greater Bendigo",
    "LATROBE_VIC": "Latrobe",
    "SHEPPARTON": "Greater Shepparton",
    "MILDURA": "Mildura",
    "BAW_BAW": "Baw Baw",
    "MITCHELL": "Mitchell",
    "MACEDON_RANGES": "Macedon Ranges",
    "EAST_GIPPSLAND": "East Gippsland",
    "WELLINGTON": "Wellington",
    "WODONGA": "Wodonga",
    "BASS_COAST": "Bass Coast",
    "SURF_COAST": "Surf Coast",
    "WANGARATTA": "Wangaratta",
    "MOIRA": "Moira",
    "CAMPASPE": "Campaspe",
    "SOUTH_GIPPSLAND": "South Gippsland",
    "WARRNAMBOOL": "Warrnambool",
    "COLAC_OTWAY": "Colac Otway",
    "MOUNT_ALEXANDER": "Mount Alexander",
    "HORSHAM": "Horsham",
    "INDIGO": "Indigo",
    "HEPBURN": "Hepburn",
    "BENALLA": "Benalla",
    "MURRINDINDI": "Murrindindi",
    "ALPINE": "Alpine",
    "ARARAT": "Ararat",
}


class VICSPEARAdapter(CouncilAdapter):
    """
    Scraper for Victoria's SPEAR Planning Portal.
    This single scraper handles ALL Victorian councils using SPEAR (~50 councils).

    Key advantage: Build once, scrape 50 councils!
    """

    SUPPORTED_COUNCILS = list(VIC_COUNCIL_LGA_MAP.keys())

    def __init__(self, council_config: CouncilConfig):
        super().__init__(council_config)
        self.portal_url = SPEAR_PORTAL
        self.search_url = SPEAR_SEARCH
        self.lga_name = VIC_COUNCIL_LGA_MAP.get(council_config.code)

    async def get_portal_status(self) -> PortalHealth:
        """Check if the SPEAR portal is accessible."""
        start_time = datetime.utcnow()

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.search_url)

                    # Look for search form elements
                    if await browser.wait_for_selector(
                        page,
                        "#councilName, input[name*='council'], .search-form",
                        timeout=15000,
                    ):
                        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        return PortalHealth(
                            is_healthy=True,
                            message="SPEAR portal accessible",
                            response_time_ms=response_time,
                        )

                    return PortalHealth(
                        is_healthy=False,
                        message="SPEAR search form not found",
                    )

        except Exception as e:
            return PortalHealth(
                is_healthy=False,
                message=str(e),
                error_type=type(e).__name__,
            )

    async def scrape_active(self) -> list[RawRecord]:
        """Scrape active planning applications from SPEAR."""
        self._log_scrape_start(ScrapeMode.ACTIVE)

        records = []

        try:
            async with BrowserManager() as browser:
                async with browser.new_page() as page:
                    await browser.goto(page, self.search_url)
                    await asyncio.sleep(2)

                    # Select council
                    if self.lga_name:
                        await self._select_council(page, self.lga_name)

                    # Set date range for recent applications
                    end_date = date.today()
                    start_date = end_date - timedelta(days=90)

                    await self._fill_date_range(page, start_date, end_date)

                    # Select status - Under Consideration
                    await self._select_status(page, "Under Consideration")

                    # Submit search
                    await self._submit_search(page)

                    # Extract results
                    under_consideration = await self._extract_results(page, browser)
                    records.extend(under_consideration)

                    # Also get recently decided
                    await browser.goto(page, self.search_url)
                    await asyncio.sleep(2)

                    if self.lga_name:
                        await self._select_council(page, self.lga_name)

                    determined_start = end_date - timedelta(days=30)
                    await self._fill_date_range(page, determined_start, end_date)
                    await self._select_status(page, "Decided")
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
        """Scrape historical planning applications from SPEAR."""
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

                    # Select council
                    if self.lga_name:
                        await self._select_council(page, self.lga_name)

                    # Set date range
                    await self._fill_date_range(page, start_date, end_date)

                    # Search all statuses
                    await self._submit_search(page)

                    # Extract all pages
                    records = await self._scrape_all_pages(page, browser)

        except Exception as e:
            self._log_error("Failed to scrape historical applications", e)

        self._log_scrape_complete(ScrapeMode.HISTORICAL, len(records))
        return records

    async def _select_council(self, page, council_name: str) -> None:
        """Select council from dropdown."""
        selectors = [
            "#councilName",
            "select[name*='council']",
            "select[name*='lga']",
            ".council-select select",
        ]

        for selector in selectors:
            try:
                await page.select_option(selector, label=council_name)
                await asyncio.sleep(0.5)
                return
            except Exception:
                continue

        logger.warning(f"Could not select council: {council_name}")

    async def _fill_date_range(self, page, start_date: date, end_date: date) -> None:
        """Fill date range fields."""
        date_selectors = [
            ("#fromDate", start_date),
            ("#toDate", end_date),
            ("input[name*='fromDate']", start_date),
            ("input[name*='toDate']", end_date),
            ("input[name*='dateFrom']", start_date),
            ("input[name*='dateTo']", end_date),
        ]

        for selector, date_val in date_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await element.fill(date_val.strftime("%d/%m/%Y"))
            except Exception:
                continue

    async def _select_status(self, page, status: str) -> None:
        """Select application status."""
        selectors = [
            "#status",
            "select[name*='status']",
            ".status-select select",
        ]

        for selector in selectors:
            try:
                await page.select_option(selector, label=status)
                return
            except Exception:
                continue

    async def _submit_search(self, page) -> None:
        """Submit the search form."""
        selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "#searchButton",
            ".search-button",
            "button:has-text('Search')",
        ]

        for selector in selectors:
            try:
                button = await page.query_selector(selector)
                if button:
                    await button.click()
                    await asyncio.sleep(3)
                    return
            except Exception:
                continue

    async def _extract_results(self, page, browser: BrowserManager) -> list[RawRecord]:
        """Extract planning application results."""
        records = []

        try:
            # Wait for results table
            await browser.wait_for_selector(page, "table, .results-table, .search-results")

            # Extract table data
            table_data = await browser.get_table_data(page, "table.results, table.data-table, table")

            for row in table_data:
                record_data = self._map_spear_row(row)
                if record_data.get("da_number") or record_data.get("address"):
                    records.append(self._create_record(
                        data=record_data,
                        source_url=page.url,
                    ))

        except Exception as e:
            logger.error(f"Failed to extract SPEAR results: {e}")

        return records

    def _map_spear_row(self, row: dict) -> dict:
        """Map SPEAR table row to our schema."""
        mapping = {
            "Application Number": "da_number",
            "Application No.": "da_number",
            "Planning Application": "da_number",
            "Reference": "da_number",
            "Property Address": "address",
            "Address": "address",
            "Site Address": "address",
            "Location": "address",
            "Description": "description",
            "Proposal": "description",
            "Nature of Application": "description",
            "Status": "status",
            "Application Status": "status",
            "Current Status": "status",
            "Date Received": "lodged_date",
            "Lodged Date": "lodged_date",
            "Received": "lodged_date",
            "Date Lodged": "lodged_date",
            "Decision Date": "determined_date",
            "Decided": "determined_date",
            "Date Decided": "determined_date",
            "Decision": "decision",
            "Outcome": "decision",
            "Cost of Works": "estimated_cost",
            "Estimated Cost": "estimated_cost",
            "Council": "council_name",
            "LGA": "council_name",
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
        """Scrape all pages of results with pagination."""
        all_records = []
        page_num = 1
        max_pages = 100

        while page_num <= max_pages:
            records = await self._extract_results(page, browser)
            if not records:
                break

            all_records.extend(records)

            # Find and click next page
            next_button = await page.query_selector(
                "a.next, .pagination .next, a:has-text('Next'), a:has-text('>')"
            )

            if next_button:
                is_disabled = await next_button.get_attribute("disabled")
                if is_disabled or await next_button.get_attribute("class") and "disabled" in await next_button.get_attribute("class"):
                    break

                try:
                    await next_button.click()
                    await asyncio.sleep(2)
                    page_num += 1
                except Exception:
                    break
            else:
                break

        return all_records
