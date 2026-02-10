"""
Hybrid Scraper - Multi-strategy scraping with intelligent fallbacks
This is the default scraper for all universities
"""
from typing import List
from .base_scraper import BaseScraper, Faculty
from .smart_universal_scraper import SmartUniversalScraper
from .smart_dynamic_scraper import SmartDynamicScraper
from .ai_scraper import AIScraper
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class HybridScraper(BaseScraper):
    """
    Intelligent scraper that tries multiple strategies:
    1. SmartUniversalScraper (static, fast, free)
    2. SmartDynamicScraper (Playwright + scrolling, slower, free)
    3. AI scraper (Claude API, costs ~$0.01-0.05)
    Returns best results
    """

    def __init__(self, url: str, university_id: str, min_results: int = 3, min_confidence: int = 60):
        """
        Initialize hybrid scraper

        Args:
            url: Faculty page URL
            university_id: University identifier
            min_results: Minimum acceptable results before trying AI
            min_confidence: Minimum confidence score before trying AI
        """
        super().__init__(url, university_id)
        self.min_results = min_results
        self.min_confidence = min_confidence

    def scrape(self) -> List[Faculty]:
        """
        Scrape using multiple strategies with intelligent fallbacks

        Returns:
            List of Faculty objects
        """
        self.logger.info(f"=== Hybrid Scraping: {self.url} ===")

        # Step 1: Try Smart Universal Scraper (static, fast)
        self.logger.info("Step 1: Trying Smart Universal Scraper (static)...")
        smart_scraper = SmartUniversalScraper(self.url, self.university_id)

        try:
            smart_results = smart_scraper.scrape()

            # Check if results are good enough
            if len(smart_results) >= self.min_results:
                self.logger.info(f"✓ Smart scraper succeeded with {len(smart_results)} results")
                self._log_method_used('smart_static')
                return smart_results

            self.logger.warning(f"Smart scraper found only {len(smart_results)} results (need {self.min_results})")

        except Exception as e:
            self.logger.warning(f"Smart scraper failed: {e}")
            smart_results = []

        # Step 2: Try Smart Dynamic Scraper (Playwright + scrolling)
        self.logger.info("Step 2: Smart static insufficient - trying Smart Dynamic Scraper (Playwright)...")

        try:
            dynamic_scraper = SmartDynamicScraper(self.url, self.university_id)
            dynamic_results = dynamic_scraper.scrape()

            # Check if results are better
            if len(dynamic_results) >= self.min_results:
                self.logger.info(f"✓ Dynamic scraper succeeded with {len(dynamic_results)} results")
                self._log_method_used('smart_dynamic')
                return dynamic_results

            self.logger.warning(f"Dynamic scraper found only {len(dynamic_results)} results")

            # Use dynamic results if better than static
            if len(dynamic_results) > len(smart_results):
                smart_results = dynamic_results

        except Exception as e:
            self.logger.warning(f"Dynamic scraper failed: {e}")

        # Step 3: Fall back to AI if both smart methods failed
        self.logger.info("Step 3: Smart scrapers insufficient - trying AI scraper...")

        # Check if AI is available
        if not os.getenv('ANTHROPIC_API_KEY'):
            self.logger.warning("AI scraper not available (no API key) - returning best smart scraper results")
            self._log_method_used('smart_only')
            return smart_results

        try:
            ai_scraper = AIScraper(self.url, self.university_id)
            ai_results = ai_scraper.scrape()

            if len(ai_results) > len(smart_results):
                self.logger.info(f"✓ AI scraper succeeded with {len(ai_results)} results")
                self._log_method_used('ai')
                return ai_results
            else:
                self.logger.info(f"AI scraper found {len(ai_results)} results - using smart results instead")
                self._log_method_used('smart_best')
                return smart_results

        except Exception as e:
            self.logger.error(f"AI scraper failed: {e}")
            self.logger.info("Falling back to best smart scraper results")
            self._log_method_used('smart_fallback')
            return smart_results

    def _log_method_used(self, method: str):
        """
        Log which scraping method was used
        Can be used for analytics/optimization later

        Args:
            method: 'smart_static', 'smart_dynamic', 'ai', 'smart_only', 'smart_best', 'smart_fallback'
        """
        method_descriptions = {
            'smart_static': 'Smart Universal Scraper (static HTML)',
            'smart_dynamic': 'Smart Dynamic Scraper (Playwright + scrolling)',
            'ai': 'AI Scraper (Claude API)',
            'smart_only': 'Smart scraper only (no AI key)',
            'smart_best': 'Best smart scraper result',
            'smart_fallback': 'Smart scraper fallback (AI failed)'
        }

        description = method_descriptions.get(method, method)
        self.logger.info(f"[SCRAPING METHOD: {description}]")
        # You could write this to a database or Google Sheets for tracking
