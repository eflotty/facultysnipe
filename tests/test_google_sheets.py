"""
Tests for Google Sheets integration
NOTE: These tests require actual Google Sheets credentials
For true unit tests, mock the gspread library
"""
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.base_scraper import Faculty


class TestGoogleSheetsIntegration(unittest.TestCase):
    """
    Integration tests for Google Sheets

    NOTE: These require actual credentials and a test spreadsheet.
    To run these tests:
    1. Set up a test Google Sheet
    2. Set environment variables
    3. Run: python -m pytest tests/test_google_sheets.py

    For CI/CD, these should be mocked.
    """

    def setUp(self):
        """Setup test - skip if no credentials"""
        try:
            from dotenv import load_dotenv
            load_dotenv()

            from config import GOOGLE_SHEETS_CREDENTIALS, GOOGLE_SHEET_ID

            if not GOOGLE_SHEETS_CREDENTIALS or not GOOGLE_SHEET_ID:
                self.skipTest("Google Sheets credentials not configured")

            from google_sheets import GoogleSheetsManager
            self.sheets = GoogleSheetsManager()

        except Exception as e:
            self.skipTest(f"Cannot initialize Google Sheets: {e}")

    def test_connection(self):
        """Test Google Sheets connection"""
        self.assertIsNotNone(self.sheets.spreadsheet)
        self.assertIsNotNone(self.sheets.spreadsheet.title)

    def test_get_universities_config(self):
        """Test loading university configuration"""
        universities = self.sheets.get_universities_config()

        self.assertIsInstance(universities, list)
        # May be empty if no universities configured yet

    def test_faculty_data_roundtrip(self):
        """Test writing and reading faculty data"""
        # Create test faculty
        test_faculty = [
            Faculty(
                name="Test Faculty 1",
                email="test1@test.com",
                title="Test Professor"
            ),
            Faculty(
                name="Test Faculty 2",
                email="test2@test.com",
                title="Test Associate Professor"
            )
        ]

        # Write to test sheet
        test_university_id = "test_university"

        new, changed, removed = self.sheets.update_faculty(
            university_id=test_university_id,
            faculty_list=test_faculty
        )

        # All should be new on first run
        self.assertEqual(len(new), 2)
        self.assertEqual(len(changed), 0)
        self.assertEqual(len(removed), 0)

        # Read back
        existing = self.sheets.get_existing_faculty(test_university_id)
        self.assertEqual(len(existing), 2)


class TestMockedGoogleSheets(unittest.TestCase):
    """
    Unit tests with mocked Google Sheets
    TODO: Implement using unittest.mock
    """

    def test_placeholder(self):
        """Placeholder for mocked tests"""
        # TODO: Implement mocked tests for CI/CD
        pass


if __name__ == '__main__':
    unittest.main()
