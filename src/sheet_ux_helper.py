"""
Google Sheets UX Helper - Auto-populate fields from URL
Makes it easy for non-technical users to add universities
"""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from typing import Dict, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from config import SCRAPER_TIMEOUT, USER_AGENT, setup_logging


class SheetUXHelper:
    """
    Helper class to auto-populate CONFIG sheet fields from URL
    """

    def __init__(self):
        """Initialize helper"""
        self.logger = setup_logging('SheetUXHelper')

    def auto_fill_from_url(self, url: str) -> Dict[str, str]:
        """
        Auto-generate all CONFIG fields from a URL

        Args:
            url: Faculty page URL

        Returns:
            Dictionary with auto-generated fields
        """
        self.logger.info(f"Auto-filling fields for {url}")

        result = {
            'url': url,
            'university_id': self._generate_university_id(url),
            'university_name': self._extract_university_name(url),
            'scraper_class': '',  # Always empty to use HybridScraper
            'scraper_type': self._detect_scraper_type(url),
            'enabled': 'TRUE',
            'sales_rep_email': '',  # User must fill this manually
            'last_run': '',
            'last_status': '',
            'notes': 'Auto-generated'
        }

        self.logger.info(f"Generated: {result['university_id']} - {result['university_name']}")
        return result

    def _generate_university_id(self, url: str) -> str:
        """
        Generate university_id from URL

        Examples:
            https://biology.stanford.edu/people/faculty -> stanford_biology
            https://med.miami.edu/departments/microbiology/faculty -> miami_microbiology
            https://www.harvard.edu/faculty -> harvard_faculty

        Args:
            url: Faculty page URL

        Returns:
            Generated university_id
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()

        # Extract university name from domain
        # Remove common prefixes
        domain = domain.replace('www.', '').replace('www2.', '')

        # Extract main domain name (e.g., stanford.edu -> stanford)
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            # Check if first part is a subdomain that indicates department
            if domain_parts[0] in ['biology', 'chemistry', 'physics', 'med', 'medicine',
                                   'engineering', 'arts', 'science', 'business']:
                # Use subdomain as department indicator
                university = domain_parts[-2]  # Main university name
                department = domain_parts[0]
                base_id = f"{university}_{department}"
            else:
                university = domain_parts[-2]
                base_id = university
        else:
            base_id = domain.replace('.', '_')

        # Try to extract department/college from path
        path_parts = [p for p in path.split('/') if p and p not in ['faculty', 'people', 'staff', 'directory']]

        # Look for department indicators in path
        dept_keywords = ['department', 'dept', 'college', 'school', 'center', 'institute']
        department = None

        for part in path_parts:
            # Check if this path segment contains a department keyword
            if any(kw in part for kw in dept_keywords):
                # Extract the actual department name
                for kw in dept_keywords:
                    part = part.replace(kw + 's-of-', '').replace(kw + '-of-', '').replace(kw, '')
                department = part.strip('-_')
                break
            # Or if it's just a department name
            elif len(part) > 2 and part.isalpha():
                department = part
                break

        # Combine university + department if found
        if department:
            base_id = f"{base_id}_{department}"

        # Clean up the ID
        base_id = re.sub(r'[^a-z0-9_]', '_', base_id)
        base_id = re.sub(r'_+', '_', base_id)  # Remove duplicate underscores
        base_id = base_id.strip('_')

        # Limit length
        if len(base_id) > 50:
            base_id = base_id[:50].rstrip('_')

        return base_id

    def _extract_university_name(self, url: str) -> str:
        """
        Extract university name from page

        Args:
            url: Faculty page URL

        Returns:
            University name (e.g., "Stanford - Biology")
        """
        try:
            response = requests.get(
                url,
                headers={'User-Agent': USER_AGENT},
                timeout=SCRAPER_TIMEOUT
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Try to extract from page title
            title = soup.find('title')
            if title:
                title_text = title.text.strip()

                # Clean up common patterns
                # "Faculty | Department of Biology | Stanford University" -> "Stanford - Biology"
                parts = [p.strip() for p in re.split(r'[|\-–—]', title_text)]

                # Find university name (usually contains "University" or "College" or is the domain)
                university = None
                department = None

                for part in parts:
                    part_lower = part.lower()
                    if 'university' in part_lower or 'college' in part_lower or 'institute' in part_lower:
                        university = part
                    elif any(kw in part_lower for kw in ['faculty', 'staff', 'people', 'directory']):
                        continue  # Skip these generic terms
                    elif any(kw in part_lower for kw in ['department', 'school', 'biology', 'chemistry',
                                                          'physics', 'engineering', 'medicine', 'microbiology']):
                        if not department:  # Take first department-like term
                            department = part

                # If we found both, combine them
                if university and department:
                    # Clean up department name
                    department = department.replace('Department of', '').replace('School of', '').strip()
                    return f"{university} - {department}"
                elif university:
                    return university

            # Fallback: extract from domain
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '').replace('www2.', '')

            # Capitalize first part of domain
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                university_name = domain_parts[-2].capitalize()
                return f"{university_name} University"

            return domain.capitalize()

        except Exception as e:
            self.logger.warning(f"Could not extract university name from {url}: {e}")

            # Fallback to domain-based name
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '').replace('www2.', '')
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                return domain_parts[-2].capitalize() + " University"

            return domain.capitalize()

    def _detect_scraper_type(self, url: str) -> str:
        """
        Auto-detect if page is static or dynamic

        Args:
            url: Faculty page URL

        Returns:
            'static' or 'dynamic'
        """
        try:
            response = requests.get(
                url,
                headers={'User-Agent': USER_AGENT},
                timeout=SCRAPER_TIMEOUT
            )
            response.raise_for_status()

            html = response.text

            # Check for heavy JavaScript frameworks
            js_indicators = [
                'react', 'angular', 'vue.js', 'ember.js',
                'data-react', 'ng-app', 'v-app',
                '__NEXT_DATA__', '_next/static',
                'window.INITIAL_STATE'
            ]

            js_count = sum(1 for indicator in js_indicators if indicator.lower() in html.lower())

            # Check for AJAX/API endpoints
            ajax_indicators = [
                'api/faculty', 'api/people', '/api/v',
                'fetch(', 'axios.', '$.ajax',
                'XMLHttpRequest'
            ]

            ajax_count = sum(1 for indicator in ajax_indicators if indicator in html)

            # If many indicators, likely dynamic
            if js_count >= 2 or ajax_count >= 2:
                self.logger.info(f"Detected dynamic page (JS: {js_count}, AJAX: {ajax_count})")
                return 'dynamic'

            self.logger.info(f"Detected static page (JS: {js_count}, AJAX: {ajax_count})")
            return 'static'

        except Exception as e:
            self.logger.warning(f"Could not detect scraper type for {url}: {e}. Defaulting to static.")
            return 'static'


def main():
    """Test the helper"""
    import argparse

    parser = argparse.ArgumentParser(description='Auto-fill CONFIG fields from URL')
    parser.add_argument('url', help='Faculty page URL')
    args = parser.parse_args()

    helper = SheetUXHelper()
    result = helper.auto_fill_from_url(args.url)

    print("\nAuto-generated fields:")
    print("=" * 60)
    for key, value in result.items():
        print(f"{key:20s}: {value}")
    print("=" * 60)


if __name__ == '__main__':
    main()
