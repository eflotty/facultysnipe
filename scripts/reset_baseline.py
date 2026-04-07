#!/usr/bin/env python3
"""
Reset baseline for all universities
This will:
1. Back up current NEW CONTACTS sheet (rename to NEW CONTACTS BACKUP)
2. Clear NEW CONTACTS sheet
3. Set all universities to first_scrape_completed=FALSE
4. Next scheduled run will re-scrape and establish fresh baseline

WARNING: This will clear all contact history!
Make sure you have a backup if needed.

Usage:
    python3 scripts/reset_baseline.py
"""

from dotenv import load_dotenv
load_dotenv()

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets import GoogleSheetsManager
from config import setup_logging

def reset_baseline():
    """Reset baseline for fresh start"""
    logger = setup_logging('ResetBaseline')

    print("\n" + "="*60)
    print("⚠️  WARNING: BASELINE RESET")
    print("="*60)
    print("\nThis will:")
    print("  1. Rename NEW CONTACTS → NEW CONTACTS BACKUP")
    print("  2. Create fresh NEW CONTACTS sheet")
    print("  3. Set all universities to first_scrape_completed=FALSE")
    print("  4. Next scrape will establish fresh baseline (all as OLD)")
    print("\n" + "="*60)

    response = input("\nAre you sure you want to proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return

    try:
        sheets = GoogleSheetsManager()

        # Step 1: Backup NEW CONTACTS sheet
        logger.info("Step 1: Backing up NEW CONTACTS sheet...")
        try:
            contacts_sheet = sheets.spreadsheet.worksheet('NEW CONTACTS')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'NEW CONTACTS BACKUP {timestamp}'
            contacts_sheet.update_title(backup_name)
            logger.info(f"✅ Backed up to: {backup_name}")
        except Exception as e:
            logger.error(f"Failed to backup: {e}")
            print(f"\n❌ Backup failed: {e}")
            return

        # Step 2: Create fresh NEW CONTACTS sheet
        logger.info("Step 2: Creating fresh NEW CONTACTS sheet...")
        try:
            new_contacts_sheet = sheets.spreadsheet.add_worksheet(
                title='NEW CONTACTS',
                rows=1000,
                cols=12
            )

            # Set headers
            headers = [
                'Date Added', 'University', 'Name', 'Title', 'Email',
                'Profile URL', 'Department', 'Phone', 'Research Interests',
                'Faculty ID', 'Status', 'Notes'
            ]
            new_contacts_sheet.update('A1:L1', [headers])

            # Format header row
            new_contacts_sheet.format('A1:L1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.7, 'blue': 0.3}
            })

            logger.info("✅ Created fresh NEW CONTACTS sheet")
        except Exception as e:
            logger.error(f"Failed to create new sheet: {e}")
            print(f"\n❌ Failed to create new sheet: {e}")
            return

        # Step 3: Reset all universities to first_scrape_completed=FALSE
        logger.info("Step 3: Resetting all universities to first_scrape_completed=FALSE...")
        try:
            config_sheet = sheets.spreadsheet.worksheet('CONFIG')
            all_values = config_sheet.get_all_values()
            headers = all_values[0]

            if 'first_scrape_completed' not in headers:
                logger.error("first_scrape_completed column not found!")
                return

            fsc_col_idx = headers.index('first_scrape_completed')
            col_letter = chr(ord('A') + fsc_col_idx)

            # Update all rows to FALSE
            updates = []
            for row_idx in range(2, len(all_values) + 1):
                updates.append({
                    'range': f'{col_letter}{row_idx}',
                    'values': [['FALSE']]
                })

            if updates:
                config_sheet.batch_update(updates)
                logger.info(f"✅ Reset {len(updates)} universities to first_scrape_completed=FALSE")

        except Exception as e:
            logger.error(f"Failed to reset universities: {e}")
            print(f"\n❌ Failed to reset universities: {e}")
            return

        print("\n" + "="*60)
        print("✅ BASELINE RESET COMPLETE")
        print("="*60)
        print("\nNext steps:")
        print("  1. Next scheduled run (Mon/Thu 8 PM UTC) will scrape all universities")
        print("  2. All contacts will be marked as OLD (baseline)")
        print("  3. Future scrapes will mark new discoveries as NEW")
        print("\nYou can also trigger a manual run with:")
        print("  cd src && python3 main.py")
        print("\n" + "="*60 + "\n")

    except Exception as e:
        logger.error(f"Reset failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    reset_baseline()
