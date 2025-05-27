"""
Site-specific scrapers for news websites
Implements concrete scrapers for each supported site
"""

import asyncio
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import requests
from datetime import datetime

from .core import RequestsScraper, PlaywrightScraper, logger


class AdnocScraper(PlaywrightScraper):
    """Scraper for ADNOC website"""
    
    async def scrape(self, query: str, max_pages: int = 1):
        """Scrape ADNOC search results"""
        if not self.browser:
            await self._init_browser()
            
        search_url = f"{self.base_url}?query={query.replace(' ', '+')}"
        logger.info(f"Scraping ADNOC: {search_url}")
        
        try:
            # Navigate to search page
            await self.page.goto(search_url, wait_until="networkidle")
            
            # Wait for results to load
            await self.page.wait_for_selector(".search-results", timeout=10000)
            
            # Check if we have results
            no_results = await self.page.query_selector_all("text=we found 0 matches")
            if no_results:
                logger.info(f"No results found for query: {query}")
                return []
                
            # Extract results
            for page_num in range(max_pages):
                # Wait for results to be visible
                await self.page.wait_for_selector(".search-result-item", timeout=5000)
                
                # Extract data from current page
                results = await self.page.query_selector_all(".search-result-item")
                
                for result in results:
                    title_el = await result.query_selector(".title")
                    date_el = await result.query_selector(".date")
                    snippet_el = await result.query_selector(".snippet")
                    link_el = await result.query_selector("a")
                    
                    if title_el and link_el:
                        title = await title_el.inner_text()
                        link = await link_el.get_attribute("href")
                        date = await date_el.inner_text() if date_el else ""
                        snippet = await snippet_el.inner_text() if snippet_el else ""
                        
                        self.results.append({
                            "title": title.strip(),
                            "url": link,
                            "date": date.strip(),
                            "snippet": snippet.strip(),
                            "source": "ADNOC",
                            "query": query
                        })
                
                # Check if there's a next page and we haven't reached max_pages
                if page_num < max_pages - 1:
                    next_button = await self.page.query_selector(".pagination-next:not(.disabled)")
                    if next_button:
                        await next_button.click()
                        await self.page.wait_for_load_state("networkidle")
                        self.random_delay(2, 4)
                    else:
                        break
                        
            logger.info(f"Scraped {len(self.results)} results from ADNOC")
            return self.results
            
        except Exception as e:
            logger.error(f"Error scraping ADNOC: {str(e)}")
            return []
        finally:
            await self.close()


class AhramScraper(RequestsScraper):
    """Scraper for Ahram Online website"""
    
    def scrape(self, query: str, max_pages: int = 1):
        """Scrape Ahram Online search results"""
        if not self.session:
            self._init_session()
            
        search_url = f"{self.base_url}?Text={query.replace(' ', '%20')}"
        logger.info(f"Scraping Ahram Online: {search_url}")
        
        try:
            response = self.session.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all result items - updated selector based on page inspection
            results = soup.select("table tbody tr")
            
            for result in results:
                try:
                    # Extract data with updated selectors
                    category_el = result.select_one("p:first-child")
                    title_el = result.select_one("div h5 a")
                    date_el = result.select_one("p span:first-of-type")
                    snippet_el = result.select_one("p:last-of-type span")
                    
                    if title_el:
                        title = title_el.text.strip()
                        link = title_el.get("href", "")
                        # Make relative URLs absolute
                        if link and not link.startswith(("http://", "https://")):
                            link = f"https://english.ahram.org.eg{link}"
                            
                        category_text = category_el.text.strip() if category_el else ""
                        date_text = date_el.text.strip() if date_el else ""
                        snippet = snippet_el.text.strip() if snippet_el else ""
                        
                        self.results.append({
                            "title": title,
                            "url": link,
                            "date": date_text,
                            "category": category_text,
                            "snippet": snippet,
                            "source": "Ahram Online",
                            "query": query
                        })
                except Exception as e:
                    logger.error(f"Error parsing result item: {str(e)}")
                    continue
            
            logger.info(f"Scraped {len(self.results)} results from Ahram Online")
            return self.results
            
        except Exception as e:
            logger.error(f"Error scraping Ahram Online: {str(e)}")
            return []


