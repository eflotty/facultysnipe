# FacultySnipe System Architecture

## Overview

**FacultySnipe** is an automated faculty directory monitoring system that:
- Scrapes university faculty directories
- Detects new faculty additions
- Sends email notifications to sales reps
- Provides a web UI for browsing and searching contacts

---

## 🏗️ System Components

### 1. Backend (Python/Flask)

**Main Files:**
- `app.py` - Flask web server with REST API
- `src/main.py` - Orchestration engine for scraping
- `src/google_sheets.py` - Google Sheets integration
- `src/email_notifier.py` - Email notification system
- `src/scrapers/` - Scraping engines (Universal, Dynamic, AI)

### 2. Database (Google Sheets)

**Spreadsheet Name:** FacultySnipe Master

**Worksheets:**
1. **CONFIG** - University directory configurations
2. **NEW CONTACTS** - Centralized contact database
3. **SYSTEM_STATUS** - Run history and statistics
4. **DASHBOARD** - User dashboard data
5. **INSTRUCTIONS** - User guide
6. **OLD UNIVERSITY TABS** - Historical per-university sheets (deprecated)

### 3. Frontend (HTML/CSS/JavaScript)

**Template:** `templates/index.html`

**Tabs:**
1. **Dashboard** - System status, statistics, add new directories
2. **Browse Contacts** - Hierarchical browsing (Universities → Directories → Contacts)
3. **Most Recent New** - Latest NEW contacts across all directories

### 4. Scheduled Automation

**GitHub Actions:** `.github/workflows/scheduled_scrape.yml`
- Runs: Monday & Thursday at 8 PM UTC
- Triggers: `python3 src/main.py`
- Environment: Render deployment

---

## 📊 Google Sheets Structure

### CONFIG Sheet

**Purpose:** Master configuration for all university directories

**Columns:**
1. `university_id` - Unique identifier (e.g., `miami_biochemistry`)
2. `university_name` - Display name (e.g., `Miami University`)
3. `scraper_class` - Scraper to use (auto-filled)
4. `url` - Faculty directory URL
5. `enabled` - TRUE/FALSE to enable/disable scraping
6. `scraper_type` - Type: universal/dynamic/ai (auto-filled)
7. `first_scrape_completed` - TRUE after baseline established
8. `sales_rep_email` - Email for notifications
9. `last_run` - Last scrape timestamp
10. `last_status` - SUCCESS/FAILURE
11. `notes` - Admin notes

**Example Row:**
```
university_id: miami_biochemistry
university_name: Miami University
scraper_class: SmartUniversalScraper
url: https://med.miami.edu/departments/biochemistry-and-molecular-biology/about-us/faculty
enabled: TRUE
scraper_type: universal
first_scrape_completed: TRUE
sales_rep_email: sales@company.com
last_run: 2026-04-06 19:55:00
last_status: SUCCESS
notes:
```

### NEW CONTACTS Sheet

**Purpose:** Centralized database of all faculty contacts

**Columns:**
1. `Date Added` - Timestamp when discovered (YYYY-MM-DD HH:MM:SS)
2. `University` - Enhanced name (e.g., `Miami University - Biochemistry And Molecular Biology`)
3. `Name` - Faculty member name
4. `Title` - Academic title (Professor, Associate Professor, etc.)
5. `Email` - Contact email
6. `Profile URL` - Link to faculty profile page
7. `Department` - Department name
8. `Phone` - Phone number
9. `Research Interests` - Research areas
10. `Faculty ID` - Unique hash (for deduplication)
11. `Status` - NEW or OLD
12. `Notes` - Notes for sales rep

**Status Logic:**
- **NEW:** Newly discovered faculty (will show in notifications)
- **OLD:** Baseline contacts or previously seen (background data)

**Example Row:**
```
Date Added: 2026-04-06 19:55:29
University: Miami University - Biochemistry And Molecular Biology
Name: Sylvia Daunert, Pharm.D., M.S.
Title: Professor
Email: sdaunert@miami.edu
Profile URL: https://med.miami.edu/faculty/sylvia-daunert
Department:
Phone: 305-284-3781
Research Interests:
Faculty ID: a3f5b9c2d1e8f7a6
Status: OLD
Notes:
```

