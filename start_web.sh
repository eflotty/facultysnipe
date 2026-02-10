#!/bin/bash
# FacultySnipe Web Interface Startup Script

echo "🚀 Starting FacultySnipe Web Interface..."
echo ""
echo "The web interface will be available at:"
echo "  http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python3 app.py