class AlMonitorScraper(PlaywrightScraper):
    """Scraper for Al-Monitor website"""
    
    async def scrape(self, query: str, max_pages: int = 1):
        """Scrape Al-Monitor search results"""
        if not self.browser:
            await self._init_browser()
            
        search_url = f"{self.base_url}?text={query.replace(' ', '+')}"
        logger.info(f"Scraping Al-Monitor: {search_url}")
        
        try:
            # Navigate to search page
            await self.page.goto(search_url, wait_until="networkidle")
            
            # Wait for results to load
            await self.page.wait_for_selector("article", timeout=10000)
            
            # Extract results for each page
            for page_num in range(max_pages):
                # Wait for article elements to be visible
                await asyncio.sleep(2)  # Additional wait for dynamic content
                
                # Extract data from current page
                articles = await self.page.query_selector_all("article")
                
                for article in articles:
                    try:
                        title_el = await article.query_selector("h2 a, h3 a")
                        source_el = await article.query_selector(".source")
                        date_el = await article.query_selector("time")
                        
                        if title_el:
                            title = await title_el.inner_text()
                            link = await title_el.get_attribute("href")
                            # Make relative URLs absolute
                            if link and not link.startswith(("http://", "https://")):
                                link = f"https://www.al-monitor.com{link}"
                                
                            source = await source_el.inner_text() if source_el else ""
                            date = await date_el.inner_text() if date_el else ""
                            
                            self.results.append({
                                "title": title.strip(),
                                "url": link,
                                "date": date.strip(),
                                "source": f"Al-Monitor: {source.strip()}" if source else "Al-Monitor",
                                "query": query
                            })
                    except Exception as e:
                        logger.error(f"Error parsing article: {str(e)}")
                        continue
                
                # Check if there's a next page and we haven't reached max_pages
                if page_num < max_pages - 1:
                    next_button = await self.page.query_selector("a.next, a:has-text('Next')")
                    if next_button:
                        await next_button.click()
                        await self.page.wait_for_load_state("networkidle")
                        self.random_delay(2, 4)
                    else:
                        break
                        
            logger.info(f"Scraped {len(self.results)} results from Al-Monitor")
            return self.results
            
        except Exception as e:
            logger.error(f"Error scraping Al-Monitor: {str(e)}")
            return []
        finally:
            await self.close()


class AlJazeeraScraper(PlaywrightScraper):
    """Scraper for Al Jazeera website"""
    
    async def scrape(self, query: str, max_pages: int = 1):
        """Scrape Al Jazeera search results"""
        if not self.browser:
            await self._init_browser()
            
        search_url = f"{self.base_url}?sort=date"
        logger.info(f"Scraping Al Jazeera: {search_url}")
        
        try:
            # Navigate to search page
            await self.page.goto(search_url, wait_until="networkidle")
            
            # Input search query
            await self.page.fill('input[placeholder="Search"]', query)
            await self.page.press('input[placeholder="Search"]', 'Enter')
            
            # Wait for results to load
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)  # Additional wait for dynamic content
            
            # Extract results for each page
            for page_num in range(max_pages):
                # Wait for article elements to be visible
                article_selector = "article"
                await self.page.wait_for_selector(article_selector, timeout=10000)
                
                # Extract data from current page
                articles = await self.page.query_selector_all(article_selector)
                
                for article in articles:
                    title_el = await article.query_selector("h3 a, h2 a")
                    date_el = await article.query_selector("time, .date")
                    category_el = await article.query_selector(".category")
                    snippet_el = await article.query_selector("p")
                    
                    if title_el:
                        title = await title_el.inner_text()
                        link = await title_el.get_attribute("href")
                        # Make relative URLs absolute
                        if link and not link.startswith(("http://", "https://")):
                            link = f"https://www.aljazeera.com{link}"
                            
                        date = await date_el.inner_text() if date_el else ""
                        category = await category_el.inner_text() if category_el else ""
                        snippet = await snippet_el.inner_text() if snippet_el else ""
                        
                        self.results.append({
                            "title": title.strip(),
                            "url": link,
                            "date": date.strip(),
                            "category": category.strip(),
                            "snippet": snippet.strip(),
                            "source": "Al Jazeera",
                            "query": query
                        })
                
                # Check if there's a next page and we haven't reached max_pages
                if page_num < max_pages - 1:
                    next_button = await self.page.query_selector("button:has-text('Next')")
                    if next_button:
                        await next_button.click()
                        await self.page.wait_for_load_state("networkidle")
                        self.random_delay(2, 4)
                    else:
                        break
                        
            logger.info(f"Scraped {len(self.results)} results from Al Jazeera")
            return self.results
            
        except Exception as e:
            logger.error(f"Error scraping Al Jazeera: {str(e)}")
            return []
        finally:
            await self.close()


