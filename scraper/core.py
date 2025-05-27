"""
Core scraper module for news websites
Implements a hybrid approach with Playwright and Requests
"""

import os
import json
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("news_scraper")

class BaseScraper:
    """Base class for all scrapers with common functionality"""
    
    def __init__(self, base_url: str, output_dir: str = "output"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.results = []
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
    def random_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """Implement random delay between requests for ethical scraping"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"Waiting for {delay:.2f} seconds")
        time.sleep(delay)
        
    def save_results(self, filename: str = None):
        """Save scraped results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain = self.base_url.split("//")[-1].split("/")[0].replace(".", "_")
            filename = f"{domain}_{timestamp}.json"
            
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "source": self.base_url,
                "timestamp": datetime.now().isoformat(),
                "articles": self.results
            }, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved {len(self.results)} results to {filepath}")
        return filepath
    
    def scrape(self, query: str, max_pages: int = 1):
        """
        Abstract method to be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement scrape method")


class RequestsScraper(BaseScraper):
    """Scraper using Requests + BeautifulSoup for static sites"""
    
    def __init__(self, base_url: str, output_dir: str = "output"):
        super().__init__(base_url, output_dir)
        self.session = None
        
    def _init_session(self):
        """Initialize requests session with proper headers"""
        import requests
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        })
        
    def scrape(self, query: str, max_pages: int = 1):
        """
        Scrape using requests and BeautifulSoup
        To be implemented by site-specific subclasses
        """
        if not self.session:
            self._init_session()
            
        # Implementation will be site-specific
        raise NotImplementedError("Site-specific implementation required")


class PlaywrightScraper(BaseScraper):
    """Scraper using Playwright for JavaScript-heavy sites"""
    
    def __init__(self, base_url: str, output_dir: str = "output", headless: bool = True):
        super().__init__(base_url, output_dir)
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless
        
    async def _init_browser(self):
        """Initialize Playwright browser"""
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.page = await self.context.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(30000)
        
    async def close(self):
        """Close browser and context"""
        if self.browser:
            await self.browser.close()
            
    async def scrape(self, query: str, max_pages: int = 1):
        """
        Scrape using Playwright
        To be implemented by site-specific subclasses
        """
        if not self.browser:
            await self._init_browser()
            
        # Implementation will be site-specific
        raise NotImplementedError("Site-specific implementation required")


class ScraperFactory:
    """Factory to create appropriate scraper for each site"""
    
    @staticmethod
    def create_scraper(url: str, output_dir: str = "output") -> BaseScraper:
        """Create appropriate scraper based on URL"""
        domain = url.split("//")[-1].split("/")[0].lower()
        
        # JavaScript-heavy sites
        if "adnoc.ae" in domain or "aljazeera.com" in domain:
            return PlaywrightScraper(url, output_dir)
        
        # Mixed sites - defaulting to Playwright for safety
        elif "al-monitor.com" in domain or "alarabiya.net" in domain:
            return PlaywrightScraper(url, output_dir)
        
        # More static sites
        elif "africanreview.com" in domain or "ahram.org.eg" in domain:
            return RequestsScraper(url, output_dir)
        
        # Default to Playwright for unknown sites
        else:
            logger.info(f"Unknown domain {domain}, defaulting to Playwright scraper")
            return PlaywrightScraper(url, output_dir)
