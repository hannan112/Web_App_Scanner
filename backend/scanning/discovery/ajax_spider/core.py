# scanning/discovery/ajax_spider/core.py

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from .browser_manager import BrowserManager, BrowserConfig
from .request_tracker import RequestTracker
from .page_analyzer import PageAnalyzer
from scanning.models.scan import Scan

logger = logging.getLogger(__name__)


class AjaxSpider:
    """Core AJAX spider using Playwright for modern web apps"""
    
    def __init__(
        self,
        start_url: str,
        scan: Scan,
        max_depth: int = 3,
        max_pages: int = 100,
        max_duration: int = 300,
        headless: bool = True,
        user_agent: str = None
    ):
        self.start_url = start_url
        self.scan = scan
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.max_duration = max_duration
        
        # Initialize components
        browser_config = BrowserConfig(
            headless=headless,
            user_agent=user_agent or "SecurityScannerBot/1.0"
        )
        self.browser_manager = BrowserManager(browser_config)
        self.request_tracker = RequestTracker()
        self.page_analyzer = PageAnalyzer()
        
        # Tracking data
        self.visited_urls: Set[str] = set()
        self.url_queue: List[Dict] = []
        self.pages_crawled = 0
        self.start_time = None
        self.base_domain = urlparse(start_url).netloc
        
        # Results
        self.discovered_urls: List[Dict] = []
        self.discovered_forms: List[Dict] = []
        self.ajax_requests: List[Dict] = []
        self.javascript_objects: Dict = {}
    
    async def crawl(self, progress_callback=None) -> Dict:
        """Start crawling process"""
        self.start_time = datetime.now()
        context = None
        
        try:
            # Initialize browser
            context = await self.browser_manager.initialize()
            await self.request_tracker.setup_interception(context)
            
            # Rest of crawl code...
            
        except Exception as e:
            logger.error(f"Crawl error: {str(e)}")
            raise
        finally:
            # Only close if initialization succeeded
            if context is not None:
                await self.browser_manager.close()
        
        return self._compile_results()
    
    async def _crawl_page(self, context, url_info):
        """Crawl single page"""
        url = url_info['url']
        depth = url_info['depth']
        
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        self.pages_crawled += 1
        
        try:
            page = await context.new_page()
            
            # Navigate to page
            await page.goto(url, wait_until="domcontentloaded")
            
            # Wait for dynamic content
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Analyze page
            analysis = await self.page_analyzer.analyze(page, url)
            
            # Process extracted data
            self._process_extracted_data(analysis, url, depth)
            
            # Simulate interactions
            await self._simulate_interactions(page)
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
    
    def _process_extracted_data(self, analysis, url, depth):
        """Process and store extracted data"""
        # Store URLs
        for url_data in analysis.urls:
            if self._should_crawl(url_data['url']) and depth + 1 <= self.max_depth:
                self.url_queue.append({
                    'url': url_data['url'],
                    'depth': depth + 1,
                    'parent': url
                })
            self.discovered_urls.append(url_data)
        
        # Store forms
        for form_data in analysis.forms:
            form_data['discovered_at'] = url
            self.discovered_forms.append(form_data)
        
        # Store JavaScript objects
        if analysis.javascript_objects:
            self.javascript_objects[url] = analysis.javascript_objects
    
    async def _simulate_interactions(self, page):
        """Simulate user interactions"""
        try:
            # Click visible buttons
            buttons = await page.query_selector_all('button:visible')
            for button in buttons[:3]:  # Limit to avoid infinite loops
                try:
                    await button.click(timeout=1000)
                    await page.wait_for_timeout(500)
                except:
                    continue
            
            # Handle infinite scroll
            previous_height = await page.evaluate('document.body.scrollHeight')
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(1000)
            new_height = await page.evaluate('document.body.scrollHeight')
            
            # Repeat scroll if new content appears
            if new_height > previous_height:
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(1000)
            
        except Exception as e:
            logger.debug(f"Interaction error: {str(e)}")
    
    def _should_crawl(self, url: str) -> bool:
        """Check if URL should be crawled"""
        try:
            parsed = urlparse(url)
            
            # Basic validation
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Domain check
            if parsed.netloc != self.base_domain:
                return False
            
            # Skip binary files
            skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip']
            if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
                return False
            
            return True
            
        except:
            return False
    
    def _is_timeout(self) -> bool:
        """Check if crawl has timed out"""
        if not self.start_time:
            return False
        return (datetime.now() - self.start_time).total_seconds() > self.max_duration
    
    def _compile_results(self) -> Dict:
        """Compile final results"""
        # Get request tracker results
        request_results = self.request_tracker.get_results()
        
        return {
            'pages_crawled': self.pages_crawled,
            'urls_discovered': self.discovered_urls,
            'forms_discovered': self.discovered_forms,
            'ajax_requests': request_results['ajax_urls'],
            'request_summary': request_results['summary'],
            'javascript_objects': self.javascript_objects,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': datetime.now().isoformat(),
            'duration': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }