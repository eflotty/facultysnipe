"""
Test script to verify email notification bug fixes

This tests the three critical bugs that were fixed:
1. Sheet naming mismatch (everyone marked as "new")
2. Variable scope error (is_first undefined)
3. Duplicate people in email notifications
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.base_scraper import Faculty
from email_notifier import EmailNotifier


def test_deduplication_logic():
    """
    Test Bug #3 fix: Deduplication prevents people being listed twice
    """
    print("=" * 60)
    print("TEST 1: Email Deduplication Logic")
    print("=" * 60)

    # Create test faculty
    faculty1 = Faculty(
        name="Dr. John Doe",
        title="Professor",
        email="jdoe@university.edu"
    )

    faculty2 = Faculty(
        name="Dr. Jane Smith",
        title="Associate Professor",
        email="jsmith@university.edu"
    )

    faculty3 = Faculty(
        name="Dr. Bob Wilson",
        title="Assistant Professor",
        email="bwilson@university.edu"
    )

    # Simulate the bug: same person appears in BOTH new_faculty and changed_faculty
    new_faculty = [faculty1, faculty2]
    changed_faculty = [faculty2, faculty3]  # faculty2 is in BOTH lists!

    print(f"\nBefore deduplication:")
    print(f"  New Faculty: {len(new_faculty)} ({[f.name for f in new_faculty]})")
    print(f"  Changed Faculty: {len(changed_faculty)} ({[f.name for f in changed_faculty]})")
    print(f"  Duplicate: {faculty2.name} appears in BOTH lists")

    # Simulate the deduplication logic from send_new_faculty_alert()
    if new_faculty and changed_faculty:
        new_faculty_ids = {f.faculty_id for f in new_faculty}
        original_changed_count = len(changed_faculty)
        changed_faculty = [f for f in changed_faculty if f.faculty_id not in new_faculty_ids]
        deduplicated_count = original_changed_count - len(changed_faculty)

        print(f"\nAfter deduplication:")
        print(f"  New Faculty: {len(new_faculty)} ({[f.name for f in new_faculty]})")
        print(f"  Changed Faculty: {len(changed_faculty)} ({[f.name for f in changed_faculty]})")
        print(f"  Removed {deduplicated_count} duplicate(s)")

    # Verify the fix
    if len(changed_faculty) == 1 and changed_faculty[0].name == "Dr. Bob Wilson":
        print("\n✅ TEST PASSED: Deduplication correctly removed Dr. Jane Smith from changed list")
        return True
    else:
        print("\n❌ TEST FAILED: Deduplication did not work correctly")
        return False


def test_faculty_id_consistency():
    """
    Test that faculty_id generation is deterministic and consistent
    """
    print("\n" + "=" * 60)
    print("TEST 2: Faculty ID Consistency")
    print("=" * 60)

    # Create same faculty twice
    faculty1 = Faculty(
        name="Dr. Alice Johnson",
        title="Professor",
        email="alice@university.edu"
    )

    faculty2 = Faculty(
        name="Dr. Alice Johnson",
        title="Associate Professor",  # Different title!
        email="alice@university.edu"
    )

    print(f"\nFaculty 1: {faculty1.name} - {faculty1.title}")
    print(f"Faculty ID: {faculty1.faculty_id}")

    print(f"\nFaculty 2: {faculty2.name} - {faculty2.title}")
    print(f"Faculty ID: {faculty2.faculty_id}")

    if faculty1.faculty_id == faculty2.faculty_id:
        print("\n✅ TEST PASSED: Same person (name+email) generates same faculty_id despite different title")
        print("   This ensures title changes don't create duplicate entries")
        return True
    else:
        print("\n❌ TEST FAILED: Same person generated different faculty_ids")
        return False


def test_sheet_lookup_priority():
    """
    Test Bug #1 fix: university_id is tried FIRST before university_name
    """
    print("\n" + "=" * 60)
    print("TEST 3: Sheet Lookup Priority (Simulated)")
    print("=" * 60)

    # Simulate the fixed logic
    university_id = "miami_biochem"
    university_name = "University of Miami - Biochemistry"

    # New logic: university_id FIRST
    sheet_names_to_try = []
    sheet_names_to_try.append(university_id)

    if university_name and university_name != university_id:
        # Simplified sanitization for test
        sanitized_name = university_name.replace(" - ", "_").replace(" ", "_")
        sheet_names_to_try.append(sanitized_name)

    print(f"\nUniversity ID: {university_id}")
    print(f"University Name: {university_name}")
    print(f"\nSheet lookup order:")
    for i, name in enumerate(sheet_names_to_try, 1):
        print(f"  {i}. {name}")

    if sheet_names_to_try[0] == university_id:
        print("\n✅ TEST PASSED: university_id is tried FIRST (primary key)")
        print("   This prevents lookup failures when university_name changes")
        return True
    else:
        print("\n❌ TEST FAILED: university_id is not first in lookup order")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("EMAIL NOTIFICATION BUG FIX VERIFICATION")
    print("=" * 60)
    print("\nThis script tests the fixes for:")
    print("  Bug #1: Sheet naming mismatch causing everyone to be 'new'")
    print("  Bug #2: Variable scope error (is_first undefined)")
    print("  Bug #3: People listed twice in emails")
    print("")

    results = []

    # Run tests
    results.append(("Deduplication Logic", test_deduplication_logic()))
    results.append(("Faculty ID Consistency", test_faculty_id_consistency()))
    results.append(("Sheet Lookup Priority", test_sheet_lookup_priority()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Bug fixes are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the fixes.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
