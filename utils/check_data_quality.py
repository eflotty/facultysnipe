#!/usr/bin/env python3
"""
Data Quality Checker - Analyze faculty data quality
"""
import sys
import os
import argparse
from dotenv import load_dotenv
from collections import Counter

# Load environment
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets import GoogleSheetsManager


def check_data_quality(university_id: str = None) -> dict:
    """
    Check data quality for faculty entries

    Args:
        university_id: Optional specific university to check

    Returns:
        Dictionary with quality metrics
    """
    sheets = GoogleSheetsManager()

    # Get universities to check
    if university_id:
        universities = [{'university_id': university_id}]
    else:
        universities = sheets.get_universities_config()

    results = {}

    for univ in universities:
        univ_id = univ['university_id']

        try:
            faculty_data = sheets.get_existing_faculty(univ_id)

            if not faculty_data:
                results[univ_id] = {
                    'total': 0,
                    'quality_score': 0,
                    'issues': ['No faculty data found']
                }
                continue

            # Analyze data quality
            total = len(faculty_data)
            has_email = sum(1 for f in faculty_data.values() if f.get('email'))
            has_title = sum(1 for f in faculty_data.values() if f.get('title'))
            has_profile_url = sum(1 for f in faculty_data.values() if f.get('profile_url'))
            has_department = sum(1 for f in faculty_data.values() if f.get('department'))

            # Check for duplicates
            names = [f.get('name', '') for f in faculty_data.values()]
            name_counts = Counter(names)
            duplicates = [name for name, count in name_counts.items() if count > 1 and name]

            # Check for incomplete data
            no_contact = sum(1 for f in faculty_data.values()
                           if not f.get('email') and not f.get('profile_url'))

            # Calculate quality score (0-100)
            email_score = (has_email / total) * 30
            title_score = (has_title / total) * 20
            profile_score = (has_profile_url / total) * 25
            dept_score = (has_department / total) * 15
            completeness_score = ((total - no_contact) / total) * 10

            quality_score = int(email_score + title_score + profile_score +
                              dept_score + completeness_score)

            # Identify issues
            issues = []
            if has_email / total < 0.5:
                issues.append(f"Low email coverage: {has_email}/{total} ({has_email/total*100:.1f}%)")

            if has_title / total < 0.7:
                issues.append(f"Missing titles: {total - has_title}/{total}")

            if no_contact > 0:
                issues.append(f"No contact info: {no_contact} faculty")

            if duplicates:
                issues.append(f"Duplicate names: {', '.join(duplicates[:3])}")

            results[univ_id] = {
                'total': total,
                'has_email': has_email,
                'has_title': has_title,
                'has_profile_url': has_profile_url,
                'has_department': has_department,
                'no_contact': no_contact,
                'duplicates': len(duplicates),
                'quality_score': quality_score,
                'issues': issues
            }

        except Exception as e:
            results[univ_id] = {
                'total': 0,
                'quality_score': 0,
                'issues': [f'Error: {str(e)}']
            }

    return results


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(description='Check faculty data quality')
    parser.add_argument('--university', '-u', help='Check specific university only')
    parser.add_argument('--min-score', type=int, default=0,
                       help='Only show universities below this quality score')
    args = parser.parse_args()

    print("=" * 70)
    print("FacultySnipe - Data Quality Report")
    print("=" * 70)
    print()

    print("Analyzing data...")
    results = check_data_quality(args.university)

    if not results:
        print("No universities found")
        return

    print()

    # Sort by quality score
    sorted_results = sorted(results.items(), key=lambda x: x[1]['quality_score'])

    for univ_id, metrics in sorted_results:
        if metrics['quality_score'] < args.min_score:
            continue

        # Determine grade
        score = metrics['quality_score']
        if score >= 90:
            grade = "A (Excellent)"
        elif score >= 80:
            grade = "B (Good)"
        elif score >= 70:
            grade = "C (Fair)"
        elif score >= 60:
            grade = "D (Poor)"
        else:
            grade = "F (Critical)"

        print(f"University: {univ_id}")
        print(f"Quality Score: {score}/100 - {grade}")
        print(f"Total Faculty: {metrics['total']}")

        if metrics['total'] > 0:
            print(f"  - With Email: {metrics.get('has_email', 0)}/{metrics['total']} ({metrics.get('has_email', 0)/metrics['total']*100:.1f}%)")
            print(f"  - With Title: {metrics.get('has_title', 0)}/{metrics['total']} ({metrics.get('has_title', 0)/metrics['total']*100:.1f}%)")
            print(f"  - With Profile URL: {metrics.get('has_profile_url', 0)}/{metrics['total']}")

        if metrics.get('issues'):
            print("  Issues:")
            for issue in metrics['issues']:
                print(f"    ⚠ {issue}")

        print()

    print("=" * 70)
    print("Quality Scoring:")
    print("  - Email (30 pts): Contact information")
    print("  - Title (20 pts): Position/rank clarity")
    print("  - Profile URL (25 pts): Link to full profile")
    print("  - Department (15 pts): Organization context")
    print("  - Completeness (10 pts): At least one contact method")
    print("=" * 70)


if __name__ == '__main__':
    main()
