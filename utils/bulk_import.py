#!/usr/bin/env python3
"""
Bulk Import - Import multiple universities from CSV file
"""
import csv
import argparse
import sys
import os
from dotenv import load_dotenv

# Load environment
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets import GoogleSheetsManager
from sheet_ux_helper import SheetUXHelper


def import_from_csv(csv_file: str, auto_fill: bool = True) -> int:
    """
    Import universities from CSV file

    CSV Format:
    url,sales_rep_email
    https://biology.stanford.edu/faculty,rep1@company.com
    https://med.miami.edu/microbiology/faculty,rep2@company.com

    Args:
        csv_file: Path to CSV file
        auto_fill: Whether to auto-fill other fields

    Returns:
        Number of universities imported
    """
    print(f"Loading universities from {csv_file}...")

    # Read CSV
    universities = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'url' not in row or not row['url'].strip():
                print(f"⚠ Skipping row with missing URL: {row}")
                continue

            universities.append({
                'url': row['url'].strip(),
                'sales_rep_email': row.get('sales_rep_email', '').strip(),
                'notes': row.get('notes', '').strip()
            })

    if not universities:
        print("✗ No valid universities found in CSV")
        return 0

    print(f"Found {len(universities)} universities in CSV")
    print()

    # Connect to Google Sheets
    print("Connecting to Google Sheets...")
    try:
        sheets = GoogleSheetsManager()
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return 0

    print("✓ Connected")
    print()

    # Get existing universities
    existing = sheets.get_universities_config()
    existing_urls = {u.get('url') for u in existing}

    # Prepare updates
    new_universities = []
    for univ in universities:
        if univ['url'] in existing_urls:
            print(f"⚠ Skipping duplicate URL: {univ['url']}")
            continue

        if auto_fill:
            print(f"Auto-filling fields for {univ['url']}...")
            auto_data = sheets.ux_helper.auto_fill_from_url(univ['url'])

            # Merge with CSV data
            auto_data['sales_rep_email'] = univ['sales_rep_email'] or auto_data['sales_rep_email']
            auto_data['notes'] = univ['notes'] or auto_data.get('notes', '')

            new_universities.append(auto_data)
        else:
            new_universities.append(univ)

    if not new_universities:
        print("No new universities to import (all are duplicates)")
        return 0

    print()
    print(f"Importing {len(new_universities)} new universities...")

    # Append to CONFIG sheet
    try:
        config_sheet = sheets.spreadsheet.worksheet('CONFIG')

        # Get headers
        headers = config_sheet.row_values(1)

        # Prepare rows
        rows = []
        for univ in new_universities:
            row = [univ.get(h.strip(), '') for h in headers]
            rows.append(row)

        # Append all rows
        config_sheet.append_rows(rows)

        print(f"✓ Successfully imported {len(new_universities)} universities")
        return len(new_universities)

    except Exception as e:
        print(f"✗ Failed to import: {e}")
        return 0


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description='Bulk import universities from CSV',
        epilog='''
CSV Format:
  url,sales_rep_email,notes
  https://biology.stanford.edu/faculty,rep@company.com,Stanford Biology
  https://med.miami.edu/microbiology/faculty,rep@company.com,Miami Micro

The 'url' column is required. Other fields are optional.
        '''
    )
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--no-auto-fill', action='store_true',
                       help='Disable auto-fill (use CSV data only)')
    args = parser.parse_args()

    print("=" * 70)
    print("FacultySnipe - Bulk Import Utility")
    print("=" * 70)
    print()

    if not os.path.exists(args.csv_file):
        print(f"✗ Error: File not found: {args.csv_file}")
        sys.exit(1)

    count = import_from_csv(args.csv_file, auto_fill=not args.no_auto_fill)

    print()
    print("=" * 70)
    if count > 0:
        print(f"✓ Import complete! Added {count} universities.")
        print()
        print("Next steps:")
        print("1. Review the CONFIG sheet in Google Sheets")
        print("2. Add sales_rep_email if missing")
        print("3. Run: python src/main.py")
    else:
        print("Import failed or no new universities added.")
    print("=" * 70)


if __name__ == '__main__':
    main()
