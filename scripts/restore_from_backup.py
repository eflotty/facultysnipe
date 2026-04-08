#!/usr/bin/env python3
"""
Restore NEW CONTACTS from backup sheet
The baseline reset lost 1,245 contacts. This script restores them.

Usage:
    python3 scripts/restore_from_backup.py --force
"""

from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets import GoogleSheetsManager
from config import setup_logging

def restore_contacts():
    """Restore contacts from backup"""
    logger = setup_logging('RestoreContacts')

    print("\n" + "="*60)
    print("⚠️  RESTORING CONTACTS FROM BACKUP")
    print("="*60)
    print("\nThis will:")
    print("  1. Get all contacts from NEW CONTACTS BACKUP")
    print("  2. Merge with current NEW CONTACTS (deduplicate)")
    print("  3. Ensure all are marked as OLD (baseline)")
    print("\n" + "="*60)

    try:
        sheets = GoogleSheetsManager()

        # Get backup sheet
        logger.info("Step 1: Reading backup sheet...")
        backup_sheet = sheets.spreadsheet.worksheet('NEW CONTACTS BACKUP 20260406_195414')
        backup_data = backup_sheet.get_all_values()

        if len(backup_data) < 2:
            print("❌ Backup sheet is empty!")
            return

        headers = backup_data[0]
        backup_contacts = backup_data[1:]

        logger.info(f"Found {len(backup_contacts)} contacts in backup")

        # Get current NEW CONTACTS
        logger.info("Step 2: Reading current NEW CONTACTS...")
        current_sheet = sheets.spreadsheet.worksheet('NEW CONTACTS')
        current_data = current_sheet.get_all_values()

        current_contacts = current_data[1:] if len(current_data) > 1 else []
        logger.info(f"Found {len(current_contacts)} contacts in current sheet")

        # Build set of existing faculty IDs
        faculty_id_idx = headers.index('Faculty ID')
        status_idx = headers.index('Status')

        existing_ids = set()
        for row in current_contacts:
            if len(row) > faculty_id_idx and row[faculty_id_idx].strip():
                existing_ids.add(row[faculty_id_idx].strip())

        logger.info(f"Current sheet has {len(existing_ids)} unique faculty IDs")

        # Find contacts in backup that are NOT in current
        missing_contacts = []
        for row in backup_contacts:
            if len(row) > faculty_id_idx:
                fid = row[faculty_id_idx].strip()
                if fid and fid not in existing_ids:
                    # Ensure status is OLD
                    if len(row) > status_idx:
                        row[status_idx] = 'OLD'
                    missing_contacts.append(row)

        logger.info(f"Found {len(missing_contacts)} contacts to restore")

        if missing_contacts:
            print(f"\n📥 Restoring {len(missing_contacts)} missing contacts...")

            # Append missing contacts to current sheet
            current_sheet.append_rows(missing_contacts)

            logger.info(f"✅ Restored {len(missing_contacts)} contacts")
            print(f"✅ Successfully restored {len(missing_contacts)} contacts")
        else:
            print("ℹ️  No missing contacts to restore - all backup contacts already in NEW CONTACTS")

        # Verify final count
        final_data = current_sheet.get_all_values()
        final_count = len(final_data) - 1

        print("\n" + "="*60)
        print("✅ RESTORATION COMPLETE")
        print("="*60)
        print(f"\nBefore: {len(current_contacts)} contacts")
        print(f"Restored: {len(missing_contacts)} contacts")
        print(f"After: {final_count} contacts")
        print("\n" + "="*60 + "\n")

    except Exception as e:
        logger.error(f"Restoration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    restore_contacts()
