#!/usr/bin/env python3
"""
Deduplicate contacts by name + university (not just faculty_id)

This script handles the April 30 duplicate issue where the same person
appears multiple times with different faculty_ids (due to missing emails).

Strategy:
- Group by (name, university) combination
- Keep the entry WITH email if available
- Otherwise keep the OLDEST entry
- Delete all other duplicates
"""
import sys
import os
from datetime import datetime
from collections import defaultdict

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
load_dotenv()

from google_sheets import GoogleSheetsManager
from config import setup_logging


def deduplicate_by_name_university(dry_run=True):
    """
    Remove duplicate contacts by name + university combination

    Args:
        dry_run: If True, only report duplicates without removing them
    """
    logger = setup_logging('DeduplicateByName')

    try:
        sheets = GoogleSheetsManager()

        # Get NEW CONTACTS sheet
        logger.info("Loading NEW CONTACTS sheet...")
        contacts_sheet = sheets.spreadsheet.worksheet('NEW CONTACTS')

        # Get all data
        all_values = contacts_sheet.get_all_values()

        if len(all_values) <= 1:
            logger.info("NEW CONTACTS sheet is empty")
            return

        headers = all_values[0]

        # Find column indices
        try:
            name_col = headers.index('Name')
            university_col = headers.index('University')
            email_col = headers.index('Email')
            date_added_col = headers.index('Date Added')
            faculty_id_col = headers.index('Faculty ID')
        except ValueError as e:
            logger.error(f"Required column not found: {e}")
            return

        logger.info(f"Found {len(all_values) - 1} total rows")

        # Group by (name, university)
        # key: (name, university) -> list of (row_number, email, date_added, faculty_id, full_row)
        entries_by_name_uni = defaultdict(list)

        for row_idx, row in enumerate(all_values[1:], start=2):  # Start at row 2
            if len(row) <= max(name_col, university_col):
                continue

            name = row[name_col].strip()
            university = row[university_col].strip()

            if not name or not university:
                continue

            email = row[email_col].strip() if len(row) > email_col else ''
            date_added = row[date_added_col] if len(row) > date_added_col else ''
            faculty_id = row[faculty_id_col] if len(row) > faculty_id_col else ''

            key = (name, university)
            entries_by_name_uni[key].append((row_idx, email, date_added, faculty_id, row))

        # Find duplicates
        duplicates_info = {}
        total_duplicate_rows = 0

        for (name, university), entries in entries_by_name_uni.items():
            if len(entries) > 1:
                # Sort by priority:
                # 1. Has email (True > False)
                # 2. Date added (earlier date first)
                entries_sorted = sorted(
                    entries,
                    key=lambda x: (x[1] == '', x[2])  # Empty email last, then by date
                )

                # Keep first entry (has email, or oldest)
                keep_entry = entries_sorted[0]
                duplicate_entries = entries_sorted[1:]

                duplicates_info[(name, university)] = {
                    'name': name,
                    'university': university,
                    'keep_row': keep_entry[0],
                    'keep_email': keep_entry[1] or 'NO EMAIL',
                    'keep_date': keep_entry[2],
                    'keep_faculty_id': keep_entry[3],
                    'duplicate_rows': [e[0] for e in duplicate_entries],
                    'duplicate_details': [
                        {
                            'row': e[0],
                            'email': e[1] or 'NO EMAIL',
                            'date': e[2],
                            'faculty_id': e[3]
                        }
                        for e in duplicate_entries
                    ],
                    'duplicate_count': len(duplicate_entries)
                }
                total_duplicate_rows += len(duplicate_entries)

        # Print report
        logger.info("")
        logger.info("=" * 80)
        logger.info("DUPLICATE DETECTION REPORT (by Name + University)")
        logger.info("=" * 80)
        logger.info(f"Total rows in NEW CONTACTS: {len(all_values) - 1}")
        logger.info(f"Unique (name, university) combinations: {len(entries_by_name_uni)}")
        logger.info(f"Combinations with duplicates: {len(duplicates_info)}")
        logger.info(f"Total duplicate rows to remove: {total_duplicate_rows}")
        logger.info("")

        if not duplicates_info:
            logger.info("✅ No duplicates found!")
            return

        # Show top 20 most duplicated
        logger.info("Top 20 most duplicated people:")
        logger.info("-" * 80)

        sorted_duplicates = sorted(
            duplicates_info.items(),
            key=lambda x: x[1]['duplicate_count'],
            reverse=True
        )

        for (name, university), info in sorted_duplicates[:20]:
            uni_short = university[:50] if len(university) > 50 else university
            logger.info(
                f"  {name[:30]:30} @ {uni_short:50}"
            )
            logger.info(
                f"    Keeping: Row {info['keep_row']:4} | {info['keep_email'][:40]:40} | {info['keep_date'][:10]}"
            )
            for dup in info['duplicate_details']:
                logger.info(
                    f"    Removing: Row {dup['row']:4} | {dup['email'][:40]:40} | {dup['date'][:10]}"
                )
            logger.info("")

        logger.info("=" * 80)

        if dry_run:
            logger.info("")
            logger.info("🔍 DRY RUN MODE - No changes made")
            logger.info("Run with --execute flag to remove duplicates")
            logger.info("")
            logger.info(f"Would remove {total_duplicate_rows} duplicate rows")
            return total_duplicate_rows

        # Execute removal
        logger.info("")
        logger.info("🔧 EXECUTING REMOVAL...")
        logger.info("")

        # Collect all rows to delete (in reverse order)
        rows_to_delete = []
        for info in duplicates_info.values():
            rows_to_delete.extend(info['duplicate_rows'])

        rows_to_delete.sort(reverse=True)  # Delete from bottom to top

        logger.info(f"Deleting {len(rows_to_delete)} rows...")

        # Delete rows
        deleted_count = 0

        for row_num in rows_to_delete:
            try:
                contacts_sheet.delete_rows(row_num)
                deleted_count += 1

                if deleted_count % 10 == 0:
                    logger.info(f"  Deleted {deleted_count}/{len(rows_to_delete)} rows...")

            except Exception as e:
                logger.error(f"Failed to delete row {row_num}: {e}")

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"✅ DEDUPLICATION COMPLETE")
        logger.info(f"   Removed {deleted_count} duplicate rows")
        logger.info(f"   Remaining unique contacts: {len(entries_by_name_uni)}")
        logger.info("=" * 80)

        return deleted_count

    except Exception as e:
        logger.error(f"Failed to deduplicate contacts: {e}", exc_info=True)
        raise


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Deduplicate contacts by name + university (not just faculty_id)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually remove duplicates (default is dry-run)'
    )

    args = parser.parse_args()

    if args.execute:
        print("\n⚠️  WARNING: This will PERMANENTLY DELETE duplicate rows!")
        print("Are you sure you want to continue? (yes/no): ", end='')
        response = input().strip().lower()

        if response != 'yes':
            print("Aborted.")
            return 1

    try:
        deduplicate_by_name_university(dry_run=not args.execute)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
