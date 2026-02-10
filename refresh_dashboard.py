#!/usr/bin/env python3
"""
Refresh Dashboard - Recreate dashboard with fixed formulas
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

print("=" * 60)
print("Refreshing Dashboard...")
print("=" * 60)

sheets = GoogleSheetsManager()

# Force refresh the dashboard
sheets.create_dashboard_sheet(force_refresh=True)

print()
print("✓ Dashboard refreshed!")
print("Check your Google Sheet - formulas should now work correctly")
print("=" * 60)
