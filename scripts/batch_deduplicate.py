#!/usr/bin/env python3
"""
Batch deduplicate contacts using Google Sheets batch API

This is a faster, rate-limit-friendly version that uses batch operations
instead of deleting rows one at a time.

Strategy:
1. Identify all duplicate rows
2. Create a new sheet with only unique contacts
3. Delete old NEW CONTACTS sheet
4. Rename new sheet to NEW CONTACTS

This avoids hitting rate limits from 2,500+ individual delete operations.
"""
import sys
import os
from collections import defaultdict

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
load_dotenv()

from google_sheets import GoogleSheetsManager
from config import setup_logging


def batch_deduplicate(dry_run=True):
    """
    Deduplicate by creating new sheet with only unique contacts

    Args:
        dry_run: If True, only report what would be done
    """
    logger = setup_logging('BatchDeduplicate')

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
        except ValueError as e:
            logger.error(f"Required column not found: {e}")
            return

        logger.info(f"Found {len(all_values) - 1} total rows")

        # Group by (name, university)
        entries_by_name_uni = defaultdict(list)

        for row_idx, row in enumerate(all_values[1:], start=1):  # Start at 1 (data rows)
            if len(row) <= max(name_col, university_col):
                continue

            name = row[name_col].strip()
            university = row[university_col].strip()

            if not name or not university:
                continue

            email = row[email_col].strip() if len(row) > email_col else ''
            date_added = row[date_added_col] if len(row) > date_added_col else ''

            key = (name, university)
            entries_by_name_uni[key].append((row_idx, email, date_added, row))

        # Select which row to keep for each duplicate group
        unique_rows = [headers]  # Start with headers
        duplicates_removed = 0

        for (name, university), entries in entries_by_name_uni.items():
            if len(entries) == 1:
                # No duplicates, keep it
                unique_rows.append(entries[0][3])
            else:
                # Duplicates - sort and keep best one
                entries_sorted = sorted(
                    entries,
                    key=lambda x: (x[1] == '', x[2])  # Empty email last, then by date
                )

                # Keep first entry (has email, or oldest)
                unique_rows.append(entries_sorted[0][3])
                duplicates_removed += len(entries) - 1

        logger.info("")
        logger.info("=" * 80)
        logger.info("BATCH DEDUPLICATION REPORT")
        logger.info("=" * 80)
        logger.info(f"Total rows (current): {len(all_values) - 1}")
        logger.info(f"Unique contacts: {len(unique_rows) - 1}")
        logger.info(f"Duplicates to remove: {duplicates_removed}")
        logger.info(f"Final row count: {len(unique_rows) - 1}")
        logger.info("=" * 80)

        if dry_run:
            logger.info("")
            logger.info("🔍 DRY RUN MODE - No changes made")
            logger.info("Run with --execute flag to perform deduplication")
            return duplicates_removed

        # Execute: Create new sheet with deduplicated data
        logger.info("")
        logger.info("🔧 EXECUTING BATCH DEDUPLICATION...")
        logger.info("")

        # Step 1: Create temporary sheet with unique data
        logger.info("Creating temporary sheet with deduplicated data...")
        temp_sheet = sheets.spreadsheet.add_worksheet(
            title='NEW_CONTACTS_DEDUPLICATED',
            rows=len(unique_rows) + 100,
            cols=len(headers)
        )

        # Write all unique rows in one batch
        logger.info(f"Writing {len(unique_rows)} rows to temporary sheet...")
        temp_sheet.update('A1', unique_rows, value_input_option='RAW')

        # Step 2: Format header row
        logger.info("Formatting header row...")
        temp_sheet.format('A1:Z1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.2, 'green': 0.7, 'blue': 0.3}
        })

        # Step 3: Delete old NEW CONTACTS sheet
        logger.info("Deleting old NEW CONTACTS sheet...")
        sheets.spreadsheet.del_worksheet(contacts_sheet)

        # Step 4: Rename temporary sheet to NEW CONTACTS
        logger.info("Renaming deduplicated sheet to 'NEW CONTACTS'...")
        temp_sheet.update_title('NEW CONTACTS')

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ BATCH DEDUPLICATION COMPLETE")
        logger.info(f"   Removed {duplicates_removed} duplicate rows")
        logger.info(f"   Final contact count: {len(unique_rows) - 1}")
        logger.info("=" * 80)

        return duplicates_removed

    except Exception as e:
        logger.error(f"Failed to deduplicate contacts: {e}", exc_info=True)
        raise


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Batch deduplicate contacts (faster, avoids rate limits)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually perform deduplication (default is dry-run)'
    )

    args = parser.parse_args()

    if args.execute:
        print("\n⚠️  WARNING: This will replace NEW CONTACTS sheet with deduplicated version!")
        print("Are you sure you want to continue? (yes/no): ", end='')
        response = input().strip().lower()

        if response != 'yes':
            print("Aborted.")
            return 1

    try:
        batch_deduplicate(dry_run=not args.execute)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
