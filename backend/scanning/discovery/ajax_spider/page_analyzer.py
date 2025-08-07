# scanning/discovery/ajax_spider/page_analyzer.py

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import Page

logger = logging.getLogger(__name__)


@dataclass
class ExtractedData:
    urls: List[Dict]
    forms: List[Dict]
    javascript_objects: Dict
    dynamic_content: Dict


class PageAnalyzer:
    """Analyzes webpage content for AJAX spider"""

    def __init__(self):
        pass

    async def analyze(self, page: Page, url: str) -> ExtractedData:
        """Analyze page content"""
        # Extract content using both Playwright and BeautifulSoup
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract different types of data
        urls = await self._extract_urls(page, soup, url)
        forms = await self._extract_forms(page, soup, url)
        javascript_objects = await self._extract_javascript_objects(page)
        dynamic_content = await self._detect_dynamic_content(page)

        return ExtractedData(
            urls=urls,
            forms=forms,
            javascript_objects=javascript_objects,
            dynamic_content=dynamic_content,
        )

    async def _extract_urls(
        self, page: Page, soup: BeautifulSoup, base_url: str
    ) -> List[Dict]:
        """Extract URLs from page"""
        urls = []

        # Extract from links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            full_url = urljoin(base_url, href)

            urls.append(
                {"url": full_url, "source": "link", "text": text, "parent": base_url}
            )

        # Extract from JavaScript
        js_urls = await page.evaluate(
            """
            () => {
                const urls = new Set();
                
                // Common data attributes
                document.querySelectorAll('[data-url], [data-href]').forEach(el => {
                    ['data-url', 'data-href'].forEach(attr => {
                        const url = el.getAttribute(attr);
                        if (url) urls.add(url);
                    });
                });
                
                // SPA routes
                document.querySelectorAll('[href^="#/"], [href^="#!"]').forEach(el => {
                    const href = el.getAttribute('href');
                    if (href) urls.add(href);
                });
                
                return Array.from(urls);
            }
        """
        )

        for js_url in js_urls:
            full_url = urljoin(base_url, js_url)
            urls.append(
                {
                    "url": full_url,
                    "source": "javascript",
                    "text": "",
                    "parent": base_url,
                }
            )

        return urls

    async def _extract_forms(
        self, page: Page, soup: BeautifulSoup, base_url: str
    ) -> List[Dict]:
        """Extract forms from page"""
        forms = []

        for form in soup.find_all("form"):
            form_data = {
                "action": urljoin(base_url, form.get("action", "")),
                "method": form.get("method", "get").upper(),
                "inputs": [],
                "url": base_url,
            }

            # Extract input fields
            for input_elem in form.find_all(["input", "textarea", "select"]):
                input_data = {
                    "name": input_elem.get("name", ""),
                    "type": input_elem.get("type", "text"),
                    "value": input_elem.get("value", ""),
                    "required": input_elem.has_attr("required"),
                }
                form_data["inputs"].append(input_data)

            forms.append(form_data)

        return forms

    async def _extract_javascript_objects(self, page: Page) -> Dict:
        """Extract JavaScript objects and frameworks"""
        js_objects = await page.evaluate(
            """
            () => {
                const objects = {};
                
                // Detect frameworks
                if (window.React) objects.framework = 'React';
                else if (window.Vue) objects.framework = 'Vue';
                else if (window.ng) objects.framework = 'Angular';
                
                // Get configuration objects
                if (window.APP_CONFIG) objects.appConfig = window.APP_CONFIG;
                if (window.API_ENDPOINTS) objects.apiEndpoints = window.API_ENDPOINTS;
                
                // Get routes for SPAs
                if (window._reactRouter) objects.routes = window._reactRouter;
                
                return objects;
            }
        """
        )

        return js_objects

    async def _detect_dynamic_content(self, page: Page) -> Dict:
        """Detect dynamic content patterns"""
        dynamic_content = {}

        # Check for infinite scroll
        dynamic_content["infinite_scroll"] = await page.evaluate(
            """
            () => {
                const scrollEvents = [];
                window.addEventListener('scroll', () => scrollEvents.push(Date.now()));
                window.scrollTo(0, document.body.scrollHeight);
                setTimeout(() => window.scrollTo(0, 0), 100);
                return scrollEvents.length > 0;
            }
        """
        )

        # Check for lazy loading
        dynamic_content["lazy_loading"] = await page.evaluate(
            """
            () => {
                const lazyElements = document.querySelectorAll('[data-lazy], [loading="lazy"]');
                return lazyElements.length > 0;
            }
        """
        )

        return dynamic_content
