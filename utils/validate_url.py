#!/usr/bin/env python3
"""
URL Validator - Check if a faculty URL is scrapable
"""
import requests
from bs4 import BeautifulSoup
import argparse
import sys
from urllib.parse import urlparse


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
TIMEOUT = 30


def validate_url(url: str) -> dict:
    """
    Validate if URL is accessible and contains faculty data

    Args:
        url: Faculty directory URL

    Returns:
        Dictionary with validation results
    """
    result = {
        'url': url,
        'accessible': False,
        'status_code': None,
        'has_emails': False,
        'email_count': 0,
        'has_names': False,
        'name_count': 0,
        'likely_faculty_page': False,
        'warnings': [],
        'recommendations': []
    }

    # Check URL format
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        result['warnings'].append("Invalid URL format")
        return result

    # Try to fetch the page
    try:
        response = requests.get(
            url,
            headers={'User-Agent': USER_AGENT},
            timeout=TIMEOUT,
            allow_redirects=True
        )
        result['status_code'] = response.status_code

        if response.status_code != 200:
            result['warnings'].append(f"HTTP {response.status_code} - Page may not be accessible")
            return result

        result['accessible'] = True

        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')

        # Check for emails
        mailto_links = soup.find_all('a', href=lambda x: x and 'mailto:' in x)
        result['email_count'] = len(mailto_links)
        result['has_emails'] = result['email_count'] > 0

        # Check for person names (capitalized two+ word sequences)
        import re
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        text = soup.get_text()
        names = re.findall(name_pattern, text)
        result['name_count'] = len(set(names))  # Unique names
        result['has_names'] = result['name_count'] >= 3

        # Check for faculty-related keywords
        faculty_keywords = ['faculty', 'professor', 'staff', 'people', 'directory', 'department']
        keyword_matches = sum(1 for kw in faculty_keywords if kw in text.lower())

        # Determine if likely a faculty page
        result['likely_faculty_page'] = (
            result['has_emails'] and
            result['has_names'] and
            keyword_matches >= 2
        )

        # Generate recommendations
        if not result['has_emails']:
            result['recommendations'].append("No email addresses found - page may not list contact info")

        if not result['has_names']:
            result['recommendations'].append(f"Only found {result['name_count']} names - may not be a faculty directory")

        if keyword_matches < 2:
            result['recommendations'].append("Few faculty-related keywords found - verify this is a faculty page")

        if result['likely_faculty_page']:
            result['recommendations'].append("✓ This looks like a valid faculty page!")
        else:
            result['recommendations'].append("⚠ This may not be an ideal faculty page - verify manually")

    except requests.exceptions.Timeout:
        result['warnings'].append("Request timed out - server may be slow")
    except requests.exceptions.ConnectionError:
        result['warnings'].append("Connection error - check URL or network")
    except Exception as e:
        result['warnings'].append(f"Error: {str(e)}")

    return result


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(description='Validate faculty directory URL')
    parser.add_argument('url', help='Faculty directory URL to validate')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    args = parser.parse_args()

    print("=" * 70)
    print(f"Validating URL: {args.url}")
    print("=" * 70)
    print()

    result = validate_url(args.url)

    # Print results
    print(f"Status: {'✓ Accessible' if result['accessible'] else '✗ Not accessible'}")
    if result['status_code']:
        print(f"HTTP Status: {result['status_code']}")
    print()

    print(f"Emails found: {result['email_count']}")
    print(f"Names found: {result['name_count']}")
    print(f"Likely faculty page: {'YES' if result['likely_faculty_page'] else 'NO'}")
    print()

    if result['warnings']:
        print("⚠ WARNINGS:")
        for warning in result['warnings']:
            print(f"  - {warning}")
        print()

    if result['recommendations']:
        print("RECOMMENDATIONS:")
        for rec in result['recommendations']:
            print(f"  {rec}")
        print()

    print("=" * 70)

    # Exit code based on validation
    if result['likely_faculty_page']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
