"""
Scrapers package
"""
from .base_scraper import BaseScraper, Faculty
from .static_scraper import StaticScraper
from .dynamic_scraper import DynamicScraper
from .registry import ScraperRegistry

__all__ = ['BaseScraper', 'Faculty', 'StaticScraper', 'DynamicScraper', 'ScraperRegistry']
