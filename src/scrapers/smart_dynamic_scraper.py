"""
Smart Dynamic Scraper - Combines Smart Universal Scraper with Playwright
Handles JavaScript, infinite scroll, lazy-loading, and pagination
"""
from typing import List
from playwright.sync_api import Page
from bs4 import BeautifulSoup
from .dynamic_scraper import DynamicScraper
from .smart_universal_scraper import SmartUniversalScraper
from .base_scraper import Faculty


class SmartDynamicScraper(DynamicScraper):
    """
    Universal dynamic scraper that uses Playwright for rendering
    and SmartUniversalScraper logic for parsing

    Best for JavaScript-heavy sites with lazy-loading
    """

    def __init__(self, url: str, university_id: str):
        """Initialize scraper"""
        super().__init__(url, university_id)
        # Create smart scraper instance for parsing logic
        self.smart_scraper = SmartUniversalScraper(url, university_id)

    def parse(self, soup: BeautifulSoup, page: Page) -> List[Faculty]:
        """
        Parse faculty using SmartUniversalScraper strategies

        Args:
            soup: BeautifulSoup parsed HTML
            page: Playwright Page object

        Returns:
            List of Faculty objects
        """
        self.logger.info("Parsing with Smart Universal strategies...")

        # Use SmartUniversalScraper's _scrape_single_page method
        # which tries all strategies and merges results
        faculty_list = self.smart_scraper._scrape_single_page(soup)

        # Enrich with profile data
        faculty_list = self.smart_scraper._enrich_faculty_data(faculty_list, soup)

        return faculty_list