### SYSTEM_STATUS Sheet

**Purpose:** Track scraping run history and performance

**Columns:**
1. `timestamp` - Run start time
2. `status` - SUCCESS/FAILURE
3. `universities_processed` - Number of directories scraped
4. `new_faculty` - Count of NEW faculty discovered
5. `changed_faculty` - Count of updated faculty
6. `execution_time` - Runtime in seconds
7. `errors` - Error messages (if any)
8. `github_url` - Link to GitHub Actions run

---

## 🔄 Data Flow

### 1. Adding a New Directory

**User Action:**
1. User opens Dashboard tab
2. Enters faculty directory URL
3. Optionally adds sales rep email
4. Clicks "Add Directory"

**Backend Process:**
```
POST /api/add-university
  ↓
app.py: add_university()
  ↓
Write to CONFIG sheet:
  - Column D (url)
  - Column E (enabled = TRUE)
  - Column G (sales_rep_email)
  ↓
Auto-fill runs on next scrape:
  - Extracts university_id
  - Extracts university_name
  - Determines scraper_class
  - Sets first_scrape_completed = FALSE
```

### 2. First Scrape (Baseline Establishment)

**Trigger:** Monday/Thursday 8 PM UTC (or manual run)

**Process:**
```
GitHub Actions: scheduled_scrape.yml
  ↓
python3 src/main.py
  ↓
main.py: FacultyMonitor.run()
  ↓
For each university in CONFIG:
  ↓
  Check: is_first_scrape(university_id)?
  ↓
  if TRUE (first scrape):
    ↓
    Scrape faculty directory
    ↓
    Add ALL contacts to NEW CONTACTS with Status=OLD
    ↓
    mark_first_scrape_complete(university_id)
    ↓
    No email notification sent (baseline)
```

**Result:**
- All existing faculty marked as OLD (baseline)
- `first_scrape_completed` = TRUE in CONFIG
- Future scrapes will detect NEW hires

### 3. Subsequent Scrapes (Change Detection)

**Process:**
```
python3 src/main.py
  ↓
For each university in CONFIG:
  ↓
  Check: is_first_scrape(university_id)?
  ↓
  if FALSE (baseline already established):
    ↓
    Scrape faculty directory
    ↓
    Load existing faculty IDs from NEW CONTACTS
    ↓
    Compare: new_faculty_ids vs existing_ids
    ↓
    Find NEW faculty (not in existing_ids)
    ↓
    Add NEW faculty to NEW CONTACTS with Status=NEW
    ↓
    Send email notification to sales_rep_email
```

**Change Detection:**
```python
# Load existing faculty
existing_ids = {row[9] for row in NEW CONTACTS if row[9].strip()}

# Generate faculty_id from scraped data
faculty_id = hash(name + email + title)

# Check if new
if faculty_id not in existing_ids:
    # This is a NEW hire!
    add_to_new_contacts(faculty, status='NEW')
    send_email_notification(sales_rep_email)
```

### 4. Browsing Contacts (UI)

**User Flow:**
```
User clicks "Browse Contacts" tab
  ↓
GET /api/universities/grouped
  ↓
google_sheets.py: get_grouped_universities()
  ↓
Groups universities by domain:
  - "University of Miami" (20 directories)
  - "University of Florida" (16 directories)
  - "Stanford" (1 directory)
  ↓
For each directory, get contact counts:
  - NEW count
  - OLD count
  ↓
Return grouped structure
  ↓
Frontend renders:
  Level 1: Universities (parent groups)
  Level 2: Directories (departments)
  Level 3: Contacts (individual faculty)
```

**Example API Response:**
```json
{
  "success": true,
  "data": {
    "University of Miami": {
      "directories": [
        {
          "university_name": "Miami University - Biochemistry And Molecular Biology",
          "department": "Biochemistry And Molecular Biology",
          "url": "https://med.miami.edu/...",
          "enabled": true,
          "contacts": {"new": 0, "old": 112}
        }
      ],
      "total_new": 0,
      "total_old": 1308
    }
  }
}
```

