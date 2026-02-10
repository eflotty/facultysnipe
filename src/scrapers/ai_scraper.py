"""
AI-Powered Scraper - Uses Claude API to extract faculty data
Fallback for when smart scraper fails or returns low-confidence results
"""
import json
import os
from typing import List
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper, Faculty
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import SCRAPER_TIMEOUT, USER_AGENT


class AIScraper(BaseScraper):
    """
    AI-powered scraper using Claude API
    Costs ~$0.01-0.05 per scrape but handles ANY page format
    """

    def __init__(self, url: str, university_id: str):
        super().__init__(url, university_id)
        self.api_key = os.getenv('ANTHROPIC_API_KEY')

        if not self.api_key:
            self.logger.warning("ANTHROPIC_API_KEY not set - AI scraper disabled")

    def scrape(self) -> List[Faculty]:
        """
        Scrape faculty using Claude API

        Returns:
            List of Faculty objects
        """
        if not self.api_key:
            self.logger.error("Cannot use AI scraper - no API key configured")
            return []

        self.logger.info(f"AI scraping {self.url} using Claude API")

        # Fetch HTML
        response = requests.get(
            self.url,
            headers={'User-Agent': USER_AGENT},
            timeout=SCRAPER_TIMEOUT
        )
        response.raise_for_status()

        html = response.content
        soup = BeautifulSoup(html, 'lxml')

        # Clean HTML (remove scripts, styles, etc.)
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        clean_html = str(soup)

        # Truncate if too long (Claude has token limits)
        if len(clean_html) > 100000:
            clean_html = clean_html[:100000] + "\n...(truncated)"

        # Call Claude API
        faculty_list = self._extract_with_claude(clean_html)

        # Validate results
        validated = self.validate(faculty_list)

        self.logger.info(f"AI scraper extracted {len(validated)} faculty")

        return validated

    def _extract_with_claude(self, html: str) -> List[Faculty]:
        """
        Use Claude API to extract faculty data from HTML

        Args:
            html: Cleaned HTML content

        Returns:
            List of Faculty objects
        """
        prompt = f"""Extract all faculty members from this university faculty page HTML.

For each faculty member, extract:
- name (required)
- title (position/rank like "Professor", "Associate Professor")
- email (if available)
- profile_url (link to their profile page, if available)
- department (if specified)
- phone (if available)
- research_interests (if available)

Return ONLY valid JSON array, no other text. Format:
[
  {{
    "name": "John Smith",
    "title": "Professor",
    "email": "jsmith@university.edu",
    "profile_url": "https://university.edu/faculty/john-smith",
    "department": "Biology",
    "phone": "555-1234",
    "research_interests": "Molecular biology"
  }}
]

If a field is not available, omit it or use null.

HTML:
{html}
"""

        try:
            # Call Claude API
            api_response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': self.api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                },
                json={
                    'model': 'claude-3-haiku-20240307',  # Cheapest model
                    'max_tokens': 4096,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                },
                timeout=60
            )

            api_response.raise_for_status()
            result = api_response.json()

            # Extract text from response
            text = result['content'][0]['text']

            # Parse JSON
            # Claude might wrap in markdown code blocks
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]

            faculty_data = json.loads(text.strip())

            # Convert to Faculty objects
            faculty_list = []
            for data in faculty_data:
                try:
                    faculty = Faculty(
                        name=data.get('name'),
                        title=data.get('title'),
                        email=data.get('email'),
                        profile_url=data.get('profile_url'),
                        department=data.get('department'),
                        phone=data.get('phone'),
                        research_interests=data.get('research_interests')
                    )
                    faculty_list.append(faculty)
                except Exception as e:
                    self.logger.warning(f"Failed to create Faculty from data: {e}")
                    continue

            # Log cost estimate
            input_tokens = result.get('usage', {}).get('input_tokens', 0)
            output_tokens = result.get('usage', {}).get('output_tokens', 0)
            cost = (input_tokens * 0.00025 / 1000) + (output_tokens * 0.00125 / 1000)
            self.logger.info(f"AI scraping cost: ${cost:.4f} ({input_tokens} in + {output_tokens} out tokens)")

            return faculty_list

        except Exception as e:
            self.logger.error(f"Claude API failed: {e}")
            return []
