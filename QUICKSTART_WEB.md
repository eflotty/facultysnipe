# Quick Start - Web Interface

## Start the Web Server

### Option 1: Using the Script (Easiest)
```bash
./start_web.sh
```

### Option 2: Direct Command
```bash
python3 app.py
```

## Access the Interface

Open your browser and go to:
```
http://localhost:5001
```

## Add Your First University

1. **Enter the URL**
   - Paste the faculty directory URL
   - Example: `https://biology.stanford.edu/people/faculty`

2. **Add Sales Rep Email (Optional)**
   - Enter the email for notifications
   - Example: `rep@company.com`

3. **Click "Add University"**
   - The URL is added to Google Sheets immediately
   - Auto-fill will populate details on next run

4. **Run the Monitor**
   - Click "🚀 Run Monitor Now"
   - Watch as the bot scrapes and updates data

## What Happens Next?

The system will:
1. ✅ Auto-detect the university name and ID
2. ✅ Choose the best scraper strategy
3. ✅ Scrape all faculty data
4. ✅ Update your Google Sheet
5. ✅ Send email alerts for new faculty

## View Results

- **Statistics Card** - See total universities, enabled count, success rate
- **Universities List** - View all monitored universities with status badges
- **Auto-Refresh** - Page updates every 30 seconds automatically

## That's It!

No Google Sheets access required. No technical knowledge needed. Just paste URLs and click!

---

**Need Help?** Check `WEB_INTERFACE.md` for detailed documentation.
