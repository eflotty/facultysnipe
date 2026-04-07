#!/usr/bin/env python3
"""
Convert NEW contacts to OLD for baseline universities
Use this if baseline reset happened but contacts are still marked as NEW

This script:
1. Finds all contacts marked as NEW
2. Converts them to OLD (baseline)
3. Ensures first_scrape_completed = TRUE for all universities

Usage:
    python3 scripts/convert_new_to_old_baseline.py
"""

from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets import GoogleSheetsManager
from config import setup_logging

def convert_to_baseline():
    """Convert all NEW contacts to OLD (baseline)"""
    logger = setup_logging('ConvertBaseline')

    print("\n" + "="*60)
    print("⚠️  WARNING: CONVERT NEW TO OLD BASELINE")
    print("="*60)
    print("\nThis will:")
    print("  1. Find all contacts marked as NEW in NEW CONTACTS sheet")
    print("  2. Convert them to OLD (baseline)")
    print("  3. Set all universities to first_scrape_completed=TRUE")
    print("\nUse this if baseline reset happened but contacts are still NEW.")
    print("\n" + "="*60)

    response = input("\nAre you sure you want to proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return

    try:
        sheets = GoogleSheetsManager()

        # Step 1: Convert NEW contacts to OLD
        logger.info("Step 1: Converting NEW contacts to OLD in NEW CONTACTS sheet...")
        try:
            contacts_sheet = sheets.spreadsheet.worksheet('NEW CONTACTS')
            all_values = contacts_sheet.get_all_values()

            if len(all_values) < 2:
                logger.info("No contacts to convert")
                return

            headers = all_values[0]

            # Find Status column
            if 'Status' not in headers:
                logger.error("Status column not found!")
                return

            status_col_idx = headers.index('Status')
            col_letter = chr(ord('A') + status_col_idx)

            # Find all rows with NEW status
            updates = []
            new_count = 0

            for row_idx, row in enumerate(all_values[1:], start=2):
                if len(row) > status_col_idx:
                    status = row[status_col_idx].strip().upper()
                    if status == 'NEW':
                        updates.append({
                            'range': f'{col_letter}{row_idx}',
                            'values': [['OLD']]
                        })
                        new_count += 1

            if updates:
                # Batch update in chunks of 100 to avoid quota limits
                chunk_size = 100
                for i in range(0, len(updates), chunk_size):
                    chunk = updates[i:i + chunk_size]
                    contacts_sheet.batch_update(chunk)
                    logger.info(f"Updated {len(chunk)} contacts ({i + len(chunk)}/{len(updates)})")

                logger.info(f"✅ Converted {new_count} contacts from NEW to OLD")
                print(f"\n✅ Converted {new_count} contacts from NEW to OLD (baseline)")
            else:
                logger.info("No NEW contacts found to convert")
                print("\nℹ️  No NEW contacts found - already baseline")

        except Exception as e:
            logger.error(f"Failed to convert contacts: {e}")
            print(f"\n❌ Failed to convert contacts: {e}")
            return

        # Step 2: Mark all universities as first_scrape_completed=TRUE
        logger.info("Step 2: Ensuring all universities marked as first_scrape_completed=TRUE...")
        try:
            config_sheet = sheets.spreadsheet.worksheet('CONFIG')
            all_values = config_sheet.get_all_values()
            headers = all_values[0]

            if 'first_scrape_completed' not in headers:
                logger.error("first_scrape_completed column not found!")
                return

            fsc_col_idx = headers.index('first_scrape_completed')
            col_letter = chr(ord('A') + fsc_col_idx)

            # Update all rows to TRUE
            updates = []
            for row_idx in range(2, len(all_values) + 1):
                # Only update if not already TRUE
                if row_idx - 1 < len(all_values):
                    row = all_values[row_idx - 1]
                    if len(row) > fsc_col_idx:
                        current_value = row[fsc_col_idx].strip().upper()
                        if current_value != 'TRUE':
                            updates.append({
                                'range': f'{col_letter}{row_idx}',
                                'values': [['TRUE']]
                            })

            if updates:
                config_sheet.batch_update(updates)
                logger.info(f"✅ Marked {len(updates)} universities as first_scrape_completed=TRUE")
                print(f"✅ Marked {len(updates)} universities as baseline complete")
            else:
                logger.info("All universities already marked as complete")
                print("ℹ️  All universities already marked as baseline complete")

        except Exception as e:
            logger.error(f"Failed to update universities: {e}")
            print(f"\n❌ Failed to update universities: {e}")
            return

        print("\n" + "="*60)
        print("✅ BASELINE CONVERSION COMPLETE")
        print("="*60)
        print("\nAll existing contacts are now marked as OLD (baseline).")
        print("Future scrapes will mark new discoveries as NEW.")
        print("\n" + "="*60 + "\n")

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    convert_to_baseline()
