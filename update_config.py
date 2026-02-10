#!/usr/bin/env python3
"""
Update CONFIG sheet with working test URL
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
config_sheet = spreadsheet.worksheet('CONFIG')

# Update row 2 with working URL
print("Updating CONFIG with Stanford Biology test...")
config_sheet.update('B2:D2', [[
    'Stanford - Biology',
    'MiamiMicrobiologyScraper',
    'https://biology.stanford.edu/people/faculty'
]])

print("✓ Updated CONFIG sheet")
print("  University: Stanford - Biology")
print("  URL: https://biology.stanford.edu/people/faculty")
