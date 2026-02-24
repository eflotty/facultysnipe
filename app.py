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

# Lazy load sheets manager to avoid startup errors
_sheets = None

def get_sheets():
    global _sheets
    if _sheets is None:
        _sheets = GoogleSheetsManager()
    return _sheets


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
    """Add directory URL to Google Sheets"""
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
        sheets = get_sheets()
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
            'message': f'✅ Directory added and ENABLED! Will be scraped on next scheduled run (Mon/Thu 8 PM UTC).',
            'url': url
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/universities', methods=['GET'])
def get_universities():
    """Get list of all universities from CONFIG sheet"""
    try:
        sheets = get_sheets()
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
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in get_universities: {error_details}")
        return jsonify({'success': False, 'error': str(e), 'traceback': error_details}), 500


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
        sheets = get_sheets()
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

            # Get next scheduled run (Monday or Thursday at 8 PM UTC)
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            next_run = None

            # Find next Monday or Thursday
            days_ahead = {0: 1, 1: 3, 2: 2, 3: 1, 4: 4, 5: 3, 6: 2}  # Mon=0, Thu=3
            days_to_add = days_ahead.get(now.weekday(), 1)
            next_run = (now + timedelta(days=days_to_add)).replace(hour=20, minute=0, second=0)

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


@app.route('/api/universities/grouped', methods=['GET'])
def get_universities_grouped():
    """Get universities grouped by parent institution"""
    try:
        sheets = get_sheets()
        grouped = sheets.get_grouped_universities()
        return jsonify({
            'success': True,
            'data': grouped,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get contacts with filtering and pagination"""
    try:
        university_name = request.args.get('university_name')
        status = request.args.get('status', 'NEW')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        sheets = get_sheets()
        result = sheets.get_contacts_from_new_contacts_sheet(
            university_name=university_name,
            status=status,
            limit=limit,
            offset=offset
        )

        return jsonify({
            'success': True,
            **result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contacts/summary', methods=['GET'])
def get_contacts_summary():
    """Get contact count statistics"""
    try:
        sheets = get_sheets()
        counts = sheets.get_contact_counts_by_university()

        total_new = sum(v['new'] for v in counts.values())
        total_old = sum(v['old'] for v in counts.values())

        return jsonify({
            'success': True,
            'summary': {
                'total_contacts': total_new + total_old,
                'total_new': total_new,
                'total_old': total_old
            },
            'by_university': counts
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/debug/university-names', methods=['GET'])
def debug_university_names():
    """Debug endpoint to check university names in CONFIG vs NEW CONTACTS"""
    try:
        sheets = get_sheets()

        # Get universities from CONFIG
        universities = sheets.get_universities_config()
        config_names = [u.get('university_name', '') for u in universities]

        # Get contact counts (shows what's in NEW CONTACTS)
        counts = sheets.get_contact_counts_by_university()
        contacts_names = list(counts.keys())

        return jsonify({
            'success': True,
            'config_sheet_names': config_names,
            'new_contacts_sheet_names': contacts_names,
            'counts': counts
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contacts/search', methods=['GET'])
def search_contacts():
    """Search contacts across all universities"""
    try:
        query = request.args.get('q', '').strip()
        status = request.args.get('status', 'NEW')  # Default to NEW contacts only
        limit = int(request.args.get('limit', 100))

        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Search query must be at least 2 characters'
            }), 400

        sheets = get_sheets()

        # Get all contacts matching status
        all_contacts = sheets.get_contacts_from_new_contacts_sheet(
            status=status,
            limit=10000  # Get all to search through
        )

        # Filter contacts by search query
        query_lower = query.lower()
        matching_contacts = []

        for contact in all_contacts['contacts']:
            # Search in multiple fields
            searchable_text = ' '.join([
                contact.get('name', ''),
                contact.get('email', ''),
                contact.get('title', ''),
                contact.get('university', ''),
                contact.get('department', ''),
                contact.get('research_interests', '')
            ]).lower()

            if query_lower in searchable_text:
                matching_contacts.append(contact)

            if len(matching_contacts) >= limit:
                break

        return jsonify({
            'success': True,
            'query': query,
            'total': len(matching_contacts),
            'returned': len(matching_contacts),
            'contacts': matching_contacts
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
