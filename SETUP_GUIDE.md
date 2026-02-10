# Detailed Setup Guide for FacultySnipe

This guide walks you through setting up FacultySnipe from scratch.

## Table of Contents
1. [Google Cloud Setup](#google-cloud-setup)
2. [Google Sheets Setup](#google-sheets-setup)
3. [Email Configuration](#email-configuration)
4. [Local Testing](#local-testing)
5. [GitHub Actions Deployment](#github-actions-deployment)
6. [Adding Your First University](#adding-your-first-university)

---

## 1. Google Cloud Setup

### Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a Project" → "New Project"
3. Name it "FacultySnipe" (or your preferred name)
4. Click "Create"

### Enable Google Sheets API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click on it and click "Enable"

### Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in:
   - Service account name: `facultysnipe-bot`
   - Service account ID: (auto-filled)
   - Description: "FacultySnipe automation bot"
4. Click "Create and Continue"
5. Skip "Grant this service account access" (click Continue)
6. Skip "Grant users access" (click Done)

### Download Credentials

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON" format
5. Click "Create" - a JSON file will download
6. **IMPORTANT**: Keep this file secure - it's your authentication credential

The JSON file looks like this:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "facultysnipe-bot@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
```

---

## 2. Google Sheets Setup

### Create the Master Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new blank spreadsheet
3. Name it "FacultySnipe Master"
4. Note the Sheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit
   ```

### Share with Service Account

1. Click "Share" button (top right)
2. Paste the service account email (from credentials JSON):
   ```
   facultysnipe-bot@your-project.iam.gserviceaccount.com
   ```
3. Give it "Editor" access
4. Uncheck "Notify people"
5. Click "Share"

### Create CONFIG Sheet

1. Rename "Sheet1" to "CONFIG"
2. Add headers in row 1 (A1:J1):
   ```
   university_id | university_name | scraper_class | url | enabled | scraper_type | sales_rep_email | last_run | last_status | notes
   ```

3. Format the sheet:
   - Make header row bold
   - Add freeze (View → Freeze → 1 row)
   - Add filters (Data → Create a filter)

### Example CONFIG Data

Add a test row to verify setup:

| university_id | university_name | scraper_class | url | enabled | scraper_type | sales_rep_email | last_run | last_status | notes |
|---------------|-----------------|---------------|-----|---------|--------------|-----------------|----------|-------------|-------|
| miami_microbio | Miami - Microbiology | MiamiMicrobiologyScraper | https://med.miami.edu/departments/microbiology-and-immunology/faculty-and-staff | TRUE | static | your-email@gmail.com | | | Test university |

---

## 3. Email Configuration

### Option A: Gmail (Recommended for Testing)

1. **Enable 2-Factor Authentication**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable "2-Step Verification"

2. **Create App Password**
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Other (Custom name)"
   - Name it "FacultySnipe"
   - Click "Generate"
   - Copy the 16-character password (remove spaces)

3. **Your Settings**
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   SENDER_EMAIL=your-email@gmail.com
   ```

### Option B: SendGrid (Recommended for Production)

1. Sign up at [SendGrid](https://sendgrid.com) (free tier: 100 emails/day)
2. Create API key (Settings → API Keys)
3. Your settings:
   ```
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USERNAME=apikey
   SMTP_PASSWORD=your-sendgrid-api-key
   SENDER_EMAIL=verified-sender@yourdomain.com
   ```

---

## 4. Local Testing

### Install Dependencies

```bash
cd FacultySnipe
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual credentials:
   ```bash
   # Paste entire JSON content as single line (or use heredoc)
   GOOGLE_SHEETS_CREDENTIALS='{"type": "service_account", "project_id": "..."}'

   # From Google Sheets URL
   GOOGLE_SHEET_ID="your-sheet-id-from-url"

   # From email setup above
   SMTP_HOST="smtp.gmail.com"
   SMTP_PORT="587"
   SMTP_USERNAME="your-email@gmail.com"
   SMTP_PASSWORD="your-app-password"
   SENDER_EMAIL="your-email@gmail.com"
   ```

### Test Connection

```bash
cd src
python -c "from google_sheets import GoogleSheetsManager; mgr = GoogleSheetsManager(); print('✓ Connected:', mgr.spreadsheet.title)"
```

Expected output:
```
✓ Connected: FacultySnipe Master
```

### Run First Test

```bash
python main.py
```

Expected behavior:
- Loads CONFIG sheet
- Processes enabled universities
- Updates Google Sheets
- Sends email if changes detected

---

## 5. GitHub Actions Deployment

### Add Repository Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret" for each:

**GOOGLE_SHEETS_CREDENTIALS**
- Name: `GOOGLE_SHEETS_CREDENTIALS`
- Value: Paste entire JSON from credentials file (as single line)

**GOOGLE_SHEET_ID**
- Name: `GOOGLE_SHEET_ID`
- Value: Your sheet ID from URL

**SMTP Settings** (repeat for each)
- `SMTP_HOST`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SMTP_USERNAME`: Your email
- `SMTP_PASSWORD`: Your app password
- `SENDER_EMAIL`: Your email

### Test Manual Run

1. Go to Actions tab
2. Select "Faculty Monitor" workflow
3. Click "Run workflow"
4. Select branch (main)
5. Click "Run workflow"

### View Results

1. Click on the running workflow
2. Click "monitor" job
3. View real-time logs
4. Check for errors
5. Download artifacts (logs) if needed

### Verify Success

- Check Google Sheets for updated data
- Check email inbox for notifications
- Review workflow logs for errors

---

## 6. Adding Your First University

### Research the Target Page

1. **Visit the faculty page**
   - Example: https://med.miami.edu/departments/microbiology-and-immunology/faculty-and-staff

2. **Inspect the HTML**
   - Right-click → "View Page Source"
   - Is it static HTML or JavaScript-rendered?
   - Static: You can see faculty names in source
   - Dynamic: Source shows `<div id="root"></div>` or similar

3. **Identify CSS Selectors**
   - Right-click on a faculty member → "Inspect"
   - Note the CSS classes/selectors:
     - Faculty card container: `.faculty-card`, `.person`, etc.
     - Name: `.name`, `h2`, `.person-name`
     - Title: `.title`, `.position`, `.rank`
     - Email: `a[href^="mailto:"]`
     - Profile link: `a.profile-link`

### Create the Scraper

1. **Copy template**
   ```bash
   cp src/universities/template.py src/universities/miami.py
   ```

2. **Edit the scraper**
   ```python
   from scrapers.static_scraper import StaticScraper, Faculty

   class MiamiMicrobiologyScraper(StaticScraper):
       def parse(self, soup):
           faculty_list = []

           # Use your identified selectors
           for card in soup.select('.faculty-card'):
               faculty_list.append(Faculty(
                   name=card.select_one('.name').text.strip(),
                   title=card.select_one('.title').text.strip(),
                   email=self._extract_email(card),
                   profile_url=card.select_one('a')['href'],
                   department="Microbiology and Immunology"
               ))

           return faculty_list
   ```

3. **Test locally**
   ```bash
   cd src
   python main.py --university miami_microbio
   ```

### Add to CONFIG Sheet

1. Open Google Sheets
2. Add row to CONFIG:
   - university_id: `miami_microbio`
   - university_name: `Miami - Microbiology`
   - scraper_class: `MiamiMicrobiologyScraper`
   - url: `https://med.miami.edu/...`
   - enabled: `TRUE`
   - scraper_type: `static`
   - sales_rep_email: `your-email@gmail.com`

### Deploy

```bash
git add src/universities/miami.py
git commit -m "Add Miami Microbiology scraper"
git push origin main
```

### Verify

1. Check GitHub Actions runs successfully
2. Check Google Sheets for new "miami_microbio" sheet
3. Check email for notification
4. Review faculty data quality

---

## Common Issues

### "Permission denied" on Google Sheets
- Verify service account has Editor access
- Check credentials JSON is valid
- Ensure Google Sheets API is enabled

### "Authentication failed" for email
- Double-check app password (no spaces)
- Verify 2FA is enabled for Gmail
- Try regenerating app password

### "No faculty found"
- Check URL is accessible
- Verify CSS selectors are correct
- Check page source vs. rendered HTML
- Try Playwright (dynamic) if BeautifulSoup fails

### GitHub Actions timeout
- Check if site is blocking automated requests
- Reduce number of universities per run
- Increase timeout in workflow YAML

---

## Next Steps

- Add more universities (30+ recommended)
- Set up monitoring for failed runs
- Customize email templates
- Add Slack/Discord webhooks
- Build analytics dashboard

**Congratulations!** Your FacultySnipe system is now operational.
