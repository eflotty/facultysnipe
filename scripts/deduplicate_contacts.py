#!/usr/bin/env python3
"""
Deduplicate contacts in NEW CONTACTS sheet

This script identifies and removes duplicate faculty members in the NEW CONTACTS sheet.
Duplicates can occur when the sheet lookup fails, causing everyone to be marked as "new"
on every scrape run.

The script keeps the EARLIEST entry for each faculty_id and removes later duplicates.
"""
import sys
import os
from datetime import datetime
from collections import defaultdict

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets import GoogleSheetsManager
from config import setup_logging


def deduplicate_new_contacts(dry_run=True):
    """
    Remove duplicate contacts from NEW CONTACTS sheet

    Args:
        dry_run: If True, only report duplicates without removing them
    """
    logger = setup_logging('DeduplicateContacts')

    try:
        sheets = GoogleSheetsManager()

        # Get NEW CONTACTS sheet
        logger.info("Loading NEW CONTACTS sheet...")
        contacts_sheet = sheets.spreadsheet.worksheet('NEW CONTACTS')

        # Get all data including row numbers
        all_values = contacts_sheet.get_all_values()

        if len(all_values) <= 1:
            logger.info("NEW CONTACTS sheet is empty")
            return

        headers = all_values[0]

        # Find column indices
        try:
            faculty_id_col = headers.index('Faculty ID')
            date_added_col = headers.index('Date Added')
            name_col = headers.index('Name')
            status_col = headers.index('Status')
        except ValueError as e:
            logger.error(f"Required column not found: {e}")
            return

        logger.info(f"Found {len(all_values) - 1} total rows")

        # Track entries by faculty_id
        # faculty_id -> [(row_number, date_added, full_row)]
        entries_by_id = defaultdict(list)

        for row_idx, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
            if len(row) <= faculty_id_col:
                continue

            faculty_id = row[faculty_id_col].strip()
            if not faculty_id:
                continue

            date_added = row[date_added_col] if len(row) > date_added_col else ''
            entries_by_id[faculty_id].append((row_idx, date_added, row))

        # Find duplicates
        duplicates_info = {}
        total_duplicate_rows = 0

        for faculty_id, entries in entries_by_id.items():
            if len(entries) > 1:
                # Sort by date added (earliest first)
                entries.sort(key=lambda x: x[1])  # Sort by date_added

                # Keep first entry, mark others as duplicates
                keep_row = entries[0]
                duplicate_rows = entries[1:]

                name = keep_row[2][name_col] if len(keep_row[2]) > name_col else 'Unknown'
                duplicates_info[faculty_id] = {
                    'name': name,
                    'keep_row': keep_row[0],
                    'keep_date': keep_row[1],
                    'duplicate_rows': [r[0] for r in duplicate_rows],
                    'duplicate_count': len(duplicate_rows)
                }
                total_duplicate_rows += len(duplicate_rows)

        # Print report
        logger.info("")
        logger.info("=" * 70)
        logger.info("DUPLICATE DETECTION REPORT")
        logger.info("=" * 70)
        logger.info(f"Total rows in NEW CONTACTS: {len(all_values) - 1}")
        logger.info(f"Unique faculty members: {len(entries_by_id)}")
        logger.info(f"Faculty members with duplicates: {len(duplicates_info)}")
        logger.info(f"Total duplicate rows to remove: {total_duplicate_rows}")
        logger.info("")

        if not duplicates_info:
            logger.info("✅ No duplicates found!")
            return

        # Show top 20 most duplicated
        logger.info("Top 20 most duplicated faculty members:")
        logger.info("-" * 70)

        sorted_duplicates = sorted(
            duplicates_info.items(),
            key=lambda x: x[1]['duplicate_count'],
            reverse=True
        )

        for faculty_id, info in sorted_duplicates[:20]:
            logger.info(
                f"  {info['name'][:40]:40} - {info['duplicate_count'] + 1} entries "
                f"(keeping row {info['keep_row']}, removing {info['duplicate_count']})"
            )

        logger.info("")
        logger.info("=" * 70)

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

        # Collect all rows to delete (in reverse order to avoid index shifting)
        rows_to_delete = []
        for info in duplicates_info.values():
            rows_to_delete.extend(info['duplicate_rows'])

        rows_to_delete.sort(reverse=True)  # Delete from bottom to top

        logger.info(f"Deleting {len(rows_to_delete)} rows...")

        # Delete in batches (Google Sheets API limits)
        batch_size = 100
        deleted_count = 0

        for i in range(0, len(rows_to_delete), batch_size):
            batch = rows_to_delete[i:i + batch_size]

            for row_num in batch:
                try:
                    contacts_sheet.delete_rows(row_num)
                    deleted_count += 1

                    if deleted_count % 10 == 0:
                        logger.info(f"  Deleted {deleted_count}/{len(rows_to_delete)} rows...")

                except Exception as e:
                    logger.error(f"Failed to delete row {row_num}: {e}")

        logger.info("")
        logger.info("=" * 70)
        logger.info(f"✅ DEDUPLICATION COMPLETE")
        logger.info(f"   Removed {deleted_count} duplicate rows")
        logger.info(f"   Remaining unique contacts: {len(entries_by_id)}")
        logger.info("=" * 70)

        return deleted_count

    except Exception as e:
        logger.error(f"Failed to deduplicate contacts: {e}", exc_info=True)
        raise


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Deduplicate contacts in NEW CONTACTS sheet'
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
        deduplicate_new_contacts(dry_run=not args.execute)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
