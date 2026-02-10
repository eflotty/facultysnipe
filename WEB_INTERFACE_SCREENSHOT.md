# Web Interface - Visual Layout

## Add University Form

Here's exactly what your team will see when they open the web interface:

```
╔═════════════════════════════════════════════════════════════════╗
║                                                                 ║
║                       FacultySnipe                              ║
║            Automated University Faculty Monitoring              ║
║                                                                 ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  ┌─────────────────────────────────────────────────────────┐   ║
║  │  Add University                                         │   ║
║  │  Enter faculty directory URL and sales rep email       │   ║
║  │  for notifications                                      │   ║
║  │                                                         │   ║
║  │  Faculty Directory URL                                 │   ║
║  │  ┌──────────────────────────────────────────────────┐  │   ║
║  │  │ https://biology.stanford.edu/people/faculty      │  │   ║
║  │  └──────────────────────────────────────────────────┘  │   ║
║  │                                                         │   ║
║  │  📧 Sales Rep Email                                    │   ║
║  │  ┌──────────────────────────────────────────────────┐  │   ║
║  │  │ rep@company.com                                  │  │   ║
║  │  └──────────────────────────────────────────────────┘  │   ║
║  │  This person will receive email alerts when new        │   ║
║  │  faculty are detected                                   │   ║
║  │                                                         │   ║
║  │  ┌──────────────────────────────────────────────────┐  │   ║
║  │  │          Add University                          │  │   ║
║  │  └──────────────────────────────────────────────────┘  │   ║
║  │                                                         │   ║
║  └─────────────────────────────────────────────────────────┘   ║
║                                                                 ║
║  ┌─────────────────────────────────────────────────────────┐   ║
║  │  Statistics                                             │   ║
║  │                                                         │   ║
║  │   ┌──────────┐  ┌──────────┐  ┌──────────┐            │   ║
║  │   │    12    │  │    10    │  │    8     │            │   ║
║  │   │  TOTAL   │  │ ENABLED  │  │ SUCCESS  │            │   ║
║  │   └──────────┘  └──────────┘  └──────────┘            │   ║
║  │                                                         │   ║
║  └─────────────────────────────────────────────────────────┘   ║
║                                                                 ║
║  ┌─────────────────────────────────────────────────────────┐   ║
║  │  Monitored Universities                                 │   ║
║  │  All universities in your configuration                 │   ║
║  │                                                         │   ║
║  │  ┌──────────────────────────────────────────────────┐  │   ║
║  │  │        🚀 Run Monitor Now                        │  │   ║
║  │  └──────────────────────────────────────────────────┘  │   ║
║  │                                                         │   ║
║  │  ┌──────────────────────────────────────────────────┐  │   ║
║  │  │ Stanford University                              │  │   ║
║  │  │ https://biology.stanford.edu/people/faculty      │  │   ║
║  │  │ 📧 john@company.com                              │  │   ║
║  │  │ [ENABLED] [SUCCESS]                              │  │   ║
║  │  └──────────────────────────────────────────────────┘  │   ║
║  │                                                         │   ║
║  │  ┌──────────────────────────────────────────────────┐  │   ║
║  │  │ UFL - Biochemistry                               │  │   ║
║  │  │ https://biochem.ufl.edu/people/faculty           │  │   ║
║  │  │ 📧 sarah@company.com                             │  │   ║
║  │  │ [ENABLED] [SUCCESS]                              │  │   ║
║  │  └──────────────────────────────────────────────────┘  │   ║
║  │                                                         │   ║
║  │  ┌──────────────────────────────────────────────────┐  │   ║
║  │  │ Miami - Microbiology                             │  │   ║
║  │  │ https://med.miami.edu/microbiology/faculty       │  │   ║
║  │  │ [DISABLED]                                       │  │   ║
║  │  └──────────────────────────────────────────────────┘  │   ║
║  │                                                         │   ║
║  └─────────────────────────────────────────────────────────┘   ║
║                                                                 ║
╚═════════════════════════════════════════════════════════════════╝
```

## Key Features Highlighted

### 1. **Two Input Fields**
- ✅ **Faculty Directory URL** - Required field
- ✅ **📧 Sales Rep Email** - With helpful description below

### 2. **Clear Help Text**
The form shows:
> "This person will receive email alerts when new faculty are detected"

So your team knows exactly what the email field is for!

### 3. **University List Shows Email**
Each university in the list now shows:
- University name
- URL
- **📧 Sales rep email** (with email icon)
- Status badges

## What Happens When You Submit

### Step 1: Enter Data
```
URL: https://biology.stanford.edu/people/faculty
Email: john@company.com
```

### Step 2: Click "Add University"
The form submits and shows a success message:
```
✅ Added https://biology.stanford.edu/people/faculty to CONFIG sheet!
   Run the bot to auto-fill details.
```

### Step 3: Bot Auto-fills
Next time you run the monitor, it auto-fills:
- `university_id`: stanford_biology
- `university_name`: Stanford University
- `scraper_class`: HybridScraper
- `enabled`: TRUE

### Step 4: New Faculty Email Alert
When new faculty are detected, the system emails `john@company.com` with:
- List of new faculty names
- Titles and emails
- Links to their profiles
- Direct link to Google Sheet

## Example Email Your Sales Rep Gets

```
Subject: 🎓 3 New Faculty Detected at Stanford University

Hi there!

We detected 3 new faculty members at Stanford University:

1. Dr. Jane Smith
   - Title: Assistant Professor
   - Email: jsmith@stanford.edu
   - Profile: https://biology.stanford.edu/people/jane-smith

2. Dr. John Doe
   - Title: Associate Professor
   - Email: jdoe@stanford.edu
   - Profile: https://biology.stanford.edu/people/john-doe

3. Dr. Sarah Johnson
   - Title: Professor
   - Email: sjohnson@stanford.edu
   - Profile: https://biology.stanford.edu/people/sarah-johnson

View all data: [Link to Google Sheet]

---
Generated by FacultySnipe
```

## Access Instructions for Your Team

1. **Start the web server** (one time)
   ```bash
   ./start_web.sh
   ```

2. **Open browser** (everyone on the network)
   ```
   http://localhost:5001
   ```

3. **Add universities** (as many as you want)
   - Paste URL
   - Enter sales rep email
   - Click "Add University"

4. **Run monitor** (triggers scraping)
   - Click "🚀 Run Monitor Now"
   - Wait for completion
   - Check email for alerts

That's it! No Google Sheets access needed. No technical knowledge required.
