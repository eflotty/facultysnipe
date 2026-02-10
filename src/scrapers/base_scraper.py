"""
Base scraper classes and Faculty dataclass
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import hashlib
import json
from datetime import datetime


@dataclass
class Faculty:
    """
    Normalized faculty data structure
    """
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    profile_url: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    research_interests: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    faculty_id: str = field(init=False)

    def __post_init__(self):
        """Generate unique ID based on key fields"""
        self.faculty_id = self._generate_id()

    def _generate_id(self) -> str:
        """
        Generate deterministic hash ID from key fields

        Returns:
            8-character hex hash
        """
        # Use name + email + title for ID generation
        # This ensures same person gets same ID even if other fields change
        id_string = f"{self.name.lower().strip()}|{(self.email or '').lower().strip()}|{(self.title or '').lower().strip()}"
        return hashlib.sha256(id_string.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert raw_data dict to JSON string for Google Sheets
        if isinstance(data.get('raw_data'), dict):
            data['raw_data'] = json.dumps(data['raw_data'])
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Faculty':
        """Create Faculty from dictionary"""
        # Parse raw_data JSON string back to dict
        if isinstance(data.get('raw_data'), str):
            try:
                data['raw_data'] = json.loads(data['raw_data'])
            except json.JSONDecodeError:
                data['raw_data'] = {}

        # Remove extra fields that aren't in Faculty dataclass
        faculty_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in faculty_fields and k != 'faculty_id'}

        return cls(**filtered_data)


class BaseScraper(ABC):
    """
    Abstract base class for all university scrapers
    """

    def __init__(self, url: str, university_id: str):
        """
        Initialize scraper

        Args:
            url: Faculty page URL
            university_id: Unique university identifier
        """
        self.url = url
        self.university_id = university_id
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Setup logger for this scraper"""
        import logging
        logger = logging.getLogger(f'FacultySnipe.{self.university_id}')
        return logger

    @abstractmethod
    def scrape(self) -> List[Faculty]:
        """
        Scrape faculty data from university page

        Returns:
            List of Faculty objects

        Raises:
            Exception: If scraping fails
        """
        pass

    def validate(self, faculty_list: List[Faculty]) -> List[Faculty]:
        """
        Validate scraped faculty data

        Args:
            faculty_list: List of scraped faculty

        Returns:
            Validated faculty list (invalid entries removed)
        """
        validated = []

        for faculty in faculty_list:
            if not faculty.name or len(faculty.name.strip()) < 2:
                self.logger.warning(f"Skipping faculty with invalid name: {faculty.name}")
                continue

            # At least one contact method should exist
            if not any([faculty.email, faculty.profile_url, faculty.phone]):
                self.logger.warning(f"Skipping faculty with no contact info: {faculty.name}")
                continue

            # Log completeness for monitoring
            completeness = []
            if faculty.email:
                completeness.append('email')
            if faculty.phone:
                completeness.append('phone')
            if faculty.title:
                completeness.append('title')
            if faculty.profile_url:
                completeness.append('profile')
            if faculty.department:
                completeness.append('dept')

            self.logger.debug(f"✓ {faculty.name}: {', '.join(completeness)}")

            validated.append(faculty)

        self.logger.info(f"Validated {len(validated)}/{len(faculty_list)} faculty members")
        return validated

    def _extract_email(self, element) -> Optional[str]:
        """
        Extract email from HTML element (handles mailto: links and obfuscation)

        Args:
            element: BeautifulSoup element

        Returns:
            Email address or None
        """
        # Try mailto: links
        mailto_links = element.find_all('a', href=lambda x: x and 'mailto:' in x.lower())
        if mailto_links:
            email = mailto_links[0]['href'].lower().replace('mailto:', '').split('?')[0].split('#')[0].strip()
            # Clean up any URL encoding
            import urllib.parse
            email = urllib.parse.unquote(email)
            if self._is_valid_email(email):
                return email

        # Try data attributes (some sites hide emails here)
        email_attrs = element.find(attrs={"data-email": True})
        if email_attrs and email_attrs.get('data-email'):
            email = email_attrs['data-email'].strip()
            if self._is_valid_email(email):
                return email

        # Try text matching email pattern
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = element.get_text()
        matches = re.findall(email_pattern, text)

        # Return first valid email
        for match in matches:
            if self._is_valid_email(match):
                return match.lower()

        # Handle obfuscated emails (e.g., "name [at] domain [dot] edu")
        obfuscated_pattern = r'([a-zA-Z0-9._%+-]+)\s*\[at\]\s*([a-zA-Z0-9.-]+)\s*\[dot\]\s*([a-zA-Z]{2,})'
        match = re.search(obfuscated_pattern, text, re.I)
        if match:
            email = f"{match.group(1)}@{match.group(2)}.{match.group(3)}".lower()
            if self._is_valid_email(email):
                return email

        return None

    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format

        Args:
            email: Email address to validate

        Returns:
            True if valid
        """
        if not email or len(email) < 5:
            return False

        # Check for common invalid patterns
        invalid_patterns = [
            'example.com', 'test.com', 'mailto:', 'javascript:',
            '[at]', '[dot]', 'noreply', 'webmaster'
        ]

        email_lower = email.lower()
        for pattern in invalid_patterns:
            if pattern in email_lower:
                return False

        # Basic format check
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """
        Clean and normalize text

        Args:
            text: Raw text

        Returns:
            Cleaned text or None
        """
        if not text:
            return None

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove common academic prefixes
        prefixes = [
            'Dr.', 'Dr', 'Professor', 'Prof.', 'Prof',
            'Mr.', 'Mr', 'Ms.', 'Ms', 'Mrs.', 'Mrs',
            'Mx.', 'Mx', 'Rev.', 'Rev'
        ]
        for prefix in prefixes:
            if text.startswith(prefix + ' '):
                text = text[len(prefix):].strip()

        # Remove common suffixes
        suffixes = [
            ', Ph.D.', ', PhD', ', Ph.D', ', M.D.', ', MD',
            ', D.Phil.', ', DPhil', ', Sc.D.', ', ScD',
            ', Jr.', ', Jr', ', Sr.', ', Sr', ', II', ', III', ', IV'
        ]
        for suffix in suffixes:
            if text.endswith(suffix):
                text = text[:-len(suffix)].strip()

        # Remove degree abbreviations in parentheses
        import re
        text = re.sub(r'\s*\([^)]*(?:PhD|Ph\.D|MD|M\.D|ScD|DPhil)[^)]*\)', '', text, flags=re.I)

        # Remove multiple spaces
        text = ' '.join(text.split())

        return text.strip() if text.strip() else None