class AfricanReviewScraper(RequestsScraper):
    """Scraper for African Review website"""
    
    def scrape(self, query: str, max_pages: int = 1):
        """Scrape African Review search results"""
        if not self.session:
            self._init_session()
            
        search_url = f"{self.base_url}?q={query.replace(' ', '+')}&Search="
        logger.info(f"Scraping African Review: {search_url}")
        
        try:
            response = self.session.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Updated selectors based on page inspection
            results = []
            
            # Try different possible selectors for search results
            result_containers = soup.select(".search-result, .search-results li, .article-list li")
            
            if not result_containers:
                # If no results found with specific selectors, try to find any article-like elements
                result_containers = soup.select("article, .article, .news-item")
            
            # If still no results, try to extract from the first few h3 elements
            if not result_containers:
                headings = soup.select("h3 a, h2 a")
                for heading in headings[:10]:  # Limit to first 10 to avoid unrelated content
                    title = heading.text.strip()
                    link = heading.get("href", "")
                    # Make relative URLs absolute
                    if link and not link.startswith(("http://", "https://")):
                        link = f"https://africanreview.com{link}"
                    
                    self.results.append({
                        "title": title,
                        "url": link,
                        "date": "",
                        "snippet": "",
                        "source": "African Review",
                        "query": query
                    })
            else:
                # Process results from containers
                for result in result_containers:
                    try:
                        title_el = result.select_one("h3 a, h2 a, .title a")
                        date_el = result.select_one("time, .date, .meta time")
                        snippet_el = result.select_one("p, .summary, .excerpt")
                        
                        if title_el:
                            title = title_el.text.strip()
                            link = title_el.get("href", "")
                            # Make relative URLs absolute
                            if link and not link.startswith(("http://", "https://")):
                                link = f"https://africanreview.com{link}"
                                
                            date_text = date_el.text.strip() if date_el else ""
                            snippet = snippet_el.text.strip() if snippet_el else ""
                            
                            self.results.append({
                                "title": title,
                                "url": link,
                                "date": date_text,
                                "snippet": snippet,
                                "source": "African Review",
                                "query": query
                            })
                    except Exception as e:
                        logger.error(f"Error parsing result item: {str(e)}")
                        continue
            
            logger.info(f"Scraped {len(self.results)} results from African Review")
            return self.results
            
        except Exception as e:
            logger.error(f"Error scraping African Review: {str(e)}")
            return []


# Map domains to scraper classes
SCRAPER_MAP = {
    "adnoc.ae": AdnocScraper,
    "ahram.org.eg": AhramScraper,
    "aljazeera.com": AlJazeeraScraper,
    "africanreview.com": AfricanReviewScraper,
    "al-monitor.com": AlMonitorScraper,
    # Add more mappings as implemented
}


def get_scraper_for_url(url: str, output_dir: str = "output"):
    """Get the appropriate scraper for a given URL"""
    domain = url.split("//")[-1].split("/")[0].lower()
    
    for key, scraper_class in SCRAPER_MAP.items():
        if key in domain:
            return scraper_class(url, output_dir)
    
    # Default to base classes based on domain analysis
    from .core import ScraperFactory
    return ScraperFactory.create_scraper(url, output_dir)
