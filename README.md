# FacultySnipe - Automated University Faculty Monitoring System

![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Fully automated system to monitor 30+ university faculty pages for new additions, store data in Google Sheets, and email sales reps when new faculty are detected. Runs twice weekly via GitHub Actions at **zero cost**.

## Features

- **Automated Monitoring**: Runs twice weekly (Monday & Thursday at 3 AM UTC)
- **Zero-Code University Addition**: Just paste a URL - system auto-generates all configuration
- **Smart Universal Scraper**: Adapts to 80%+ of university pages without custom code
- **AI-Powered Fallback**: Claude API fallback for complex pages (~$0.01-0.05/scrape)
- **Change Detection**: Automatically identifies new faculty, updated profiles, and removals
- **Email Notifications**: Professional HTML emails sent to sales reps with faculty details
- **Google Sheets Integration**: Non-technical users can view/edit data and configuration
- **Automatic Retry Logic**: Handles transient failures and rate limits gracefully
- **100% Free**: Runs on GitHub Actions free tier with zero infrastructure costs (unless AI fallback needed)

## Quick Start

### Prerequisites

1. Python 3.11+
2. Google Cloud account (free)
3. Gmail account or SendGrid (free tier)
4. GitHub account

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/FacultySnipe.git
   cd FacultySnipe
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Setup Google Sheets**

   a. Create a Google Cloud Project at https://console.cloud.google.com

   b. Enable Google Sheets API

   c. Create a service account and download credentials JSON

   d. Create a new Google Sheet and share it with the service account email

   e. Create a "CONFIG" sheet with these columns:
   ```
   university_id | university_name | scraper_class | url | enabled | scraper_type | sales_rep_email | last_run | last_status | notes
   ```

4. **Configure environment variables**

   Copy `.env.example` to `.env` and fill in:
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```bash
   GOOGLE_SHEETS_CREDENTIALS='{"type": "service_account", ...}'
   GOOGLE_SHEET_ID="your-google-sheet-id"
   SMTP_HOST="smtp.gmail.com"
   SMTP_PORT="587"
   SMTP_USERNAME="your-email@gmail.com"
   SMTP_PASSWORD="your-app-password"
   SENDER_EMAIL="your-email@gmail.com"
   ```

5. **Test locally**
   ```bash
   cd src
   python main.py
   ```

### GitHub Actions Setup

1. **Add secrets** to your GitHub repository (Settings → Secrets and variables → Actions):
   - `GOOGLE_SHEETS_CREDENTIALS`
   - `GOOGLE_SHEET_ID`
   - `SMTP_HOST`
   - `SMTP_PORT`
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD`
   - `SENDER_EMAIL`

2. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial FacultySnipe setup"
   git push origin main
   ```

3. **Enable GitHub Actions** (if not already enabled)

4. **Test manual run**: Actions → Faculty Monitor → Run workflow

## Adding New Universities

### Simple Method (Recommended for 80%+ of Universities)

**No coding required!** The system automatically adapts to most university pages.

1. **Open the Google Sheet**
2. **Go to the CONFIG tab**
3. **Add a new row with ONLY the URL:**
   - Paste the faculty directory URL in the `url` column
   - Example: `https://biology.stanford.edu/people/faculty`
4. **Leave other fields EMPTY** - they will auto-populate
5. **Run the setup script OR wait for next automatic run:**
   ```bash
   python setup_sheet.py
   ```
   OR let the system auto-fill on next scheduled run

6. **The system will automatically generate:**
   - `university_id`: (e.g., `stanford_biology`)
   - `university_name`: (e.g., `Stanford - Biology`)
   - `scraper_type`: (`static` or `dynamic`)
   - `enabled`: (`TRUE`)
   - `scraper_class`: (empty = uses smart scraper)

7. **Manually fill in:**
   - `sales_rep_email`: Your email for notifications

8. **Done!** The system will automatically scrape on next run.

### Testing a New URL

Validate a URL before adding it:
```bash
python utils/validate_url.py "https://biology.stanford.edu/faculty"
```

This checks if the page is accessible and contains faculty data.

### Bulk Import (Multiple Universities)

Create a CSV file with URLs:
```csv
url,sales_rep_email,notes
https://biology.stanford.edu/faculty,rep@company.com,Stanford Bio
https://med.miami.edu/microbiology/faculty,rep@company.com,Miami Micro
```

Import:
```bash
python utils/bulk_import.py universities.csv
```

### Custom Scraper (Only if Smart Scraper Fails)

If the smart scraper doesn't work for a specific university (rare), you can create a custom scraper:

1. **Analyze the page**
   - Check if smart scraper extracted any data
   - Identify CSS selectors if needed

2. **Create custom scraper** (see `src/universities/template.py`)

3. **Update CONFIG sheet**
   - Set `scraper_class` to your custom class name
   - Set `enabled` to `TRUE`

4. **Test and deploy**

## Project Structure

```
FacultySnipe/
├── .github/workflows/
│   └── faculty_monitor.yml    # GitHub Actions workflow
├── src/
│   ├── config.py              # Configuration and logging
│   ├── google_sheets.py       # Google Sheets integration
│   ├── email_notifier.py      # Email notifications
│   ├── main.py                # Main orchestration
│   ├── scrapers/
│   │   ├── base_scraper.py    # Abstract base class
│   │   ├── static_scraper.py  # BeautifulSoup implementation
│   │   ├── dynamic_scraper.py # Playwright implementation
│   │   └── registry.py        # Dynamic scraper loading
│   └── universities/
│       ├── miami.py           # Example: Miami Microbiology
│       ├── uf_biochem.py      # Example: UF Biochem (Playwright)
│       └── template.py        # Template for new universities
├── tests/
│   ├── test_scrapers.py
│   └── test_google_sheets.py
├── requirements.txt
├── .env.example
└── README.md
```

## How It Works

### Change Detection Algorithm

1. Load existing faculty from Google Sheet (keyed by `faculty_id`)
2. Scrape current faculty from website
3. For each scraped faculty:
   - Generate `faculty_id` from hash of (name + email + title)
   - If ID not in existing data → **NEW FACULTY**
   - If ID exists but fields changed → **CHANGED FACULTY**
4. Check for IDs in existing data but not scraped → **REMOVED FACULTY**
5. Update sheet and send email notifications

### Data Flow

```
GitHub Actions Trigger
  ↓
Load CONFIG from Google Sheets
  ↓
For each enabled university:
  ├─→ Load scraper dynamically
  ├─→ Scrape faculty page
  ├─→ Detect changes (new/modified/removed)
  ├─→ Update Google Sheets
  └─→ Send email if changes detected
```

## Utility Scripts

### validate_url.py - Check if URL is Scrapable
```bash
python utils/validate_url.py "https://biology.stanford.edu/faculty"
```
Checks if a URL is accessible and contains faculty data.

### bulk_import.py - Import Multiple Universities
```bash
python utils/bulk_import.py universities.csv
```
Import multiple universities from a CSV file. See `universities_template.csv` for format.

### check_data_quality.py - Analyze Data Quality
```bash
# Check all universities
python utils/check_data_quality.py

# Check specific university
python utils/check_data_quality.py --university stanford_biology

# Show only low-quality data
python utils/check_data_quality.py --min-score 70
```
Analyzes faculty data quality and identifies issues.

### setup_sheet.py - Auto-Fill Google Sheets
```bash
python setup_sheet.py
```
Auto-fills incomplete rows in CONFIG and creates INSTRUCTIONS tab.

## Google Sheets Schema

### CONFIG Sheet
| Column | Description | Auto-Generated? |
|--------|-------------|----------------|
| university_id | Unique identifier (e.g., `stanford_biology`) | ✅ Yes |
| university_name | Display name (e.g., `Stanford - Biology`) | ✅ Yes |
| scraper_class | Python class name (leave EMPTY for smart scraper) | ✅ Yes (empty) |
| url | Faculty page URL | ❌ **Required** |
| enabled | TRUE/FALSE - whether to monitor | ✅ Yes (TRUE) |
| scraper_type | `static` or `dynamic` | ✅ Yes (auto-detected) |
| sales_rep_email | Email for notifications | ❌ Manual |
| last_run | Last execution timestamp | ✅ Yes (auto-updated) |
| last_status | SUCCESS/FAILED/SKIPPED | ✅ Yes (auto-updated) |
| notes | Optional admin notes | ✅ Yes (auto-generated) |

**To add a university:** Just fill in the `url` column - everything else auto-populates!

### Per-University Sheets
| Column | Description |
|--------|-------------|
| faculty_id | Unique hash-based ID |
| name | Full name |
| title | Position/rank |
| email | Contact email |
| profile_url | Profile page link |
| department | Department name |
| first_seen | Date first detected |
| last_verified | Last check timestamp |
| status | ACTIVE/REMOVED |
| raw_data | JSON for custom fields |

## Cost Analysis

- **30 universities** × 2 min avg = 60 min/run
- **2 runs/week** = 8 runs/month = 480 minutes/month
- **GitHub Actions free tier**: 2000 minutes/month
- **Usage**: 24% of free tier
- **Cost**: $0/month

## Testing

### Run Unit Tests
```bash
python -m pytest tests/test_scrapers.py -v
```

### Test Single University
```bash
cd src
python main.py --university miami_microbio
```

### Test Email Notifications
Set `sales_rep_email` to your personal email and run a test.

## Troubleshooting

### Scraper Returns No Faculty
1. **Check if URL is valid:**
   ```bash
   python utils/validate_url.py "your-url-here"
   ```
2. **Check logs** for specific errors
3. **Try URL in browser** - some sites block automated scraping
4. **Check scraper_type** - may need to switch from static to dynamic
5. **Contact support** if smart scraper consistently fails

### Email Notifications Not Sending
1. **Check spam folder**
2. **Verify sales_rep_email is filled in CONFIG sheet**
3. **Check SMTP credentials:**
   ```bash
   python test_email.py
   ```
4. **For Gmail:**
   - Ensure 2FA is enabled
   - Use App Password, not regular password
   - Regenerate app password if old
5. **Check GitHub Actions logs** for SMTP errors

### Google Sheets Errors
1. **Permission Denied:**
   - Share sheet with service account email (Editor access)
   - Verify service account email is correct
   - Check Google Sheets API is enabled

2. **Trailing Spaces in Headers:**
   - System now auto-cleans headers
   - Manually remove spaces if issues persist

3. **Rate Limit Exceeded:**
   - System has retry logic with backoff
   - Reduce number of enabled universities if needed

### Auto-Fill Not Working
1. **Run setup script manually:**
   ```bash
   python setup_sheet.py
   ```
2. **Check URL column has valid URLs**
3. **Verify .env is configured correctly**
4. **Check logs for specific errors**

### University Marked as FAILED
1. **Check last_status column in CONFIG**
2. **View GitHub Actions logs** for error details
3. **Test locally:**
   ```bash
   python src/main.py --university your_university_id
   ```
4. **Common causes:**
   - URL changed or moved
   - Website blocking scraper
   - Timeout (increase SCRAPER_TIMEOUT in .env)
   - CSS selectors changed (need custom scraper)

## FAQ

**Q: How often does the system run?**
A: Twice weekly - Monday and Thursday at 3 AM UTC (automatic via GitHub Actions).

**Q: Can I run it more frequently?**
A: Yes, edit `.github/workflows/faculty_monitor.yml` and change the cron schedule. Be mindful of GitHub Actions free tier limits (2000 min/month).

**Q: Do I need to write code to add a university?**
A: No! Just paste the URL in the Google Sheet. The smart scraper handles 80%+ of pages automatically.

**Q: What if the smart scraper doesn't work?**
A: The system will fall back to AI-powered scraping (costs ~$0.01-0.05 per scrape). If that fails, you can create a custom scraper.

**Q: How do I know if a new faculty member was detected?**
A: You'll receive an email notification at the address specified in `sales_rep_email`.

**Q: Can I monitor the same university with multiple sales reps?**
A: Not directly, but you can add the same URL multiple times with different university_ids and sales_rep_emails.

**Q: What data is collected?**
A: Name, title, email, profile URL, department, phone, and research interests (if available on the page).

**Q: Is there a limit to how many universities I can monitor?**
A: Practical limit is ~50-60 universities to stay within GitHub Actions free tier (2000 min/month).

**Q: Can I export the data?**
A: Yes, it's all in Google Sheets! You can download as CSV/Excel anytime.

**Q: What happens if a faculty member is removed from a page?**
A: The system detects removals but doesn't notify by default (to reduce noise). Check the status column in the university sheet.

**Q: Can I integrate with our CRM?**
A: Not built-in yet, but it's on the roadmap. You can export from Google Sheets and import to your CRM for now.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-university`)
3. Commit changes (`git commit -m 'Add scraper for New University'`)
4. Push to branch (`git push origin feature/new-university`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- Open a GitHub Issue
- Check existing issues for solutions
- Review logs in GitHub Actions artifacts

## Roadmap

- [ ] Web dashboard for viewing all universities
- [ ] Slack/Discord webhook integration
- [ ] ML-based "interesting change" detection
- [ ] CRM integration (Salesforce/HubSpot)
- [ ] Historical tracking and analytics
- [ ] Smart caching to skip unchanged pages
- [ ] Parallel scraper execution

---

Built with ❤️ for automated faculty monitoring
