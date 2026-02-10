#!/usr/bin/env python3
"""
Setup Google Sheets with auto-fill and instructions
Run this after adding new URLs to auto-populate fields
"""
from dotenv import load_dotenv
import os
import sys

# Load environment
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google_sheets import GoogleSheetsManager
from config import validate_environment


def main():
    """Setup and auto-fill Google Sheet"""
    print("=" * 60)
    print("FacultySnipe - Sheet Setup Utility")
    print("=" * 60)
    print()

    # Validate environment
    try:
        validate_environment()
    except ValueError as e:
        print(f"ERROR: {e}")
        print("\nPlease ensure .env file is configured correctly.")
        sys.exit(1)

    # Initialize sheets manager
    print("Connecting to Google Sheets...")
    try:
        sheets = GoogleSheetsManager()
    except Exception as e:
        print(f"ERROR: Failed to connect to Google Sheets: {e}")
        sys.exit(1)

    print("✓ Connected successfully")
    print()

    # Create instructions tab
    print("Creating/updating INSTRUCTIONS tab...")
    sheets.create_instructions_tab()
    print()

    # Create dashboard
    print("Creating/updating DASHBOARD tab...")
    sheets.create_dashboard_sheet()
    print()

    # Auto-fill incomplete rows
    print("Auto-filling incomplete rows in CONFIG...")
    filled_count = sheets.auto_fill_config_rows()

    if filled_count > 0:
        print(f"✓ Auto-filled {filled_count} rows")
    else:
        print("✓ All rows are complete (or no URLs to process)")

    print()
    print("=" * 60)
    print("Setup complete!")
    print()
    print("Sheets created/updated:")
    print("  ✓ CONFIG - University configuration")
    print("  ✓ INSTRUCTIONS - User guide")
    print("  ✓ DASHBOARD - Quick stats and recent activity")
    print("  ✓ NEW CONTACTS - Aggregated new faculty across all universities")
    print()
    print("Next steps:")
    print("1. Open your Google Sheet")
    print("2. Check the INSTRUCTIONS tab for guidance")
    print("3. Review auto-filled CONFIG rows")
    print("4. Add sales_rep_email for notifications")
    print("5. Run: python src/main.py")
    print()
    print("After running, check NEW CONTACTS tab for all new faculty!")
    print("=" * 60)


if __name__ == '__main__':
    main()
