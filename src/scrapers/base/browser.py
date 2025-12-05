"""
Browser Manager for Playwright-based scraping.
Handles browser lifecycle, page management, and common operations.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator
import logging

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeout,
)

from src.config import settings


logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Manages Playwright browser instances for scraping.
    Provides context managers for safe resource handling.
    """

    def __init__(
        self,
        headless: Optional[bool] = None,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
    ):
        """
        Initialize browser manager.

        Args:
            headless: Run browser in headless mode
            user_agent: Custom user agent string
            proxy: Proxy server URL
        """
        self.headless = headless if headless is not None else settings.scraper_headless
        self.user_agent = user_agent or settings.scraper_user_agent
        self.proxy = proxy
        self.timeout = settings.scraper_timeout_seconds * 1000  # Convert to ms

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def __aenter__(self) -> "BrowserManager":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Start the browser."""
        if self._browser is not None:
            return

        self._playwright = await async_playwright().start()

        launch_options = {
            "headless": self.headless,
        }

        if self.proxy:
            launch_options["proxy"] = {"server": self.proxy}

        self._browser = await self._playwright.chromium.launch(**launch_options)
        logger.debug("Browser started")

    async def close(self) -> None:
        """Close the browser and cleanup."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.debug("Browser closed")

    @asynccontextmanager
    async def new_context(
        self,
        viewport: Optional[dict] = None,
        locale: str = "en-AU",
        timezone: str = "Australia/Sydney",
    ) -> AsyncIterator[BrowserContext]:
        """
        Create a new browser context.

        Args:
            viewport: Viewport size dict {"width": int, "height": int}
            locale: Browser locale
            timezone: Browser timezone

        Yields:
            Browser context
        """
        if not self._browser:
            await self.start()

        context_options = {
            "user_agent": self.user_agent,
            "viewport": viewport or {"width": 1920, "height": 1080},
            "locale": locale,
            "timezone_id": timezone,
        }

        context = await self._browser.new_context(**context_options)

        try:
            yield context
        finally:
            await context.close()

    @asynccontextmanager
    async def new_page(
        self,
        context: Optional[BrowserContext] = None,
    ) -> AsyncIterator[Page]:
        """
        Create a new page.

        Args:
            context: Existing context or create new one

        Yields:
            Page object
        """
        if context:
            page = await context.new_page()
            try:
                yield page
            finally:
                await page.close()
        else:
            async with self.new_context() as ctx:
                page = await ctx.new_page()
                try:
                    yield page
                finally:
                    await page.close()

    async def goto(
        self,
        page: Page,
        url: str,
        wait_until: str = "networkidle",
        timeout: Optional[int] = None,
    ) -> None:
        """
        Navigate to a URL with error handling.

        Args:
            page: Page to navigate
            url: URL to navigate to
            wait_until: When to consider navigation complete
            timeout: Navigation timeout in ms
        """
        timeout = timeout or self.timeout
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
        except PlaywrightTimeout:
            logger.warning(f"Navigation timeout for {url}, continuing anyway")
        except Exception as e:
            logger.error(f"Navigation error for {url}: {e}")
            raise

    async def wait_for_selector(
        self,
        page: Page,
        selector: str,
        timeout: Optional[int] = None,
        state: str = "visible",
    ) -> bool:
        """
        Wait for a selector to appear.

        Args:
            page: Page to wait on
            selector: CSS selector
            timeout: Wait timeout in ms
            state: Element state to wait for

        Returns:
            True if element found, False if timeout
        """
        timeout = timeout or self.timeout
        try:
            await page.wait_for_selector(selector, timeout=timeout, state=state)
            return True
        except PlaywrightTimeout:
            return False

    async def get_text(self, page: Page, selector: str) -> Optional[str]:
        """
        Get text content of an element.

        Args:
            page: Page to query
            selector: CSS selector

        Returns:
            Text content or None
        """
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.text_content()
        except Exception:
            pass
        return None

    async def get_all_text(self, page: Page, selector: str) -> list[str]:
        """
        Get text content of all matching elements.

        Args:
            page: Page to query
            selector: CSS selector

        Returns:
            List of text contents
        """
        try:
            elements = await page.query_selector_all(selector)
            texts = []
            for el in elements:
                text = await el.text_content()
                if text:
                    texts.append(text.strip())
            return texts
        except Exception:
            return []

    async def get_attribute(
        self,
        page: Page,
        selector: str,
        attribute: str,
    ) -> Optional[str]:
        """
        Get attribute value of an element.

        Args:
            page: Page to query
            selector: CSS selector
            attribute: Attribute name

        Returns:
            Attribute value or None
        """
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.get_attribute(attribute)
        except Exception:
            pass
        return None

    async def click_and_wait(
        self,
        page: Page,
        selector: str,
        wait_for: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> bool:
        """
        Click an element and optionally wait for another.

        Args:
            page: Page to interact with
            selector: Selector to click
            wait_for: Selector to wait for after click
            timeout: Wait timeout in ms

        Returns:
            True if successful
        """
        timeout = timeout or self.timeout
        try:
            await page.click(selector, timeout=timeout)
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"Click failed for {selector}: {e}")
            return False

    async def fill_form(self, page: Page, form_data: dict) -> None:
        """
        Fill a form with data.

        Args:
            page: Page containing the form
            form_data: Dict of selector -> value pairs
        """
        for selector, value in form_data.items():
            try:
                await page.fill(selector, str(value))
            except Exception as e:
                logger.warning(f"Failed to fill {selector}: {e}")

    async def select_option(
        self,
        page: Page,
        selector: str,
        value: str,
    ) -> bool:
        """
        Select an option in a dropdown.

        Args:
            page: Page containing the select
            selector: Select element selector
            value: Value to select

        Returns:
            True if successful
        """
        try:
            await page.select_option(selector, value)
            return True
        except Exception as e:
            logger.warning(f"Failed to select {value} in {selector}: {e}")
            return False

    async def get_table_data(
        self,
        page: Page,
        table_selector: str,
        header_selector: str = "th",
        row_selector: str = "tbody tr",
        cell_selector: str = "td",
    ) -> list[dict]:
        """
        Extract data from an HTML table.

        Args:
            page: Page containing the table
            table_selector: Table element selector
            header_selector: Header cell selector
            row_selector: Row selector
            cell_selector: Cell selector

        Returns:
            List of dicts with header keys and cell values
        """
        try:
            # Get headers
            headers = await page.query_selector_all(f"{table_selector} {header_selector}")
            header_texts = []
            for h in headers:
                text = await h.text_content()
                header_texts.append(text.strip() if text else "")

            # Get rows
            rows = await page.query_selector_all(f"{table_selector} {row_selector}")
            data = []

            for row in rows:
                cells = await row.query_selector_all(cell_selector)
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(header_texts):
                        text = await cell.text_content()
                        row_data[header_texts[i]] = text.strip() if text else ""
                if row_data:
                    data.append(row_data)

            return data
        except Exception as e:
            logger.error(f"Failed to extract table data: {e}")
            return []

    async def scroll_to_bottom(self, page: Page, delay: float = 0.5) -> None:
        """
        Scroll to the bottom of the page (for infinite scroll).

        Args:
            page: Page to scroll
            delay: Delay between scroll steps
        """
        previous_height = 0
        while True:
            current_height = await page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(delay)
            previous_height = current_height

    async def take_screenshot(
        self,
        page: Page,
        path: str,
        full_page: bool = True,
    ) -> None:
        """
        Take a screenshot for debugging.

        Args:
            page: Page to screenshot
            path: File path to save
            full_page: Capture full page or just viewport
        """
        await page.screenshot(path=path, full_page=full_page)
        logger.debug(f"Screenshot saved to {path}")
