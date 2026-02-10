"""
Scraper registry for dynamic loading
"""
import importlib
import sys
import os
from typing import Type, Optional
from .base_scraper import BaseScraper

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class ScraperRegistry:
    """
    Factory for dynamically loading scraper classes
    """

    @staticmethod
    def get_scraper(scraper_class: str, url: str, university_id: str) -> Optional[BaseScraper]:
        """
        Dynamically load and instantiate scraper class
        Falls back to HybridScraper if custom scraper not found

        Args:
            scraper_class: Name of scraper class (e.g., 'MiamiMicrobiologyScraper')
                          Can be empty/None to use HybridScraper
            url: Faculty page URL
            university_id: University identifier

        Returns:
            Instantiated scraper object or None if failed
        """
        # If no scraper_class specified, use HybridScraper
        if not scraper_class or scraper_class.strip() == '':
            print(f"No custom scraper specified - using HybridScraper for {university_id}")
            from .hybrid_scraper import HybridScraper
            return HybridScraper(url=url, university_id=university_id)

        try:
            # Try to load custom scraper
            # Convert class name to module name
            # MiamiMicrobiologyScraper -> miami_microbiology
            # UFBiochemScraper -> uf_biochem
            module_name = ScraperRegistry._class_to_module(scraper_class)

            # Import module from universities package
            module = importlib.import_module(f'universities.{module_name}')

            # Get class from module
            scraper_cls = getattr(module, scraper_class)

            # Instantiate and return
            print(f"Using custom scraper: {scraper_class}")
            return scraper_cls(url=url, university_id=university_id)

        except (ImportError, AttributeError) as e:
            print(f"Custom scraper {scraper_class} not found: {e}")
            print(f"Falling back to HybridScraper for {university_id}")

            # Fall back to HybridScraper
            from .hybrid_scraper import HybridScraper
            return HybridScraper(url=url, university_id=university_id)

    @staticmethod
    def _class_to_module(class_name: str) -> str:
        """
        Convert class name to module name

        Args:
            class_name: Class name (e.g., 'MiamiMicrobiologyScraper')

        Returns:
            Module name (e.g., 'miami')

        Examples:
            MiamiMicrobiologyScraper -> miami
            UFBiochemScraper -> uf_biochem
            StanfordBiologyScraper -> stanford_biology
        """
        # Remove 'Scraper' suffix
        name = class_name.replace('Scraper', '')

        # Convert CamelCase to snake_case
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                # Add underscore before uppercase letters (except first)
                if name[i-1].islower() or (i < len(name) - 1 and name[i+1].islower()):
                    result.append('_')
            result.append(char.lower())

        module_name = ''.join(result)

        # Clean up double underscores
        while '__' in module_name:
            module_name = module_name.replace('__', '_')

        return module_name.strip('_')
