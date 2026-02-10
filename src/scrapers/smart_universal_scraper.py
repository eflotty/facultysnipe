"""
Smart Universal Scraper - Adapts to any university faculty page
Uses multiple strategies to extract faculty data without custom coding
THOROUGH MODE: Prioritizes completeness over speed
"""
import re
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from .base_scraper import BaseScraper, Faculty
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import SCRAPER_TIMEOUT, USER_AGENT


def get_retry_session(retries=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504)):
    """
    Create requests session with retry logic

    Args:
        retries: Number of retries
        backoff_factor: Backoff factor for retries
        status_forcelist: HTTP status codes to retry on

    Returns:
        Configured requests session
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class SmartUniversalScraper(BaseScraper):
    """
    Universal scraper that tries multiple strategies to extract faculty data
    Works on 80%+ of university pages without custom configuration
    """

    def scrape(self) -> List[Faculty]:
        """
        Scrape faculty using multiple adaptive strategies
        Handles pagination automatically

        Returns:
            List of Faculty objects
        """
        self.logger.info(f"Smart scraping {self.url}")

        all_faculty = []
        pages_scraped = 0
        max_pages = 10  # Safety limit

        # Start with the main page
        current_url = self.url
        visited_urls = set()

        while current_url and pages_scraped < max_pages:
            if current_url in visited_urls:
                break

            visited_urls.add(current_url)
            pages_scraped += 1

            self.logger.info(f"Scraping page {pages_scraped}: {current_url}")

            # Respectful delay between pages (not first page)
            if pages_scraped > 1:
                time.sleep(2)  # 2 second delay between pages

            # Fetch HTML with retry logic
            try:
                session = get_retry_session()
                response = session.get(
                    current_url,
                    headers={'User-Agent': USER_AGENT},
                    timeout=SCRAPER_TIMEOUT
                )
                response.raise_for_status()
            except Exception as e:
                self.logger.warning(f"Failed to fetch {current_url} after retries: {e}")
                break

            html = response.content
            soup = BeautifulSoup(html, 'lxml')

            # Scrape current page
            page_faculty = self._scrape_single_page(soup)
            all_faculty.extend(page_faculty)

            # Check for pagination
            next_url = self._find_next_page(soup, current_url)
            current_url = next_url

        if pages_scraped > 1:
            self.logger.info(f"Scraped {pages_scraped} pages total")

        # Deduplicate faculty across pages
        all_faculty = self._deduplicate_faculty(all_faculty)

        return all_faculty

    def _scrape_single_page(self, soup: BeautifulSoup) -> List[Faculty]:
        """
        Scrape faculty from a single page using multiple strategies
        THOROUGH MODE: Try ALL strategies and merge results

        Returns:
            List of Faculty objects
        """
        # Try ALL strategies (not just first success)
        strategies = [
            self._strategy_faculty_containers,
            self._strategy_email_clustering,
            self._strategy_academic_titles,
            self._strategy_table_detection,
            self._strategy_text_mining
        ]

        all_results = {}  # Use dict to merge by faculty_id
        strategy_scores = {}

        self.logger.info("Running all strategies in THOROUGH mode...")

        for strategy in strategies:
            try:
                results, confidence = strategy(soup)
                self.logger.debug(f"{strategy.__name__}: Found {len(results)} faculty (confidence: {confidence}%)")

                # Add results to collection, merging data
                for faculty in results:
                    if faculty.faculty_id in all_results:
                        # Merge with existing - keep most complete data
                        existing = all_results[faculty.faculty_id]
                        merged = self._merge_faculty_data(existing, faculty)
                        all_results[faculty.faculty_id] = merged
                        strategy_scores[faculty.faculty_id] = max(strategy_scores.get(faculty.faculty_id, 0), confidence)
                    else:
                        all_results[faculty.faculty_id] = faculty
                        strategy_scores[faculty.faculty_id] = confidence

            except Exception as e:
                self.logger.debug(f"{strategy.__name__} failed: {e}")
                continue

        # Convert back to list
        merged_results = list(all_results.values())

        if merged_results:
            # Enrich with additional data extraction
            enriched_results = self._enrich_faculty_data(merged_results, soup)

            # Validate
            validated = self.validate(enriched_results)
            avg_confidence = sum(strategy_scores.values()) / len(strategy_scores) if strategy_scores else 0
            self.logger.info(f"✓ Extracted {len(validated)} faculty (merged from all strategies, avg confidence: {avg_confidence:.0f}%)")
            return validated

        self.logger.warning("⚠ All scraping strategies failed - no faculty found")
        return []

    def _merge_faculty_data(self, existing: Faculty, new: Faculty) -> Faculty:
        """
        Merge two Faculty objects, keeping most complete data

        Args:
            existing: Existing faculty data
            new: New faculty data

        Returns:
            Merged Faculty object
        """
        # Keep whichever field is more complete
        return Faculty(
            name=existing.name,  # Name should be the same (same ID)
            title=new.title if new.title and len(new.title) > len(existing.title or '') else existing.title,
            email=new.email or existing.email,  # Prefer any email
            profile_url=new.profile_url or existing.profile_url,
            department=new.department if new.department and len(new.department) > len(existing.department or '') else existing.department,
            phone=new.phone or existing.phone,
            research_interests=new.research_interests if new.research_interests and len(new.research_interests) > len(existing.research_interests or '') else existing.research_interests,
            raw_data={**existing.raw_data, **new.raw_data}
        )

    def _enrich_faculty_data(self, faculty_list: List[Faculty], soup: BeautifulSoup) -> List[Faculty]:
        """
        Enrich faculty data with additional thorough extraction
        Includes following profile links to extract more complete data

        Args:
            faculty_list: Initial faculty list
            soup: Page BeautifulSoup object

        Returns:
            Enriched faculty list
        """
        self.logger.info("Enriching faculty data with additional extraction...")

        enriched = []
        for idx, faculty in enumerate(faculty_list):
            # Try to find more complete information for this faculty

            # CRITICAL: If missing email but have profile URL, follow the link!
            if not faculty.email and faculty.profile_url:
                self.logger.info(f"Following profile link for {faculty.name} to find email...")
                profile_data = self._scrape_profile_page(faculty.profile_url)

                if profile_data.get('email'):
                    faculty.email = profile_data['email']
                    self.logger.info(f"✓ Found email from profile: {faculty.email}")

                # Also get other data if missing
                if not faculty.phone and profile_data.get('phone'):
                    faculty.phone = profile_data['phone']

                if not faculty.research_interests and profile_data.get('research_interests'):
                    faculty.research_interests = profile_data['research_interests']

                if not faculty.department and profile_data.get('department'):
                    faculty.department = profile_data['department']

                # Small delay to be respectful
                if idx < len(faculty_list) - 1:
                    time.sleep(0.5)

            # If still missing email, search harder on main page
            if not faculty.email:
                faculty.email = self._find_email_by_name(soup, faculty.name)

            # If missing phone, search harder
            if not faculty.phone:
                faculty.phone = self._find_phone_by_name(soup, faculty.name)

            # If missing department, try to extract
            if not faculty.department:
                faculty.department = self._extract_department(soup)

            enriched.append(faculty)

        return enriched

    def _scrape_profile_page(self, profile_url: str) -> dict:
        """
        Scrape individual faculty profile page for additional data

        Args:
            profile_url: URL to faculty profile page

        Returns:
            Dictionary with extracted data (email, phone, etc.)
        """
        result = {
            'email': None,
            'phone': None,
            'research_interests': None,
            'department': None
        }

        try:
            session = get_retry_session()
            response = session.get(
                profile_url,
                headers={'User-Agent': USER_AGENT},
                timeout=30  # Shorter timeout for individual profiles
            )
            response.raise_for_status()

            profile_soup = BeautifulSoup(response.content, 'lxml')

            # Extract email (usually more visible on profile pages)
            result['email'] = self._extract_email(profile_soup)

            # Extract phone
            result['phone'] = self._extract_phone(profile_soup)

            # Extract research interests (usually longer on profile pages)
            research_keywords = ['research', 'interests', 'focus', 'areas', 'specialization', 'expertise']
            for keyword in research_keywords:
                # Look for sections with these keywords
                headers = profile_soup.find_all(['h2', 'h3', 'h4'], string=re.compile(keyword, re.I))
                for header in headers:
                    # Get the next sibling content
                    content_elem = header.find_next_sibling(['p', 'div', 'ul'])
                    if content_elem:
                        text = content_elem.get_text().strip()
                        if len(text) > 20:  # Meaningful content
                            result['research_interests'] = text[:500]
                            break

                if result['research_interests']:
                    break

            # Extract department if visible
            result['department'] = self._extract_department(profile_soup)

            self.logger.debug(f"Profile scrape complete: email={bool(result['email'])}, phone={bool(result['phone'])}")

        except Exception as e:
            self.logger.debug(f"Could not scrape profile page {profile_url}: {e}")

        return result

    def _strategy_faculty_containers(self, soup: BeautifulSoup) -> Tuple[List[Faculty], int]:
        """
        Strategy 1: Find containers with faculty-related class/id names

        Returns:
            (faculty_list, confidence_score)
        """
        faculty_list = []

        # Expanded keywords for better matching
        faculty_keywords = [
            'faculty', 'professor', 'people', 'person', 'staff',
            'member', 'team', 'bio', 'profile', 'card', 'researcher',
            'investigator', 'scientist', 'personnel', 'directory',
            'employee', 'academic', 'scholar', 'expert'
        ]

        containers = []
        for keyword in faculty_keywords:
            containers.extend(soup.find_all(class_=re.compile(keyword, re.I)))
            containers.extend(soup.find_all(id=re.compile(keyword, re.I)))
            containers.extend(soup.find_all(attrs={"data-type": re.compile(keyword, re.I)}))
            # Also check for data-* attributes
            containers.extend(soup.find_all(attrs={"data-role": re.compile(keyword, re.I)}))
            containers.extend(soup.find_all(attrs={"data-category": re.compile(keyword, re.I)}))

        # Deduplicate
        seen = set()
        unique_containers = []
        for container in containers:
            # Use element's position in tree as unique identifier
            container_id = id(container)
            if container_id not in seen:
                seen.add(container_id)
                unique_containers.append(container)

        if not unique_containers:
            return [], 0

        # Extract faculty from each container
        for container in unique_containers:
            faculty = self._extract_faculty_from_container(container)
            if faculty and faculty not in faculty_list:
                faculty_list.append(faculty)

        # Confidence based on keyword match and results
        confidence = min(90, 50 + len(faculty_list) * 5)

        return faculty_list, confidence

    def _strategy_email_clustering(self, soup: BeautifulSoup) -> Tuple[List[Faculty], int]:
        """
        Strategy 2: Find all emails, group by parent container

        Returns:
            (faculty_list, confidence_score)
        """
        faculty_list = []

        # Find all email links
        email_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))

        if len(email_links) < 3:
            return [], 0

        # Group by parent container
        for email_link in email_links:
            email = email_link['href'].replace('mailto:', '').split('?')[0].strip()

            # Find parent container (likely faculty card/div)
            parent = email_link.find_parent(['div', 'li', 'tr', 'article', 'section'])

            if parent:
                faculty = self._extract_faculty_from_container(parent, known_email=email)
                if faculty:
                    faculty_list.append(faculty)

        # Higher confidence if we found many emails
        confidence = min(85, 40 + len(faculty_list) * 5)

        return faculty_list, confidence

    def _strategy_academic_titles(self, soup: BeautifulSoup) -> Tuple[List[Faculty], int]:
        """
        Strategy 3: Find academic titles (Professor, Dr.) and extract nearby data

        Returns:
            (faculty_list, confidence_score)
        """
        faculty_list = []

        # Find elements containing academic titles
        title_pattern = re.compile(
            r'\b(Professor|Associate Professor|Assistant Professor|Dr\.|Ph\.?D\.?|Faculty)\b',
            re.I
        )

        elements_with_titles = soup.find_all(string=title_pattern)

        if len(elements_with_titles) < 3:
            return [], 0

        for element in elements_with_titles:
            parent = element.find_parent(['div', 'li', 'tr', 'article', 'section', 'p'])

            if parent:
                faculty = self._extract_faculty_from_container(parent)
                if faculty and faculty not in faculty_list:
                    faculty_list.append(faculty)

        confidence = min(75, 30 + len(faculty_list) * 5)

        return faculty_list, confidence

    def _strategy_table_detection(self, soup: BeautifulSoup) -> Tuple[List[Faculty], int]:
        """
        Strategy 4: Detect tables with faculty data (THOROUGH version)

        Returns:
            (faculty_list, confidence_score)
        """
        faculty_list = []

        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            if len(rows) < 2:
                continue

            # Try to identify column headers
            header_row = rows[0]
            headers = [th.get_text().strip().lower() for th in header_row.find_all(['th', 'td'])]

            # Find column indices
            name_col = None
            email_col = None
            title_col = None
            phone_col = None
            dept_col = None

            for i, header in enumerate(headers):
                if 'name' in header or 'faculty' in header:
                    name_col = i
                elif 'email' in header or 'e-mail' in header or 'contact' in header:
                    email_col = i
                elif 'title' in header or 'position' in header or 'rank' in header:
                    title_col = i
                elif 'phone' in header or 'tel' in header:
                    phone_col = i
                elif 'department' in header or 'dept' in header:
                    dept_col = i

            # Process data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])

                if len(cells) < 2:
                    continue

                # Extract data based on columns
                name = None
                email = None
                title = None
                phone = None
                department = None

                if name_col is not None and name_col < len(cells):
                    name = self._clean_text(cells[name_col].get_text())

                if email_col is not None and email_col < len(cells):
                    email = self._extract_email(cells[email_col])

                if title_col is not None and title_col < len(cells):
                    title = self._clean_text(cells[title_col].get_text())

                if phone_col is not None and phone_col < len(cells):
                    phone = self._extract_phone(cells[phone_col])

                if dept_col is not None and dept_col < len(cells):
                    department = self._clean_text(cells[dept_col].get_text())

                # If columns not identified, try generic extraction
                if not name:
                    faculty = self._extract_faculty_from_container(row)
                    if faculty:
                        faculty_list.append(faculty)
                        continue

                # Build Faculty object
                if name:
                    # Try to find email/phone if not in specific columns
                    if not email:
                        email = self._extract_email(row)
                    if not phone:
                        phone = self._extract_phone(row)

                    # Need at least name + (email or something)
                    if email or phone or len(cells) >= 3:
                        # Extract profile URL
                        profile_url = None
                        for cell in cells:
                            link = cell.find('a', href=True)
                            if link and 'mailto:' not in link.get('href', ''):
                                href = link['href']
                                if href.startswith('http'):
                                    profile_url = href
                                elif href.startswith('/'):
                                    from urllib.parse import urljoin
                                    profile_url = urljoin(self.url, href)
                                break

                        faculty_list.append(Faculty(
                            name=name,
                            title=title,
                            email=email,
                            phone=phone,
                            department=department,
                            profile_url=profile_url
                        ))

        if len(faculty_list) >= 3:
            confidence = 75
        elif len(faculty_list) >= 1:
            confidence = 50
        else:
            confidence = 20

        return faculty_list, confidence

    def _strategy_text_mining(self, soup: BeautifulSoup) -> Tuple[List[Faculty], int]:
        """
        Strategy 5: Generic text mining for name + email patterns

        Returns:
            (faculty_list, confidence_score)
        """
        faculty_list = []

        # Find all email addresses in text
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = soup.get_text()
        emails = re.findall(email_pattern, text)

        # For each email, try to find name nearby
        for email in emails:
            # Find the element containing this email
            element = soup.find(string=re.compile(re.escape(email)))
            if element:
                parent = element.find_parent(['div', 'p', 'li', 'td'])
                if parent:
                    name = self._extract_name_from_text(parent.get_text())
                    if name:
                        faculty_list.append(Faculty(
                            name=name,
                            email=email
                        ))

        confidence = min(50, 20 + len(faculty_list) * 3)

        return faculty_list, confidence

    def _find_email_by_name(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        """
        Search for email address near a specific name

        Args:
            soup: BeautifulSoup object
            name: Faculty name to search near

        Returns:
            Email address or None
        """
        try:
            # Find all text containing the name
            name_parts = name.split()
            if len(name_parts) < 2:
                return None

            last_name = name_parts[-1]

            # Search for text containing last name
            for element in soup.find_all(string=re.compile(re.escape(last_name), re.I)):
                parent = element.find_parent(['div', 'li', 'tr', 'td', 'p', 'article'])
                if parent:
                    email = self._extract_email(parent)
                    if email:
                        return email

        except Exception as e:
            self.logger.debug(f"Error finding email for {name}: {e}")

        return None

    def _find_phone_by_name(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        """
        Search for phone number near a specific name

        Args:
            soup: BeautifulSoup object
            name: Faculty name to search near

        Returns:
            Phone number or None
        """
        try:
            # Find all text containing the name
            name_parts = name.split()
            if len(name_parts) < 2:
                return None

            last_name = name_parts[-1]

            # Search for text containing last name
            for element in soup.find_all(string=re.compile(re.escape(last_name), re.I)):
                parent = element.find_parent(['div', 'li', 'tr', 'td', 'p', 'article'])
                if parent:
                    phone = self._extract_phone(parent)
                    if phone:
                        return phone

        except Exception as e:
            self.logger.debug(f"Error finding phone for {name}: {e}")

        return None

    def _extract_phone(self, element) -> Optional[str]:
        """
        Extract phone number from element

        Args:
            element: BeautifulSoup element

        Returns:
            Phone number or None
        """
        try:
            text = element.get_text()

            # Phone number patterns (US and international)
            phone_patterns = [
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890, 123-456-7890, etc.
                r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',  # International
                r'\d{3}[-.\s]\d{4}',  # 123-4567
            ]

            for pattern in phone_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    # Clean up the phone number
                    phone = matches[0]
                    # Remove common false positives
                    if 'fax' in text[max(0, text.find(phone) - 20):text.find(phone) + 20].lower():
                        continue
                    return phone.strip()

            # Check for tel: links
            tel_links = element.find_all('a', href=re.compile(r'^tel:', re.I))
            if tel_links:
                phone = tel_links[0]['href'].replace('tel:', '').strip()
                return phone

        except Exception as e:
            self.logger.debug(f"Error extracting phone: {e}")

        return None

    def _extract_department(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Try to extract department name from page

        Args:
            soup: BeautifulSoup object

        Returns:
            Department name or None
        """
        try:
            # Look in title
            title = soup.find('title')
            if title:
                title_text = title.text
                # Common patterns: "Department of Biology", "Biology Department"
                dept_match = re.search(r'Department of ([A-Z][a-zA-Z\s&]+)', title_text)
                if dept_match:
                    return dept_match.group(1).strip()

                dept_match = re.search(r'([A-Z][a-zA-Z\s&]+) Department', title_text)
                if dept_match:
                    return dept_match.group(1).strip()

            # Look in h1, h2 tags
            for header in soup.find_all(['h1', 'h2']):
                text = header.get_text()
                if 'department' in text.lower():
                    # Extract department name
                    dept_match = re.search(r'Department of ([A-Z][a-zA-Z\s&]+)', text)
                    if dept_match:
                        return dept_match.group(1).strip()

                    dept_match = re.search(r'([A-Z][a-zA-Z\s&]+) Department', text)
                    if dept_match:
                        return dept_match.group(1).strip()

        except Exception as e:
            self.logger.debug(f"Error extracting department: {e}")

        return None

    def _extract_faculty_from_container(
        self,
        container,
        known_email: Optional[str] = None
    ) -> Optional[Faculty]:
        """
        Extract faculty data from a container element

        Args:
            container: BeautifulSoup element
            known_email: Pre-extracted email (optional)

        Returns:
            Faculty object or None
        """
        # Extract name
        name = self._extract_name(container)
        if not name:
            return None

        # Extract email (try multiple methods)
        email = known_email or self._extract_email(container)

        # Extract profile URL
        profile_url = None
        profile_link = container.find('a', href=True)
        if profile_link and 'mailto:' not in profile_link['href']:
            href = profile_link['href']
            if href.startswith('http'):
                profile_url = href
            elif href.startswith('/'):
                # Make absolute URL
                from urllib.parse import urljoin
                profile_url = urljoin(self.url, href)

        # Extract title
        title = self._extract_title(container)

        # Extract phone
        phone = self._extract_phone(container)

        # Extract department (from container or class names)
        department = None
        # Check for department in class names
        if container.get('class'):
            class_str = ' '.join(container.get('class'))
            dept_match = re.search(r'(biology|chemistry|physics|engineering|mathematics|computer|medicine|microbiology)', class_str, re.I)
            if dept_match:
                department = dept_match.group(1).capitalize()

        # Try to find department in nearby text
        if not department:
            dept_keywords = ['department', 'dept', 'division', 'school of', 'college of']
            text = container.get_text()
            for keyword in dept_keywords:
                if keyword in text.lower():
                    # Extract surrounding text
                    idx = text.lower().find(keyword)
                    context = text[max(0, idx-30):idx+50]
                    # Look for capitalized words
                    dept_match = re.search(r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+' + re.escape(keyword), context, re.I)
                    if dept_match:
                        department = dept_match.group(1)
                        break

        # Try to extract research interests
        research_interests = None
        research_keywords = ['research', 'interests', 'focus', 'specialization']
        for keyword in research_keywords:
            elem = container.find(string=re.compile(keyword, re.I))
            if elem:
                parent = elem.find_parent(['p', 'div', 'span'])
                if parent:
                    research_text = parent.get_text().strip()
                    # Clean up
                    research_text = re.sub(r'(research interests?:?|research focus:?)', '', research_text, flags=re.I).strip()
                    if research_text and len(research_text) > 10:
                        research_interests = research_text[:500]  # Limit length
                        break

        # Need at least name + (email OR profile_url)
        if not (email or profile_url):
            return None

        return Faculty(
            name=name,
            title=title,
            email=email,
            profile_url=profile_url,
            department=department,
            phone=phone,
            research_interests=research_interests
        )

    def _extract_name(self, element) -> Optional[str]:
        """Extract name from element"""
        # Try common name selectors
        for selector in ['.name', '.person-name', 'h2', 'h3', 'h4', '.title a', 'strong', 'b']:
            name_elem = element.select_one(selector)
            if name_elem:
                name = self._clean_text(name_elem.get_text())
                if name and len(name.split()) >= 2:  # At least first + last name
                    return name

        # Fallback: Look for text with capital letters (names)
        text = element.get_text()
        name = self._extract_name_from_text(text)
        return name

    def _extract_name_from_text(self, text: str) -> Optional[str]:
        """Extract name from plain text using patterns"""
        # Look for capitalized words (likely names)
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        matches = re.findall(name_pattern, text)

        if matches:
            # Return first match that looks like a name
            for match in matches:
                if len(match.split()) >= 2 and len(match) < 50:
                    return match

        return None

    def _extract_title(self, element) -> Optional[str]:
        """Extract academic title from element"""
        for selector in ['.title', '.position', '.rank', '.job-title', 'h4', 'em', 'i']:
            title_elem = element.select_one(selector)
            if title_elem:
                title = self._clean_text(title_elem.get_text())
                # Check if it looks like an academic title
                if title and any(keyword in title.lower() for keyword in ['professor', 'dr', 'faculty', 'lecturer', 'instructor']):
                    return title

        # Look in text for title keywords
        text = element.get_text()
        title_pattern = re.compile(
            r'(Professor|Associate Professor|Assistant Professor|Lecturer|Instructor|Research Scientist)',
            re.I
        )
        match = title_pattern.search(text)
        if match:
            return match.group(1)

        return None

    def _find_next_page(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Find next page URL for pagination

        Args:
            soup: Current page BeautifulSoup object
            current_url: Current page URL

        Returns:
            Next page URL or None
        """
        # Look for common pagination patterns
        pagination_patterns = [
            ('a', {'class': re.compile(r'next|pagination.*next', re.I)}),
            ('a', {'rel': 'next'}),
            ('a', {'aria-label': re.compile(r'next', re.I)}),
            ('a', {'title': re.compile(r'next page', re.I)}),
            ('link', {'rel': 'next'}),  # HTML5 link tag
        ]

        for tag, attrs in pagination_patterns:
            next_link = soup.find(tag, attrs)
            if next_link and next_link.get('href'):
                href = next_link['href']

                # Make absolute URL
                from urllib.parse import urljoin
                next_url = urljoin(current_url, href)

                self.logger.info(f"Found pagination: {next_url}")
                return next_url

        # Look for numeric pagination (page 2, 3, etc.)
        # Only follow if it's clearly the next page
        current_page_num = self._extract_page_number(current_url)
        if current_page_num:
            next_page_num = current_page_num + 1
            # Look for link with next page number
            page_links = soup.find_all('a', href=True)
            for link in page_links:
                href = link['href']
                link_page_num = self._extract_page_number(href)
                if link_page_num == next_page_num:
                    from urllib.parse import urljoin
                    next_url = urljoin(current_url, href)
                    self.logger.info(f"Found numeric pagination: page {next_page_num}")
                    return next_url

        return None

    def _extract_page_number(self, url: str) -> Optional[int]:
        """Extract page number from URL"""
        # Common patterns: ?page=2, /page/2/, ?p=2
        patterns = [
            r'[?&]page=(\d+)',
            r'[?&]p=(\d+)',
            r'/page/(\d+)',
            r'/p/(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.I)
            if match:
                return int(match.group(1))

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