**Clicking Into a Directory:**
```
User clicks "Biochemistry And Molecular Biology"
  ↓
GET /api/contacts?university_name=Miami%20University%20-%20Biochemistry%20And%20Molecular%20Biology&limit=50&offset=0
  ↓
google_sheets.py: get_contacts_from_new_contacts_sheet()
  ↓
Filter NEW CONTACTS by:
  - University = "Miami University - Biochemistry And Molecular Biology"
  - Status = ALL (default) or NEW/OLD
  - days_back = all (default) or 30/60/90
  ↓
Sort: NEW first (status_priority=1), then OLD (status_priority=0)
  ↓
Apply pagination (limit=50, offset=0)
  ↓
Return contacts
```

---

## 🎨 UI Components

### Dashboard Tab

**Features:**
- System status overview
- Recent scrape runs
- Success rate statistics
- Next scheduled run time
- Add new directory form
- Manual scrape trigger button

**Key Elements:**
```html
<div id="tab-dashboard">
  <!-- System Status Card -->
  <div id="last-run-status">Successful</div>
  <div id="next-run-time">Monday, Apr 11, 8:00 PM UTC</div>

  <!-- Add Directory Form -->
  <input id="directory-url" placeholder="https://...">
  <input id="sales-rep-email" placeholder="sales@company.com">
  <button onclick="addDirectory()">Add Directory</button>
</div>
```

### Browse Contacts Tab

**Features:**
- 3-level hierarchical navigation
- Time-based filtering (30/60/90 days, Since Added)
- Search contacts by name, email, title, etc.
- Pagination (50 contacts per page)
- Breadcrumb navigation

**Layout:**
```html
<div id="tab-browse">
  <!-- Search Bar -->
  <input id="contact-search-input" placeholder="Search contacts...">

  <!-- Time Filters -->
  <button onclick="applyTimeFilter(30)">Last 30 Days</button>
  <button onclick="applyTimeFilter(60)">Last 60 Days</button>
  <button onclick="applyTimeFilter(90)">Last 90 Days</button>
  <button onclick="applyTimeFilter('all')" class="active">Since Added</button>

  <!-- Breadcrumb -->
  <div id="breadcrumb">All Universities › University of Miami › Biochemistry</div>

  <!-- Content Area -->
  <div id="browse-content">
    <!-- Dynamically populated with universities/directories/contacts -->
  </div>

  <!-- Pagination -->
  <div id="pagination-controls">
    <button>← Previous</button>
    <span>Page 1 of 3</span>
    <button>Next →</button>
  </div>
</div>
```

**Navigation Flow:**
```
Level 1: University Groups
  ├─ University of Miami (20 departments, 1308 contacts)
  ├─ University of Florida (16 departments, 1150 contacts)
  └─ Stanford (1 department, 67 contacts)
    ↓ Click "University of Miami"

Level 2: Directories
  ├─ Biochemistry And Molecular Biology (112 contacts)
  ├─ Cell Biology (40 contacts)
  ├─ Neurology (190 contacts)
  └─ ...
    ↓ Click "Biochemistry"

Level 3: Contacts
  ├─ Sylvia Daunert, Pharm.D., M.S. (Professor) - OLD
  ├─ Mohd Tasleem Arif (Associate Professor) - OLD
  └─ ...
```

### Most Recent New Tab

**Features:**
- Shows newest NEW contacts across ALL directories
- Slim card design for quick scanning
- Click to see full details
- Time filtering (30/60/90 days, All Time)

**Layout:**
```html
<div id="tab-recent">
  <!-- Time Filters -->
  <button onclick="loadRecentContacts(30)">Last 30 Days</button>
  <button onclick="loadRecentContacts(60)">Last 60 Days</button>
  <button onclick="loadRecentContacts(90)">Last 90 Days</button>
  <button onclick="loadRecentContacts('all')">All Time</button>

  <!-- Slim Contact Cards -->
  <div class="slim-contact-card" onclick="showContactDetails(facultyId)">
    <div class="slim-contact-name">Dr. John Smith</div>
    <div class="slim-contact-meta">University of Miami - Biochemistry</div>
    <div class="slim-contact-date">2026-04-06</div>
  </div>
</div>
```

---

## 🔧 Key Technologies

### Backend
- **Flask** - Web framework
- **gspread** - Google Sheets API
- **Playwright** - Browser automation for dynamic scraping
- **BeautifulSoup** - HTML parsing
- **Anthropic Claude** - AI-powered scraping fallback

