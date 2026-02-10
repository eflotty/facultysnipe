"""
Miami University Microbiology Department Scraper
Static HTML implementation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scrapers.static_scraper import StaticScraper, Faculty
from typing import List
from bs4 import BeautifulSoup


class MiamiMicrobiologyScraper(StaticScraper):
    """
    Scraper for Miami Microbiology faculty page
    Example URL: https://med.miami.edu/departments/microbiology-and-immunology/faculty-and-staff
    """

    def parse(self, soup: BeautifulSoup) -> List[Faculty]:
        """
        Parse Miami Microbiology faculty page

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of Faculty objects
        """
        faculty_list = []

        # Find all faculty cards/entries
        # NOTE: Adjust selectors based on actual page structure
        # This is a generic example - you'll need to inspect the actual HTML

        # Option 1: Faculty cards with specific class
        faculty_cards = soup.select('.faculty-card, .people-card, .person-card')

        if not faculty_cards:
            # Option 2: List items or divs containing faculty info
            faculty_cards = soup.select('.faculty-member, .staff-member, .person')

        if not faculty_cards:
            # Option 3: Table rows
            faculty_cards = soup.select('table.faculty-list tbody tr')

        self.logger.info(f"Found {len(faculty_cards)} potential faculty entries")

        for card in faculty_cards:
            try:
                # Extract name
                name = None
                for selector in ['.name', '.person-name', 'h2', 'h3', '.title a', 'strong']:
                    name_elem = card.select_one(selector)
                    if name_elem:
                        name = self._clean_text(name_elem.get_text())
                        break

                if not name:
                    continue

                # Extract title/position
                title = None
                for selector in ['.title', '.position', '.rank', '.job-title']:
                    title_elem = card.select_one(selector)
                    if title_elem:
                        title = self._clean_text(title_elem.get_text())
                        break

                # Extract email
                email = self._extract_email(card)

                # Extract profile URL
                profile_url = None
                profile_link = card.select_one('a[href*="/faculty/"], a[href*="/people/"], a.profile-link')
                if profile_link and profile_link.get('href'):
                    profile_url = profile_link['href']
                    # Make absolute URL if relative
                    if profile_url.startswith('/'):
                        profile_url = f"https://med.miami.edu{profile_url}"

                # Extract department (usually same for all on this page)
                department = "Microbiology and Immunology"

                # Extract phone
                phone = None
                phone_elem = card.select_one('.phone, .tel, [href^="tel:"]')
                if phone_elem:
                    phone = self._clean_text(phone_elem.get_text())

                # Create Faculty object
                faculty = Faculty(
                    name=name,
                    title=title,
                    email=email,
                    profile_url=profile_url,
                    department=department,
                    phone=phone
                )

                faculty_list.append(faculty)

            except Exception as e:
                self.logger.warning(f"Failed to parse faculty card: {e}")
                continue

        return faculty_list
