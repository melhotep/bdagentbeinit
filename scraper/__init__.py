"""
Package initialization file for the scraper module
"""

from .core import BaseScraper, RequestsScraper, PlaywrightScraper, ScraperFactory
from .site_scrapers import get_scraper_for_url

__all__ = [
    'BaseScraper',
    'RequestsScraper',
    'PlaywrightScraper',
    'ScraperFactory',
    'get_scraper_for_url'
]
