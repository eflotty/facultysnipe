"""
University of Florida Biochemistry Department Scraper
Dynamic Playwright implementation for JavaScript-rendered content
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scrapers.dynamic_scraper import DynamicScraper, Faculty
from playwright.sync_api import Page
from typing import List
from bs4 import BeautifulSoup


class UFBiochemScraper(DynamicScraper):
    """
    Scraper for UF Biochemistry faculty page
    Example URL: https://biochem.med.ufl.edu/faculty/
    """

    def wait_for_content(self, page: Page):
        """
        Wait for JavaScript-rendered faculty content to load

        Args:
            page: Playwright Page object
        """
        try:
            # Wait for faculty cards/list to appear
            # Adjust selector based on actual page structure
            page.wait_for_selector(
                '.faculty-card, .people-listing, .faculty-member, article',
                timeout=30000
            )

            # Additional wait for lazy-loaded images or content
            page.wait_for_timeout(2000)

            self.logger.info("Faculty content loaded successfully")

        except Exception as e:
            self.logger.warning(f"Timeout waiting for content: {e}")
            # Continue anyway - page may have loaded

    def parse(self, soup: BeautifulSoup, page: Page) -> List[Faculty]:
        """
        Parse UF Biochemistry faculty from rendered HTML

        Args:
            soup: BeautifulSoup parsed HTML
            page: Playwright Page object

        Returns:
            List of Faculty objects
        """
        faculty_list = []

        # Find all faculty entries
        # NOTE: Adjust selectors based on actual page structure
        faculty_cards = soup.select('.faculty-card, .people-listing article, .faculty-member')

        if not faculty_cards:
            # Try alternative selectors
            faculty_cards = soup.select('div[data-faculty], .person-card, .bio-card')

        self.logger.info(f"Found {len(faculty_cards)} potential faculty entries")

        for card in faculty_cards:
            try:
                # Extract name
                name = None
                for selector in ['.name', 'h2', 'h3', '.person-name', '.faculty-name', 'a.name']:
                    name_elem = card.select_one(selector)
                    if name_elem:
                        name = self._clean_text(name_elem.get_text())
                        break

                if not name:
                    continue

                # Extract title/position
                title = None
                for selector in ['.title', '.position', '.rank', 'h4', '.degree']:
                    title_elem = card.select_one(selector)
                    if title_elem:
                        title = self._clean_text(title_elem.get_text())
                        break

                # Extract email
                email = self._extract_email(card)

                # Extract profile URL
                profile_url = None
                profile_link = card.select_one('a[href*="/faculty/"], a[href*="/people/"], a.more-info')
                if profile_link and profile_link.get('href'):
                    profile_url = profile_link['href']
                    # Make absolute URL if relative
                    if profile_url.startswith('/'):
                        profile_url = f"https://biochem.med.ufl.edu{profile_url}"

                # Extract department
                department = "Biochemistry and Molecular Biology"

                # Extract research interests
                research_interests = None
                research_elem = card.select_one('.research, .interests, .research-areas')
                if research_elem:
                    research_interests = self._clean_text(research_elem.get_text())

                # Extract phone
                phone = None
                phone_elem = card.select_one('.phone, [href^="tel:"]')
                if phone_elem:
                    phone = self._clean_text(phone_elem.get_text())

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
