#!/usr/bin/env python3
"""
One-time migration: Set first_scrape_completed=TRUE for all existing universities
This ensures they're not treated as "first scrape" after the update.

Run after deploying the first_scrape_completed column update:
    python3 scripts/migrate_first_scrape_flag.py
"""

from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets import GoogleSheetsManager
from config import setup_logging

def migrate():
    """Migrate all existing universities to first_scrape_completed=TRUE"""
    logger = setup_logging('Migration')
    logger.info("Starting migration: marking existing universities as first_scrape_completed=TRUE")

    try:
        sheets = GoogleSheetsManager()
        config_sheet = sheets.spreadsheet.worksheet('CONFIG')

        # Get all values
        all_values = config_sheet.get_all_values()

        if not all_values or len(all_values) < 2:
            logger.info("No universities to migrate")
            return

        headers = all_values[0]

        # Find column index for first_scrape_completed
        if 'first_scrape_completed' not in headers:
            logger.error("ERROR: first_scrape_completed column not found!")
            logger.error("Please run the schema update first (restart the app to trigger CONFIG sheet update)")
            return

        fsc_col_idx = headers.index('first_scrape_completed')
        col_letter = chr(ord('A') + fsc_col_idx)

        # Update all non-header rows to TRUE
        updates = []
        for row_idx in range(2, len(all_values) + 1):
            updates.append({
                'range': f'{col_letter}{row_idx}',
                'values': [['TRUE']]
            })

        if updates:
            config_sheet.batch_update(updates)
            logger.info(f"✅ Migrated {len(updates)} universities - marked as first_scrape_completed=TRUE")
            logger.info("Migration complete!")
        else:
            logger.info("No universities to migrate (only header row exists)")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    migrate()
