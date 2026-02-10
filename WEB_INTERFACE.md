# FacultySnipe Web Interface 🚀

## Overview
Simple, modern web interface for adding universities without touching Google Sheets!

## Features
- ✅ **Add Universities** - Just paste the URL, no Google Sheets access needed
- ✅ **View All Universities** - See all monitored universities with status
- ✅ **Run Monitor** - Trigger monitoring directly from the UI
- ✅ **Real-time Stats** - See total universities, enabled count, and success rate
- ✅ **Auto-refresh** - Updates every 30 seconds automatically
- ✅ **Modern UI** - Futuristic dark theme with smooth animations

## How to Use

### 1. Start the Web Server
```bash
python3 app.py
```

The server will start on `http://localhost:5000`

### 2. Open in Browser
Open your browser and go to:
```
http://localhost:5000
```

### 3. Add a University
1. Enter the faculty directory URL (e.g., `https://biology.stanford.edu/people/faculty`)
2. Optionally add a sales rep email for notifications
3. Click "Add University"
4. Done! The URL is now in your Google Sheet

### 4. Run the Monitor
Click the "🚀 Run Monitor Now" button to trigger the scraping process.

The bot will:
1. Auto-fill university details (ID, name, scraper class)
2. Scrape all faculty data
3. Update Google Sheets
4. Send email notifications for new faculty

## How It Works

### Behind the Scenes
```
User enters URL in browser
    ↓
Flask API adds URL to Google Sheets CONFIG tab
    ↓
Auto-fill logic fills in university_id, university_name, scraper_class
    ↓
Bot scrapes faculty data
    ↓
Updates Google Sheets + sends emails
```

### API Endpoints

#### `POST /api/add-university`
Add a new university URL to Google Sheets
```json
{
  "url": "https://biology.stanford.edu/people/faculty",
  "email": "rep@company.com"
}
```

#### `GET /api/universities`
Get list of all monitored universities
```json
{
  "success": true,
  "universities": [
    {
      "university_id": "stanford_biology",
      "university_name": "Stanford University",
      "url": "https://biology.stanford.edu/people/faculty",
      "enabled": true,
      "last_run": "2026-02-09 18:00:00",
      "last_status": "SUCCESS"
    }
  ]
}
```

#### `POST /api/run-monitor`
Trigger the monitoring script in background
```json
{
  "success": true,
  "message": "Monitoring started in background",
  "pid": 12345
}
```

## Deployment Options

### Option 1: Local (Simple)
Just run `python3 app.py` on your laptop
- Access at: `http://localhost:5000`
- Perfect for small teams on the same network

### Option 2: Heroku (Free Tier)
```bash
# Create Heroku app
heroku create facultysnipe

# Add Procfile
echo "web: python app.py" > Procfile

# Deploy
git push heroku main

# Set environment variables
heroku config:set GOOGLE_SHEETS_CREDENTIALS='...'
heroku config:set GOOGLE_SHEET_ID='...'
```

### Option 3: Railway (Free)
1. Connect GitHub repo to Railway
2. Add environment variables
3. Deploy automatically on push
4. Get free HTTPS URL

### Option 4: DigitalOcean App Platform ($5/month)
1. Connect GitHub repo
2. Add environment variables
3. Auto-deploy on push
4. Production-ready with monitoring

## Screenshots

### Add University
```
╔═══════════════════════════════════════════════╗
║         FacultySnipe                          ║
║   Automated University Faculty Monitoring     ║
╠═══════════════════════════════════════════════╣
║                                               ║
║  Add University                               ║
║  Enter a faculty directory URL to start       ║
║                                               ║
║  Faculty Directory URL                        ║
║  ┌─────────────────────────────────────────┐  ║
║  │ https://biology.stanford.edu/...        │  ║
║  └─────────────────────────────────────────┘  ║
║                                               ║
║  Sales Rep Email (Optional)                   ║
║  ┌─────────────────────────────────────────┐  ║
║  │ rep@company.com                         │  ║
║  └─────────────────────────────────────────┘  ║
║                                               ║
║  [ Add University ]                           ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

### Statistics
```
╔═══════════════════════════════════════════════╗
║  Statistics                                   ║
╠═══════════════════════════════════════════════╣
║                                               ║
║   ┌──────────┐  ┌──────────┐  ┌──────────┐  ║
║   │    12    │  │    10    │  │    8     │  ║
║   │  TOTAL   │  │ ENABLED  │  │ SUCCESS  │  ║
║   └──────────┘  └──────────┘  └──────────┘  ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

### Universities List
```
╔═══════════════════════════════════════════════╗
║  Monitored Universities                       ║
║  All universities in your configuration       ║
╠═══════════════════════════════════════════════╣
║                                               ║
║  [ 🚀 Run Monitor Now ]                       ║
║                                               ║
║  ┌─────────────────────────────────────────┐  ║
║  │ Stanford University                     │  ║
║  │ https://biology.stanford.edu/...        │  ║
║  │ [ENABLED] [SUCCESS]                     │  ║
║  └─────────────────────────────────────────┘  ║
║                                               ║
║  ┌─────────────────────────────────────────┐  ║
║  │ UFL - Biochemistry                      │  ║
║  │ https://biochem.ufl.edu/...             │  ║
║  │ [ENABLED] [SUCCESS]                     │  ║
║  └─────────────────────────────────────────┘  ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

## Benefits

### For Non-Technical Team
- ✅ No need to access Google Sheets
- ✅ No need to understand sheet structure
- ✅ Just paste URL and click
- ✅ Visual feedback on success/failure
- ✅ See all universities at a glance

### For Developers
- ✅ Clean separation of concerns
- ✅ RESTful API for integrations
- ✅ Easy to extend with new features
- ✅ Modern frontend with vanilla JS (no framework bloat)

## Security Notes

### Production Deployment
When deploying to production, you should:

1. **Add authentication** - Protect the interface with login
2. **Use HTTPS** - Encrypt all traffic
3. **Rate limiting** - Prevent abuse
4. **Environment variables** - Never commit credentials

Example with basic auth:
```python
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

users = {
    "admin": "password123"  # Change this!
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

## Troubleshooting

### Port Already in Use
```bash
# Change port in app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Can't Access from Another Computer
```bash
# Make sure you're binding to 0.0.0.0 (not localhost)
app.run(debug=True, host='0.0.0.0', port=5000)

# Then access from another computer using your IP:
# http://192.168.1.100:5000
```

### Google Sheets Permission Error
Make sure your service account has edit access to the Google Sheet.

## Next Steps

Optional enhancements:
- [ ] Add authentication (login system)
- [ ] Add ability to enable/disable universities from UI
- [ ] Add ability to delete universities
- [ ] Add real-time log streaming (see scraping progress live)
- [ ] Add scheduling (trigger runs at specific times)
- [ ] Add email notification preview
- [ ] Add dark/light theme toggle
- [ ] Add export to CSV feature

---

**Status:** ✅ READY TO USE
**Complexity:** Very Simple (just Flask + vanilla JS)
**Setup Time:** 2 minutes
