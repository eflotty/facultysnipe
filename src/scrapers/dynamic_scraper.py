"""
Dynamic JavaScript scraper using Playwright
Handles pagination, infinite scroll, and lazy-loading
"""
from typing import List, Optional
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper, Faculty
import sys
import os
import time
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import SCRAPER_TIMEOUT, USER_AGENT


class DynamicScraper(BaseScraper):
    """
    Playwright-based scraper for JavaScript-rendered pages
    Supports pagination, infinite scroll, and lazy-loading
    """

    def scrape(self) -> List[Faculty]:
        """
        Scrape faculty data using Playwright headless browser
        Handles pagination and scrolling automatically

        Returns:
            List of Faculty objects
        """
        self.logger.info(f"Scraping {self.url} with dynamic scraper (Playwright)")

        all_faculty = []
        pages_scraped = 0
        max_pages = 10  # Safety limit

        try:
            with sync_playwright() as p:
                # Launch headless browser
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=USER_AGENT)
                page = context.new_page()

                current_url = self.url
                visited_urls = set()

                while current_url and pages_scraped < max_pages:
                    if current_url in visited_urls:
                        break

                    visited_urls.add(current_url)
                    pages_scraped += 1

                    self.logger.info(f"Scraping page {pages_scraped}: {current_url}")

                    # Navigate to page
                    page.goto(current_url, timeout=SCRAPER_TIMEOUT * 1000, wait_until='networkidle')

                    # Wait for content (subclass-specific)
                    self.wait_for_content(page)

                    # CRITICAL: Scroll to bottom to load ALL lazy content
                    self._scroll_to_bottom(page)

                    # Get rendered HTML after scrolling
                    html = page.content()
                    soup = BeautifulSoup(html, 'lxml')

                    # Call subclass-specific parsing
                    page_faculty = self.parse(soup, page)
                    all_faculty.extend(page_faculty)

                    self.logger.info(f"Found {len(page_faculty)} faculty on page {pages_scraped}")

                    # Check for next page
                    next_url = self._find_next_page(page, soup, current_url)
                    current_url = next_url

                    # Respectful delay between pages
                    if current_url:
                        time.sleep(2)

                # Close browser
                browser.close()

                if pages_scraped > 1:
                    self.logger.info(f"Scraped {pages_scraped} pages total")

                # Deduplicate faculty across pages
                all_faculty = self._deduplicate_faculty(all_faculty)

                # Validate results
                validated = self.validate(all_faculty)

                self.logger.info(f"Successfully scraped {len(validated)} faculty members")
                return validated

        except Exception as e:
            self.logger.error(f"Failed to scrape {self.url} with Playwright: {e}")
            raise

    def _scroll_to_bottom(self, page: Page, max_scrolls=15):
        """
        Scroll to bottom of page to load ALL lazy-loaded content
        Handles infinite scroll by detecting when no new content loads

        Args:
            page: Playwright Page object
            max_scrolls: Maximum number of scroll attempts
        """
        self.logger.info("Scrolling to bottom to load all lazy content...")

        previous_height = page.evaluate("document.body.scrollHeight")
        scrolls = 0
        no_change_count = 0

        while scrolls < max_scrolls:
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            # Wait for content to load (2 seconds for slow connections)
            time.sleep(2)

            # Check if new content loaded
            new_height = page.evaluate("document.body.scrollHeight")

            if new_height == previous_height:
                no_change_count += 1
                # If height hasn't changed twice in a row, we're done
                if no_change_count >= 2:
                    self.logger.info(f"✓ Reached bottom after {scrolls + 1} scrolls")
                    break
            else:
                no_change_count = 0  # Reset if we found new content

            previous_height = new_height
            scrolls += 1

            self.logger.debug(f"Scroll {scrolls}/{max_scrolls}: Height {new_height}px")

        if scrolls >= max_scrolls:
            self.logger.warning(f"⚠ Hit max scrolls ({max_scrolls}) - may have missed content")

        # Scroll back to top for consistency
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)

    def _find_next_page(self, page: Page, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Find next page link using Playwright selectors

        Args:
            page: Playwright Page object
            soup: BeautifulSoup object
            current_url: Current page URL

        Returns:
            Next page URL or None
        """
        # Try Playwright selectors first (better for JS-rendered content)
        next_selectors = [
            'a.next',
            'a[rel="next"]',
            'button.next',
            'a:has-text("Next")',
            'button:has-text("Next")',
            'a[aria-label*="next" i]',
            'button[aria-label*="next" i]',
            'a.pagination-next',
            'li.next > a',
        ]

        for selector in next_selectors:
            try:
                next_elem = page.query_selector(selector)
                if next_elem and next_elem.is_visible():
                    href = next_elem.get_attribute('href')
                    if href and href != '#' and 'javascript:' not in href.lower():
                        from urllib.parse import urljoin
                        next_url = urljoin(current_url, href)
                        self.logger.info(f"Found next page: {next_url}")
                        return next_url
            except Exception as e:
                self.logger.debug(f"Selector '{selector}' failed: {e}")
                continue

        # Fallback to BeautifulSoup method
        return self._find_next_page_soup(soup, current_url)

    def _find_next_page_soup(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Find next page using BeautifulSoup (fallback)

        Args:
            soup: BeautifulSoup object
            current_url: Current page URL

        Returns:
            Next page URL or None
        """
        # Common pagination patterns
        pagination_patterns = [
            ('a', {'class': re.compile(r'next|pagination.*next', re.I)}),
            ('a', {'rel': 'next'}),
            ('a', {'aria-label': re.compile(r'next', re.I)}),
            ('link', {'rel': 'next'}),
        ]

        for tag, attrs in pagination_patterns:
            next_link = soup.find(tag, attrs)
            if next_link and next_link.get('href'):
                href = next_link['href']
                if href != '#' and 'javascript:' not in href.lower():
                    from urllib.parse import urljoin
                    next_url = urljoin(current_url, href)
                    self.logger.info(f"Found next page (soup): {next_url}")
                    return next_url

        return None

    def _deduplicate_faculty(self, faculty_list: List[Faculty]) -> List[Faculty]:
        """
        Remove duplicate faculty based on faculty_id

        Args:
            faculty_list: List potentially containing duplicates

        Returns:
            Deduplicated list
        """
        seen_ids = set()
        unique_faculty = []

        for faculty in faculty_list:
            if faculty.faculty_id not in seen_ids:
                seen_ids.add(faculty.faculty_id)
                unique_faculty.append(faculty)
            else:
                self.logger.debug(f"Skipping duplicate: {faculty.name}")

        if len(faculty_list) != len(unique_faculty):
            self.logger.info(f"Removed {len(faculty_list) - len(unique_faculty)} duplicates")

        return unique_faculty

    def wait_for_content(self, page: Page):
        """
        Wait for page content to load
        Default: wait for common faculty selectors or 3 seconds

        Args:
            page: Playwright Page object
        """
        # Try to wait for common faculty content selectors
        faculty_selectors = [
            '.faculty',
            '.people',
            '.person',
            '.profile',
            '[class*="faculty"]',
            '[class*="people"]',
        ]

        for selector in faculty_selectors:
            try:
                page.wait_for_selector(selector, timeout=5000)
                self.logger.debug(f"Found content with selector: {selector}")
                return
            except:
                continue

        # Fallback: just wait 3 seconds
        self.logger.debug("Using default 3 second wait")
        page.wait_for_timeout(3000)

    def parse(self, soup: BeautifulSoup, page: Page) -> List[Faculty]:
        """
        Parse faculty data from rendered HTML
        Must be implemented by subclass

        Args:
            soup: BeautifulSoup parsed HTML
            page: Playwright Page object (for additional interactions)

        Returns:
            List of Faculty objects
        """
        raise NotImplementedError("Subclass must implement parse() method")
