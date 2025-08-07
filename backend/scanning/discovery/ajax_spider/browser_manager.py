# scanning/discovery/ajax_spider/browser_manager.py

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import Browser, BrowserContext, async_playwright

logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    headless: bool = True
    user_agent: str = "SecurityScannerBot/1.0"
    viewport_width: int = 1366
    viewport_height: int = 768
    timeout: int = 30000
    ignore_https_errors: bool = True


class BrowserManager:
    """Manages Playwright browser instance for AJAX spider"""

    def __init__(self, config: BrowserConfig):
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def initialize(self):
        """Initialize browser and context"""
        playwright = await async_playwright().start()

        self.browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        self.context = await self.browser.new_context(
            viewport_width=self.config.viewport_width,
            viewport_height=self.config.viewport_height,
            user_agent=self.config.user_agent,
            ignore_https_errors=self.config.ignore_https_errors,
        )

        # Set default timeout
        self.context.set_default_timeout(self.config.timeout)

        return self.context

    async def close(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
