#!/usr/bin/env python3
"""
Migration script: Fix university names in NEW CONTACTS to match CONFIG

PROBLEM:
- NEW CONTACTS has enhanced names: "Miami University - Cell Biology"
- CONFIG has base names: "Miami University"
- This mismatch breaks UI grouping (918 orphaned contacts - 37% of database)

SOLUTION:
- Find all NEW CONTACTS entries with enhanced names
- Match them to their CONFIG entries
- Update NEW CONTACTS to use CONFIG names exactly
- Preserve department info in the Department column

This fixes Browse Contacts grouping immediately.
"""

from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets import GoogleSheetsManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_university_names():
    """Update NEW CONTACTS university names to match CONFIG"""
    sheets = GoogleSheetsManager()

    logger.info("=" * 80)
    logger.info("FIXING UNIVERSITY NAMES IN NEW CONTACTS")
    logger.info("=" * 80)

    # 1. Get CONFIG university names
    logger.info("\n1. Loading CONFIG sheet...")
    config_sheet = sheets.spreadsheet.worksheet('CONFIG')
    config_data = config_sheet.get_all_values()
    config_headers = config_data[0]
    config_rows = config_data[1:]

    # Build mapping: enhanced name -> base name
    # e.g., "Miami University - Cell Biology" -> "Miami University"
    name_mapping = {}

    for row in config_rows:
        if len(row) > 1:
            base_name = row[1].strip()  # university_name from CONFIG
            if base_name:
                # This base name is the correct one
                # Any enhanced versions should map to it
                name_mapping[base_name] = base_name

    logger.info(f"Found {len(name_mapping)} universities in CONFIG")

    # 2. Get NEW CONTACTS and find enhanced names
    logger.info("\n2. Loading NEW CONTACTS sheet...")
    new_contacts_sheet = sheets.spreadsheet.worksheet('NEW CONTACTS')
    all_contacts = new_contacts_sheet.get_all_values()
    headers = all_contacts[0]
    data_rows = all_contacts[1:]

    logger.info(f"Found {len(data_rows)} contacts in NEW CONTACTS")

    # 3. Build enhanced name -> base name mapping
    logger.info("\n3. Analyzing university names...")

    # Strategy: Enhanced names are CONFIG names + " - {department}"
    # e.g., "Miami University - Cell Biology" where "Miami University" is in CONFIG
    # We need to strip the " - {department}" suffix to get back to CONFIG name

    enhanced_names = set()
    contact_university_names = set()

    # Collect all unique university names from NEW CONTACTS
    for row in data_rows:
        if len(row) > 1 and row[1].strip():
            contact_university_names.add(row[1].strip())

    # Build a list of CONFIG names for matching
    config_names_list = list(name_mapping.keys())

    # For each contact university name, try to find its CONFIG match
    for contact_name in contact_university_names:
        if ' - ' in contact_name:
            # Try to find a CONFIG name that this enhanced name is based on
            # Method 1: Check if removing everything after last " - " gives us a CONFIG name
            parts = contact_name.rsplit(' - ', 1)  # Split from right
            potential_base = parts[0].strip()

            # Check if potential_base is a CONFIG name
            if potential_base in config_names_list:
                name_mapping[contact_name] = potential_base
                enhanced_names.add(contact_name)
                continue

            # Method 2: Check if any CONFIG name is a prefix of this name
            for config_name in config_names_list:
                if contact_name.startswith(config_name + ' - '):
                    name_mapping[contact_name] = config_name
                    enhanced_names.add(contact_name)
                    break

    logger.info(f"Found {len(enhanced_names)} enhanced university names to fix:")
    for enhanced in sorted(enhanced_names):
        if enhanced in name_mapping and name_mapping[enhanced] != enhanced:
            logger.info(f"  '{enhanced}' -> '{name_mapping[enhanced]}'")

    # 4. Update NEW CONTACTS
    logger.info("\n4. Updating NEW CONTACTS sheet...")

    updates = []
    rows_updated = 0

    for idx, row in enumerate(data_rows, start=2):  # Start at row 2 (after header)
        if len(row) > 1:
            current_name = row[1].strip()
            if current_name in name_mapping and name_mapping[current_name] != current_name:
                # This name needs to be updated
                new_name = name_mapping[current_name]
                updates.append({
                    'range': f'B{idx}',  # Column B = University
                    'values': [[new_name]]
                })
                rows_updated += 1

                if rows_updated % 100 == 0:
                    logger.info(f"  Prepared {rows_updated} updates...")

    if updates:
        logger.info(f"\n5. Writing {len(updates)} updates to Google Sheets...")

        # Batch update in chunks of 1000
        chunk_size = 1000
        for i in range(0, len(updates), chunk_size):
            chunk = updates[i:i+chunk_size]
            new_contacts_sheet.batch_update(chunk)
            logger.info(f"  Updated rows {i+1} to {min(i+chunk_size, len(updates))}")

        logger.info(f"\n✅ SUCCESS! Updated {rows_updated} contacts")
        logger.info(f"All university names now match CONFIG exactly")
    else:
        logger.info("\n✅ No updates needed - all names already match CONFIG")

    # 6. Verification
    logger.info("\n6. Verifying changes...")
    all_contacts = new_contacts_sheet.get_all_values()
    data_rows = all_contacts[1:]

    remaining_enhanced = 0
    for row in data_rows:
        if len(row) > 1:
            uni_name = row[1].strip()
            if ' - ' in uni_name:
                # Check if this enhanced name exists in CONFIG
                if uni_name not in name_mapping or name_mapping.get(uni_name) != uni_name:
                    remaining_enhanced += 1

    logger.info(f"Remaining enhanced names not in CONFIG: {remaining_enhanced}")

    if remaining_enhanced > 0:
        logger.warning("⚠️  Some enhanced names remain - check CONFIG for missing entries")
    else:
        logger.info("✅ All university names verified!")

    logger.info("\n" + "=" * 80)
    logger.info("MIGRATION COMPLETE")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("1. Check Browse Contacts in UI - grouping should work correctly now")
    logger.info("2. Future scrapes will use CONFIG names without enhancement")
    logger.info("3. No more orphaned contacts!")

if __name__ == '__main__':
    try:
        fix_university_names()
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
