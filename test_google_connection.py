#!/usr/bin/env python3
"""
Quick test script to verify Google Sheets connection
Run this to make sure everything is set up correctly
"""
import json
import sys

print("=" * 60)
print("FacultySnipe - Google Sheets Connection Test")
print("=" * 60)
print()

# Step 1: Get credentials file path
print("Step 1: Load credentials")
creds_file = input("Enter path to your credentials JSON file: ").strip()

try:
    with open(creds_file, 'r') as f:
        creds_dict = json.load(f)
    print("✓ Credentials file loaded successfully")
    print(f"  Service account: {creds_dict.get('client_email')}")
except Exception as e:
    print(f"✗ Failed to load credentials: {e}")
    sys.exit(1)

print()

# Step 2: Get Sheet ID
print("Step 2: Get Sheet ID")
sheet_id = input("Enter your Google Sheet ID: ").strip()
print(f"✓ Sheet ID: {sheet_id}")
print()

# Step 3: Test connection
print("Step 3: Test connection to Google Sheets")
print("Installing gspread if needed...")

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gspread", "google-auth"])
    import gspread
    from google.oauth2.service_account import Credentials

print("Connecting to Google Sheets...")

try:
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    # Open the spreadsheet
    spreadsheet = client.open_by_key(sheet_id)

    print("✓ Successfully connected!")
    print(f"  Spreadsheet title: {spreadsheet.title}")
    print(f"  Sheets in spreadsheet:")

    for i, worksheet in enumerate(spreadsheet.worksheets(), 1):
        print(f"    {i}. {worksheet.title}")

    # Try to read CONFIG sheet
    try:
        config_sheet = spreadsheet.worksheet('CONFIG')
        print()
        print("✓ CONFIG sheet found!")

        # Get headers
        headers = config_sheet.row_values(1)
        if headers:
            print(f"  Headers: {', '.join(headers[:3])}...")

        # Count rows
        all_values = config_sheet.get_all_values()
        print(f"  Total rows: {len(all_values)}")

    except gspread.WorksheetNotFound:
        print()
        print("⚠ CONFIG sheet not found")
        print("  Please create a sheet named 'CONFIG' (all caps)")

    print()
    print("=" * 60)
    print("✓ CONNECTION TEST SUCCESSFUL!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Copy the credentials JSON content for your .env file")
    print("2. Copy the Sheet ID for your .env file")
    print("3. Make sure CONFIG sheet has the correct headers")
    print()
    print("Save these for your .env file:")
    print(f"GOOGLE_SHEET_ID=\"{sheet_id}\"")
    print(f"GOOGLE_SHEETS_CREDENTIALS='{json.dumps(creds_dict)}'")

except Exception as e:
    print(f"✗ Connection failed: {e}")
    print()
    print("Common issues:")
    print("- Make sure you shared the sheet with the service account email")
    print("- Check that the Sheet ID is correct")
    print("- Verify the credentials file is valid JSON")
    sys.exit(1)
