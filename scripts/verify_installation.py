#!/usr/bin/env python3
"""
Verification script to check FacultySnipe installation
Run this after setup to verify everything is configured correctly
"""
import os
import sys
import json
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'


def check_mark(passed):
    return f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"


def print_header(text):
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}{text}{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")


def check_file_structure():
    """Check if all required files exist"""
    print_header("Checking File Structure")

    required_files = [
        'requirements.txt',
        '.env.example',
        '.gitignore',
        'README.md',
        'src/main.py',
        'src/config.py',
        'src/google_sheets.py',
        'src/email_notifier.py',
        'src/scrapers/base_scraper.py',
        'src/scrapers/static_scraper.py',
        'src/scrapers/dynamic_scraper.py',
        'src/scrapers/registry.py',
        'src/universities/template.py',
        '.github/workflows/faculty_monitor.yml'
    ]

    all_present = True
    for file_path in required_files:
        exists = Path(file_path).exists()
        status = check_mark(exists)
        print(f"{status} {file_path}")
        all_present = all_present and exists

    return all_present


def check_environment_variables():
    """Check if environment variables are set"""
    print_header("Checking Environment Variables")

    # Load .env if exists
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        print(f"{GREEN}✓{RESET} .env file found")
    else:
        print(f"{YELLOW}⚠{RESET} .env file not found (expected for initial setup)")
        return False

    required_vars = [
        'GOOGLE_SHEETS_CREDENTIALS',
        'GOOGLE_SHEET_ID',
        'SMTP_HOST',
        'SMTP_PORT',
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'SENDER_EMAIL'
    ]

    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        is_set = value is not None and value != ''
        status = check_mark(is_set)

        # Don't print full value for security
        display_value = 'SET' if is_set else 'NOT SET'
        print(f"{status} {var}: {display_value}")

        all_set = all_set and is_set

    return all_set


def check_credentials_format():
    """Check if Google credentials are valid JSON"""
    print_header("Checking Google Credentials Format")

    creds = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    if not creds:
        print(f"{RED}✗{RESET} GOOGLE_SHEETS_CREDENTIALS not set")
        return False

    try:
        creds_dict = json.loads(creds)
        required_keys = ['type', 'project_id', 'private_key', 'client_email']

        all_valid = True
        for key in required_keys:
            has_key = key in creds_dict
            status = check_mark(has_key)
            print(f"{status} Has '{key}' field")
            all_valid = all_valid and has_key

        return all_valid

    except json.JSONDecodeError:
        print(f"{RED}✗{RESET} Invalid JSON format")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Python Dependencies")

    required_packages = [
        'gspread',
        'google.auth',
        'bs4',
        'playwright',
        'requests',
        'dotenv'
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package.replace('.', '_'))
            print(f"{GREEN}✓{RESET} {package}")
        except ImportError:
            print(f"{RED}✗{RESET} {package} - Run: pip install -r requirements.txt")
            all_installed = False

    return all_installed


def check_google_sheets_connection():
    """Test Google Sheets connection"""
    print_header("Testing Google Sheets Connection")

    try:
        sys.path.insert(0, 'src')
        from google_sheets import GoogleSheetsManager

        print("Attempting to connect to Google Sheets...")
        manager = GoogleSheetsManager()

        print(f"{GREEN}✓{RESET} Connected to: {manager.spreadsheet.title}")
        print(f"{GREEN}✓{RESET} Sheet ID: {os.getenv('GOOGLE_SHEET_ID')}")

        # Try to read CONFIG
        try:
            universities = manager.get_universities_config()
            print(f"{GREEN}✓{RESET} CONFIG sheet found")
            print(f"{GREEN}✓{RESET} Found {len(universities)} enabled universities")
            return True
        except Exception as e:
            print(f"{YELLOW}⚠{RESET} CONFIG sheet issue: {e}")
            return True  # Connection worked, just missing config

    except Exception as e:
        print(f"{RED}✗{RESET} Connection failed: {e}")
        return False


def main():
    """Run all verification checks"""
    print(f"\n{BOLD}FacultySnipe Installation Verification{RESET}")
    print(f"This script checks if your installation is configured correctly\n")

    results = {
        'File Structure': check_file_structure(),
        'Environment Variables': check_environment_variables(),
        'Dependencies': check_dependencies()
    }

    # Only check these if environment is configured
    if results['Environment Variables']:
        results['Credentials Format'] = check_credentials_format()
        results['Google Sheets Connection'] = check_google_sheets_connection()

    # Summary
    print_header("Verification Summary")

    all_passed = True
    for check, passed in results.items():
        status = check_mark(passed)
        print(f"{status} {check}")
        all_passed = all_passed and passed

    print()

    if all_passed:
        print(f"{GREEN}{BOLD}✓ All checks passed! FacultySnipe is ready to use.{RESET}")
        print(f"\nNext steps:")
        print(f"1. Add universities to CONFIG sheet in Google Sheets")
        print(f"2. Test locally: cd src && python main.py")
        print(f"3. Deploy to GitHub Actions")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}✗ Some checks failed. Please review the issues above.{RESET}")
        print(f"\nFor help:")
        print(f"- See SETUP_GUIDE.md for detailed setup instructions")
        print(f"- Check .env.example for required environment variables")
        print(f"- Ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == '__main__':
    main()
