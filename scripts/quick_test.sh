#!/bin/bash
# Quick test script for FacultySnipe
# Tests a single university scraper locally

set -e

echo "======================================"
echo "FacultySnipe Quick Test"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Check if university ID provided
if [ -z "$1" ]; then
    echo "Usage: ./scripts/quick_test.sh <university_id>"
    echo ""
    echo "Example: ./scripts/quick_test.sh miami_microbio"
    exit 1
fi

UNIVERSITY_ID=$1

echo "Testing university: $UNIVERSITY_ID"
echo ""

# Load environment
export $(cat .env | grep -v '^#' | xargs)

# Run scraper
cd src
python main.py --university "$UNIVERSITY_ID"

echo ""
echo "======================================"
echo "Test completed!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Check Google Sheets for data"
echo "2. Check email for notification"
echo "3. If successful, add more universities"
echo "4. Deploy to GitHub Actions"