### Frontend
- **Vanilla JavaScript** - No frameworks (keeps it simple)
- **Fetch API** - AJAX requests
- **CSS Grid/Flexbox** - Responsive layout
- **Glassmorphism** - Modern UI design

### Infrastructure
- **Render** - Hosting platform
- **GitHub Actions** - Scheduled scraping
- **Google Sheets** - Database
- **SMTP** - Email notifications

---

## 📈 Current State

### Database Statistics
- **Total Contacts:** 2,458
- **Universities:** 38
- **NEW Contacts:** 0 (all baseline)
- **OLD Contacts:** 2,458

### Top Directories by Contact Count
1. Faculty by Department » College of Dentistry » University of Florida: 292 OLD
2. Miami University - Neurology: 190 OLD
3. Miami University - Biochemistry: 112 OLD
4. Miami University - Psychiatry: 110 OLD
5. Miami University - Pathology: 104 OLD

### Scraping Schedule
- **Monday:** 8:00 PM UTC
- **Thursday:** 8:00 PM UTC
- **Manual:** `python3 src/main.py`

---

## 🔍 How Baseline System Works

### Problem It Solves

Without baseline tracking:
```
Monday scrape: 100 faculty discovered → marked NEW
User doesn't check
Thursday scrape: Same 100 marked OLD, 2 new → marked NEW
User checks Friday: sees 2 NEW, 100 OLD
❌ Those 100 "OLD" are actually new to the user!
```

### Solution with Baseline

**First scrape:**
```
Check: first_scrape_completed == FALSE?
  YES → This is baseline establishment
  ↓
Scrape 100 faculty
  ↓
Mark ALL 100 as OLD (baseline)
  ↓
Set first_scrape_completed = TRUE
  ↓
No email sent (these are baseline)
```

**Subsequent scrapes:**
```
Check: first_scrape_completed == TRUE?
  YES → Baseline already established
  ↓
Scrape 102 faculty
  ↓
Compare with existing 100 in NEW CONTACTS
  ↓
Find 2 NEW (not in existing)
  ↓
Mark 2 as NEW, keep 100 as OLD
  ↓
Send email: "2 new faculty discovered!"
```

### Time Filters

Users can view contacts by recency:
- **Last 30 Days:** Contacts added in past 30 days (regardless of NEW/OLD)
- **Last 60 Days:** Contacts added in past 60 days
- **Last 90 Days:** Contacts added in past 90 days
- **Since Added:** All contacts (default)

This lets users see recent hires even if they're marked OLD (baseline).

---

## 🚀 Deployment

### Local Development
```bash
cd /Users/eddieflottemesch/Desktop/FacultySnipe
python3 app.py
# Open http://localhost:5001
```

### Render Deployment
1. Push to GitHub `main` branch
2. Render auto-deploys (if configured)
3. Or manually deploy via Render dashboard

### Environment Variables (Required)
```bash
GOOGLE_SHEETS_CREDENTIALS_BASE64=<base64 encoded service account JSON>
GOOGLE_SHEET_ID=<spreadsheet ID>
SMTP_HOST=<SMTP server>
SMTP_PORT=<SMTP port>
SMTP_USERNAME=<email username>
SMTP_PASSWORD=<email password>
SENDER_EMAIL=<from email address>
```

---

## 📝 Summary

**FacultySnipe is a 3-tier system:**

1. **Scraping Layer** - Automated faculty directory monitoring with 3 scraper types
2. **Database Layer** - Google Sheets storing configuration and contacts
3. **Web Layer** - Flask API + HTML/JS frontend for browsing and management

**Key Workflows:**
- **Add Directory** → CONFIG sheet → Auto-fill on next run
- **First Scrape** → Mark all as OLD (baseline) → Set first_scrape_completed
- **Subsequent Scrapes** → Detect NEW hires → Email notification
- **Browse Contacts** → 3-level navigation → Time filtering → Search

**Current State:**
- ✅ 2,458 contacts across 38 directories
- ✅ Baseline established (all marked OLD)
- ✅ Ready to detect NEW faculty on next scrape
- ⏳ Waiting for Render deployment
