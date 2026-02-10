"""
TEMPLATE for new university scrapers
Copy this file and modify for your specific university

Instructions:
1. Copy this file to a new file (e.g., stanford_biology.py)
2. Rename the class (e.g., StanfordBiologyScraper)
3. Update the docstring with actual URL
4. Choose StaticScraper or DynamicScraper based on page type
5. Implement parse() method with correct CSS selectors
6. Test locally before deploying
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Choose one:
from scrapers.static_scraper import StaticScraper, Faculty
# OR
# from scrapers.dynamic_scraper import DynamicScraper, Faculty
# from playwright.sync_api import Page

from typing import List
from bs4 import BeautifulSoup


class TemplateUniversityScraper(StaticScraper):
    """
    Template scraper for [University Name] [Department Name]
    URL: [Insert actual faculty page URL here]

    Static HTML: Use StaticScraper (faster, simpler)
    JavaScript-rendered: Use DynamicScraper (slower, for React/Vue/Angular sites)
    """

    def parse(self, soup: BeautifulSoup) -> List[Faculty]:
        """
        Parse faculty data from HTML

        Steps:
        1. Inspect the page source to find CSS selectors
        2. Find the container for each faculty member
        3. Extract: name (required), title, email, profile_url, etc.
        4. Return list of Faculty objects

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of Faculty objects
        """
        faculty_list = []

        # Step 1: Find all faculty card/entry containers
        # REPLACE '.faculty-card' with actual selector from page
        faculty_cards = soup.select('.faculty-card')

        self.logger.info(f"Found {len(faculty_cards)} potential faculty entries")

        # Step 2: Loop through each card and extract data
        for card in faculty_cards:
            try:
                # Extract name (REQUIRED)
                # REPLACE '.name' with actual selector
                name_elem = card.select_one('.name')
                if not name_elem:
                    continue  # Skip if no name found

                name = self._clean_text(name_elem.get_text())

                # Extract title/position (OPTIONAL)
                # REPLACE '.title' with actual selector
                title = None
                title_elem = card.select_one('.title')
                if title_elem:
                    title = self._clean_text(title_elem.get_text())

                # Extract email (OPTIONAL but recommended)
                email = self._extract_email(card)  # Helper method

                # Extract profile URL (OPTIONAL)
                profile_url = None
                profile_link = card.select_one('a[href]')  # REPLACE with actual selector
                if profile_link:
                    profile_url = profile_link['href']
                    # Make absolute URL if needed
                    if profile_url.startswith('/'):
                        profile_url = f"https://university.edu{profile_url}"  # REPLACE domain

                # Extract department (OPTIONAL)
                department = "Department Name"  # REPLACE with actual department

                # Extract phone (OPTIONAL)
                phone = None
                phone_elem = card.select_one('.phone')  # REPLACE with actual selector
                if phone_elem:
                    phone = self._clean_text(phone_elem.get_text())

                # Extract research interests (OPTIONAL)
                research_interests = None
                research_elem = card.select_one('.research')  # REPLACE with actual selector
                if research_elem:
                    research_interests = self._clean_text(research_elem.get_text())

                # Create Faculty object
                faculty = Faculty(
                    name=name,
                    title=title,
                    email=email,
                    profile_url=profile_url,
                    department=department,
                    phone=phone,
                    research_interests=research_interests
                )

                faculty_list.append(faculty)

            except Exception as e:
                self.logger.warning(f"Failed to parse faculty card: {e}")
                continue

        return faculty_list


# IF USING DynamicScraper (JavaScript-rendered pages):
"""
class TemplateUniversityScraperDynamic(DynamicScraper):
    '''
    Template for JavaScript-rendered pages
    '''

    def wait_for_content(self, page: Page):
        '''Wait for JS content to load'''
        try:
            # REPLACE '.faculty-card' with actual selector
            page.wait_for_selector('.faculty-card', timeout=30000)
            page.wait_for_timeout(2000)  # Extra wait for lazy loading
            self.logger.info("Content loaded")
        except Exception as e:
            self.logger.warning(f"Timeout waiting for content: {e}")

    def parse(self, soup: BeautifulSoup, page: Page) -> List[Faculty]:
        '''Parse rendered HTML - same as static version above'''
        # Copy the parse() implementation from above
        pass
"""
