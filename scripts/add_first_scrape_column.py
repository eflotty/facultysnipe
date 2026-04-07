#!/usr/bin/env python3
"""
Add first_scrape_completed column to existing CONFIG sheet
Run this ONCE before running the migration script.

Usage:
    python3 scripts/add_first_scrape_column.py
"""

from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets import GoogleSheetsManager
from config import setup_logging

def add_column():
    """Add first_scrape_completed column to CONFIG sheet"""
    logger = setup_logging('AddColumn')
    logger.info("Adding first_scrape_completed column to CONFIG sheet")

    try:
        sheets = GoogleSheetsManager()
        config_sheet = sheets.spreadsheet.worksheet('CONFIG')

        # Get current headers
        headers = config_sheet.row_values(1)
        logger.info(f"Current headers: {headers}")

        # Check if column already exists
        if 'first_scrape_completed' in headers:
            logger.info("✅ Column already exists! No changes needed.")
            return

        # Find scraper_type column index
        if 'scraper_type' not in headers:
            logger.error("ERROR: scraper_type column not found! Cannot determine insert position.")
            return

        scraper_type_idx = headers.index('scraper_type')
        insert_col_idx = scraper_type_idx + 2  # +1 for next column, +1 for 1-based indexing

        logger.info(f"Inserting column at position {insert_col_idx} (after scraper_type)")

        # Insert column
        config_sheet.insert_cols([[]], col=insert_col_idx)

        # Update header
        col_letter = chr(ord('A') + insert_col_idx - 1)
        config_sheet.update(f'{col_letter}1', [['first_scrape_completed']])

        logger.info(f"✅ Successfully added first_scrape_completed column at position {col_letter}")
        logger.info("You can now run the migration script: python3 scripts/migrate_first_scrape_flag.py")

    except Exception as e:
        logger.error(f"Failed to add column: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    add_column()
