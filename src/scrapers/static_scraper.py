"""
Static HTML scraper using BeautifulSoup
"""
from typing import List
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper, Faculty
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import SCRAPER_TIMEOUT, USER_AGENT


class StaticScraper(BaseScraper):
    """
    BeautifulSoup-based scraper for static HTML pages
    """

    def scrape(self) -> List[Faculty]:
        """
        Scrape faculty data using requests + BeautifulSoup

        Returns:
            List of Faculty objects
        """
        self.logger.info(f"Scraping {self.url} with static scraper")

        try:
            # Fetch HTML
            response = requests.get(
                self.url,
                headers={'User-Agent': USER_AGENT},
                timeout=SCRAPER_TIMEOUT
            )
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')

            # Call subclass-specific parsing
            faculty_list = self.parse(soup)

            # Validate results
            validated = self.validate(faculty_list)

            self.logger.info(f"Successfully scraped {len(validated)} faculty members")
            return validated

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {self.url}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to parse {self.url}: {e}")
            raise

    def parse(self, soup: BeautifulSoup) -> List[Faculty]:
        """
        Parse faculty data from BeautifulSoup object
        Must be implemented by subclass

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of Faculty objects
        """
        raise NotImplementedError("Subclass must implement parse() method")
