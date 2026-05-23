# scrapers/baseScraper.py
"""
Base Scraper Module

Provides abstract base class for all website scrapers with common functionality:
- Async Playwright browser setup and teardown
- Stealth mode browser launching
- Browser context and page management
- Retry logic and error handling
- Logging and data export
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)
from playwright_stealth import Stealth

from utils.config import ScraperConfig
from utils.logger import get_logger


class BaseScraper(ABC):
    """
    Abstract base class for all website scrapers.

    Handles:
    - Browser initialization with stealth mode
    - Browser context and page management
    - Retry logic for failed requests
    - Data export (JSON/CSV)
    - Error handling and logging
    """

    def __init__(
        self,
        website_name: str,
        version: str = "v1",
    ):
        """
        Initialize the base scraper.

        Args:
            website_name: Name of the website (e.g., 'foodpanda')
            version: Version identifier (e.g., 'v1', 'v2')
            config: ScraperConfig object with custom settings
        """
        self.website_name = website_name
        self.version = version
        self.config = ScraperConfig()
        self.logger = get_logger(f"{website_name}_{version}")

        # Browser-related attributes
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # Data storage
        self.scraped_data: List[Dict[str, Any]] = []

    async def setup_browser(self, extra_http_headers: dict = None) -> None:
        """
        Setup Playwright browser with stealth mode.

        Stealth protection is applied by injecting anti-detection scripts.

        Raises:
            RuntimeError: If browser setup fails
        """
        try:
            # Start playwright normally
            self._playwright = await async_playwright().start()
            self.logger.debug("Playwright started")

            # Launch browser in headless mode
            self._browser = await self._playwright.chromium.launch(
                headless = False,
                args = self.config.browser_args,
            )
            self.logger.info(
                f"Browser launched (headless={self.config.headless})"
            )

            # Create browser context with custom settings
            self._context = await self._browser.new_context(
                viewport=self.config.viewport,
                user_agent=self.config.user_agent,
                locale=self.config.locale,
            )
            self.logger.info("Browser context created")

            # Create main page instance
            self._page = await self._context.new_page()

            # Apply stealth mode to the page using playwright-stealth
            stealth = Stealth()
            await stealth.apply_stealth_async(self._page)
            self.logger.info("✓ Stealth mode applied to page")

            # Set default timeouts
            self._page.set_default_timeout(self.config.timeout)
            self._page.set_default_navigation_timeout(self.config.navigation_timeout)

            self.logger.info("✓ Page instance created and ready with stealth mode")

        except Exception as e:
            self.logger.error(f"✗ Failed to setup browser: {str(e)}")
            await self.teardown_browser()
            raise RuntimeError(f"Browser setup failed: {str(e)}") from e

    async def _setup_event_listeners(self) -> None:
        """
        Setup event listeners for debugging and monitoring.

        Currently logs failed requests and response status codes.
        """
        async def on_response(response):
            """Log response status codes."""
            if response.status >= 400:
                self.logger.warning(
                    f"Response {response.status}: {response.url}"
                )

        async def on_request_failed(request):
            """Log failed requests."""
            self.logger.warning(
                f"Request failed: {request.url} - {request.failure}"
            )

        self._page.on("response", on_response)
        self._page.on("requestfailed", on_request_failed)

    async def teardown_browser(self) -> None:
        """
        Cleanup browser resources.

        Safely closes page, context, and browser instances.
        Should be called in a finally block or context manager.
        """
        try:
            if self._page:
                await self._page.close()
                self.logger.debug("Page closed")

            if self._context:
                await self._context.close()
                self.logger.debug("Browser context closed")

            if self._browser:
                await self._browser.close()
                self.logger.debug("Browser closed")

            if self._playwright:
                await self._playwright.stop()
                self.logger.debug("Playwright stopped")

            self.logger.info("Browser teardown completed")

        except Exception as e:
            self.logger.error(f"Error during teardown: {str(e)}")

    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> None:
        """
        Wait for element to appear on the page.

        Args:
            selector: CSS selector or XPath
            timeout: Timeout in milliseconds (uses default if None)
        """
        if not self._page:
            raise RuntimeError("Page not initialized")

        try:
            await self._page.wait_for_selector(
                selector,
                timeout=timeout or self.config.timeout,
            )
            self.logger.debug(f"✓ Element found: {selector}")
        except Exception as e:
            self.logger.warning(f"✗ Timeout waiting for selector: {selector}")
            raise

    async def scroll_to_bottom(self, pause_time: float = 1.0) -> None:
        """
        Scroll to the bottom of the page to load dynamic content.

        Args:
            pause_time: Pause between scrolls in seconds
        """
        if not self._page:
            raise RuntimeError("Page not initialized")

        last_height = await self._page.evaluate("document.body.scrollHeight")
        self.logger.info("Starting to scroll...")

        while True:
            # Scroll down
            await self._page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(pause_time)

            # Calculate new height
            new_height = await self._page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                self.logger.info("✓ Reached bottom of page")
                break
            last_height = new_height

    async def execute_script(self, script: str) -> Any:
        """
        Execute JavaScript and return result.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of the script execution
        """
        if not self._page:
            raise RuntimeError("Page not initialized")

        try:
            result = await self._page.evaluate(script)
            return result
        except Exception as e:
            self.logger.error(f"✗ Script execution failed: {str(e)}")
            raise

    async def take_screenshot(self, filename: Optional[str] = None) -> None:
        """
        Take a screenshot for debugging.

        Args:
            filename: Output filename (auto-generated if None)
        """
        if not self._page:
            raise RuntimeError("Page not initialized")

        output_dir = Path("output/screenshots")
        output_dir.mkdir(parents=True, exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.website_name}_{self.version}_{timestamp}.png"

        filepath = output_dir / filename
        await self._page.screenshot(path=str(filepath))
        self.logger.info(f"✓ Screenshot saved: {filepath}")

    def export_data(self, format: str = "json") -> Path:
        """
        Export scraped data to file.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            Path to exported file
        """
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.website_name}_{self.version}_{timestamp}"

        try:
            if format.lower() == "json":
                filepath = output_dir / f"{filename}.json"
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)

            elif format.lower() == "csv":
                import csv
                filepath = output_dir / f"{filename}.csv"
                if self.scraped_data:
                    with open(filepath, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=self.scraped_data[0].keys())
                        writer.writeheader()
                        writer.writerows(self.scraped_data)
            else:
                raise ValueError(f"Unsupported format: {format}")

            self.logger.info(f"✓ Data exported to {filepath} ({len(self.scraped_data)} items)")
            return filepath

        except Exception as e:
            self.logger.error(f"✗ Export failed: {str(e)}")
            raise

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Abstract method to be implemented by subclasses.

        Must contain the actual scraping logic.

        Returns:
            List of dictionaries containing scraped data
        """
        pass

    async def run(self) -> List[Dict[str, Any]]:
        """
        Main entry point - setup, scrape, cleanup, export.

        This is a template method that orchestrates the scraping process.

        Returns:
            List of scraped data items
        """
        try:
            self.logger.info(f"Starting scraper: {self.website_name} {self.version}")
            start_time = datetime.now()

            # Setup browser
            await self.setup_browser()

            # Execute scraping logic
            self.scraped_data = await self.scrape()

            # Export data
            self.export_data("json")

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(
                f"✓ Scraping completed successfully in {duration:.2f}s. "
                f"Collected {len(self.scraped_data)} items."
            )

            return self.scraped_data

        except Exception as e:
            self.logger.error(f"✗ Scraping failed: {str(e)}")
            raise

        finally:
            await self.teardown_browser()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.teardown_browser()
        return False