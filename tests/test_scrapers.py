"""
Unit tests for scraper classes
"""
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.base_scraper import Faculty, BaseScraper


class TestFacultyDataclass(unittest.TestCase):
    """Test Faculty dataclass"""

    def test_faculty_creation(self):
        """Test creating Faculty object"""
        faculty = Faculty(
            name="Dr. Jane Smith",
            title="Professor",
            email="jsmith@university.edu"
        )

        self.assertEqual(faculty.name, "Dr. Jane Smith")
        self.assertEqual(faculty.title, "Professor")
        self.assertEqual(faculty.email, "jsmith@university.edu")
        self.assertIsNotNone(faculty.faculty_id)
        self.assertEqual(len(faculty.faculty_id), 16)

    def test_faculty_id_generation(self):
        """Test deterministic ID generation"""
        faculty1 = Faculty(
            name="John Doe",
            title="Assistant Professor",
            email="jdoe@uni.edu"
        )

        faculty2 = Faculty(
            name="John Doe",
            title="Assistant Professor",
            email="jdoe@uni.edu"
        )

        # Same data should generate same ID
        self.assertEqual(faculty1.faculty_id, faculty2.faculty_id)

    def test_faculty_id_uniqueness(self):
        """Test that different faculty get different IDs"""
        faculty1 = Faculty(
            name="Alice Johnson",
            email="alice@uni.edu"
        )

        faculty2 = Faculty(
            name="Bob Williams",
            email="bob@uni.edu"
        )

        self.assertNotEqual(faculty1.faculty_id, faculty2.faculty_id)

    def test_to_dict(self):
        """Test converting Faculty to dictionary"""
        faculty = Faculty(
            name="Test Person",
            email="test@test.com",
            raw_data={"custom": "value"}
        )

        data = faculty.to_dict()

        self.assertIsInstance(data, dict)
        self.assertEqual(data['name'], "Test Person")
        self.assertEqual(data['email'], "test@test.com")
        self.assertIsInstance(data['raw_data'], str)  # Should be JSON string

    def test_from_dict(self):
        """Test creating Faculty from dictionary"""
        data = {
            'name': 'Test Person',
            'email': 'test@test.com',
            'title': 'Professor',
            'raw_data': '{"custom": "value"}'
        }

        faculty = Faculty.from_dict(data)

        self.assertEqual(faculty.name, "Test Person")
        self.assertEqual(faculty.email, "test@test.com")
        self.assertIsInstance(faculty.raw_data, dict)


class TestBaseScraper(unittest.TestCase):
    """Test BaseScraper methods"""

    def test_validate_valid_faculty(self):
        """Test validation accepts valid faculty"""

        class TestScraper(BaseScraper):
            def scrape(self):
                pass

        scraper = TestScraper(url="http://test.com", university_id="test")

        faculty_list = [
            Faculty(name="John Doe", email="john@test.com"),
            Faculty(name="Jane Smith", profile_url="http://test.com/jane")
        ]

        validated = scraper.validate(faculty_list)

        self.assertEqual(len(validated), 2)

    def test_validate_rejects_invalid(self):
        """Test validation rejects invalid faculty"""

        class TestScraper(BaseScraper):
            def scrape(self):
                pass

        scraper = TestScraper(url="http://test.com", university_id="test")

        faculty_list = [
            Faculty(name="John Doe", email="john@test.com"),  # Valid
            Faculty(name=""),  # Invalid - no name
            Faculty(name="X"),  # Invalid - name too short
            Faculty(name="No Contact Info")  # Invalid - no contact
        ]

        validated = scraper.validate(faculty_list)

        # Only first one should pass
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0].name, "John Doe")


if __name__ == '__main__':
    unittest.main()
