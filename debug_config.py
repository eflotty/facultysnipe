#!/usr/bin/env python3
"""
Debug script to check what's being read from CONFIG sheet
"""
from dotenv import load_dotenv
import os
load_dotenv('.env')

import gspread
from google.oauth2.service_account import Credentials
import json

# Get credentials
creds_dict = json.loads(os.getenv('GOOGLE_SHEETS_CREDENTIALS'))
sheet_id = os.getenv('GOOGLE_SHEET_ID')

# Connect
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(sheet_id)

# Get CONFIG sheet
config_sheet = spreadsheet.worksheet('CONFIG')

print("=== RAW DATA ===")
all_values = config_sheet.get_all_values()
for i, row in enumerate(all_values[:5], 1):  # First 5 rows
    print(f"Row {i}: {row}")

print("\n=== RECORDS ===")
records = config_sheet.get_all_records()
print(f"Total records: {len(records)}")
for i, record in enumerate(records, 1):
    print(f"\nRecord {i}:")
    for key, value in record.items():
        print(f"  {key}: {value!r}")

print("\n=== ENABLED FILTER ===")
enabled = [
    record for record in records
    if record.get('enabled', '').upper() == 'TRUE'
]
print(f"Enabled universities: {len(enabled)}")
for uni in enabled:
    print(f"  - {uni.get('university_id')}: {uni.get('university_name')}")
