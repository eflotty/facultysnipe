"""
FacultySnipe Web Interface
Simple Flask app for adding universities without touching Google Sheets
"""
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google_sheets import GoogleSheetsManager

app = Flask(__name__)
sheets = GoogleSheetsManager()


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check for Render"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/api/add-university', methods=['POST'])
def add_university():
    """Add university URL to Google Sheets"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        sales_rep_email = data.get('email', '').strip()

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        # Validate URL format
        if not url.startswith('http'):
            return jsonify({'success': False, 'error': 'URL must start with http:// or https://'}), 400

        # Add URL to Google Sheets CONFIG tab
        # The auto-fill logic will automatically populate university_id, university_name, etc.
        config_sheet = sheets.spreadsheet.worksheet('CONFIG')

        # Get next empty row
        all_values = config_sheet.get_all_values()
        next_row = len(all_values) + 1

        # Add URL (auto-fill will fill the rest on next run)
        config_sheet.update(f'D{next_row}', [[url]])  # Column D = URL

        # Add sales rep email if provided
        if sales_rep_email:
            config_sheet.update(f'G{next_row}', [[sales_rep_email]])  # Column G = sales_rep_email

        # Set enabled to TRUE so it's immediately ready to be scraped
        config_sheet.update(f'E{next_row}', [['TRUE']])  # Column E = enabled

        return jsonify({
            'success': True,
            'message': f'✅ University added and ENABLED! Click "Run Monitor Now" to start scraping.',
            'url': url
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/universities', methods=['GET'])
def get_universities():
    """Get list of all universities from CONFIG sheet"""
    try:
        universities = sheets.get_universities_config()

        # Format for frontend
        result = []
        for uni in universities:
            result.append({
                'university_id': uni.get('university_id'),
                'university_name': uni.get('university_name'),
                'url': uni.get('url'),
                'enabled': uni.get('enabled'),
                'last_run': uni.get('last_run'),
                'last_status': uni.get('last_status'),
                'sales_rep_email': uni.get('sales_rep_email')
            })

        return jsonify({'success': True, 'universities': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/run-monitor', methods=['POST'])
def run_monitor():
    """Trigger the monitoring script"""
    try:
        import subprocess

        # Run in background
        process = subprocess.Popen(
            ['python3', 'src/main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(__file__)
        )

        return jsonify({
            'success': True,
            'message': 'Monitoring started in background',
            'pid': process.pid
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/system-status', methods=['GET'])
def get_system_status():
    """Get recent run history from SYSTEM_STATUS tab"""
    try:
        # Get SYSTEM_STATUS sheet
        try:
            status_sheet = sheets.spreadsheet.worksheet('SYSTEM_STATUS')
            records = status_sheet.get_all_records()

            # Get last 5 runs
            recent_runs = records[-5:] if len(records) > 5 else records

            # Calculate statistics
            total_runs = len(records)
            successful_runs = sum(1 for r in records if r.get('status') == 'SUCCESS')
            success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0

            # Get next scheduled run (Monday or Thursday at 3 AM UTC)
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            next_run = None

            # Find next Monday or Thursday
            days_ahead = {0: 1, 1: 3, 2: 2, 3: 1, 4: 4, 5: 3, 6: 2}  # Mon=0, Thu=3
            days_to_add = days_ahead.get(now.weekday(), 1)
            next_run = (now + timedelta(days=days_to_add)).replace(hour=3, minute=0, second=0)

            return jsonify({
                'success': True,
                'recent_runs': recent_runs,
                'stats': {
                    'total_runs': total_runs,
                    'successful_runs': successful_runs,
                    'success_rate': round(success_rate, 1),
                    'next_run': next_run.isoformat() if next_run else None
                }
            })

        except Exception as e:
            # SYSTEM_STATUS sheet doesn't exist yet
            return jsonify({
                'success': True,
                'recent_runs': [],
                'stats': {
                    'total_runs': 0,
                    'successful_runs': 0,
                    'success_rate': 0,
                    'next_run': None
                },
                'message': 'System status tracking will be available after first automated run'
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
