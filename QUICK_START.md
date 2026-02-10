# FacultySnipe - Quick Start Guide

## 🚀 Deploy in 10 Minutes

### Step 1: Push to GitHub (2 minutes)

```bash
cd /Users/eddieflottemesch/Desktop/FacultySnipe
git add .
git commit -m "Add Render deployment and monitoring"
git push origin main
```

### Step 2: Deploy to Render (5 minutes)

1. Go to https://render.com and sign up with GitHub
2. Click **New +** → **Web Service**
3. Connect your **FacultySnipe** repository
4. Configure:
   - **Name:** `facultysnipe-web`
   - **Build Command:** `pip install -r requirements-web.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
5. Add environment variables (copy from your `.env` file):
   - `GOOGLE_SHEETS_CREDENTIALS`
   - `GOOGLE_SHEET_ID`
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SENDER_EMAIL`
   - `LOG_LEVEL` = `INFO`
   - `PORT` = `10000`
6. Click **Create Web Service**
7. Wait 2-3 minutes for deployment

### Step 3: Get Your URL (1 minute)

Your app will be live at:
```
https://facultysnipe-web.onrender.com
```
(or whatever name you chose)

### Step 4: Test It (2 minutes)

1. Visit your URL
2. Add a test university
3. Check Google Sheets CONFIG tab - should see new row
4. Trigger manual GitHub Actions run to verify everything works

---

## 📧 Share with Your Buddy

Send this message:

```
Hi! Here's our faculty monitoring system:

🔗 https://facultysnipe-web.onrender.com

To add a university:
1. Paste the faculty directory URL
2. Enter your email
3. Click "Add University"

The system runs automatically every Monday and Thursday at 3 AM UTC.
You'll get an email when new faculty are detected.

No coding needed - just paste and click!
```

---

## 📊 What You Get

### Public Web Interface
- Add universities without terminal access
- View all monitored universities
- See system status and run history
- Simple, non-technical UI

### Automatic Scraping
- Runs Monday & Thursday at 3 AM UTC
- No manual triggering needed
- Processes all enabled universities
- Updates Google Sheets automatically

### Email Notifications
- Success emails (when new faculty found)
- Failure alerts (immediate)
- Run statistics and links to logs

### Monitoring Dashboard
- Last run status (✅ or ❌)
- Next scheduled run time
- Success rate percentage
- Recent run history
- Auto-refreshes every 30 seconds

### Google Sheets Tracking
- **CONFIG:** University configuration
- **Individual sheets:** Faculty data per university
- **NEW CONTACTS:** All new faculty in one place
- **SYSTEM_STATUS:** Complete run history ← NEW!

---

## 💰 Cost

**$0/month** - Everything runs on free tiers:
- Render Free: 750 hours/month (enough for 24/7)
- GitHub Actions Free: 2,000 minutes/month (way more than needed)
- Google Sheets: Unlimited
- Gmail SMTP: 500 emails/day

---

## 🔍 Monitoring

### What Your Buddy Sees

Web UI shows:
- Last run: "Thursday, Feb 6 at 3:00 AM - ✅ SUCCESS"
- Next run: "Monday, Feb 10 at 3:00 AM UTC"
- Success rate: "95% (19/20)"
- Recent runs: ✅ ✅ ✅ ❌ ✅

### What You Receive

**Success Email (when new faculty found):**
```
Subject: ✅ FacultySnipe Run Successful - 3 New Faculty

Summary:
- Universities Processed: 12
- New Faculty Detected: 3
- Changed Faculty: 1
- Execution Time: 8.5 min
```

**Failure Email (always sent):**
```
Subject: ❌ FacultySnipe Run Failed

Errors:
- Connection timeout to stanford.edu

Check logs: [GitHub Actions link]
```

### Google Sheets SYSTEM_STATUS

Complete run history:
| timestamp | status | new_faculty | execution_time | github_url |
|-----------|--------|-------------|----------------|------------|
| 2024-02-09 03:00 | SUCCESS | 3 | 8.5 min | [link] |
| 2024-02-06 03:00 | SUCCESS | 0 | 7.8 min | [link] |

---

## 📋 Files Changed

### New Files Created
- ✅ `render.yaml` - Render deployment config
- ✅ `requirements-web.txt` - Web-only dependencies
- ✅ `scripts/send_run_summary.py` - Email notifications
- ✅ `DEPLOYMENT_GUIDE.md` - Full deployment instructions
- ✅ `IMPLEMENTATION_SUMMARY.md` - What was implemented
- ✅ `QUICK_START.md` - This file!

### Files Modified
- ✅ `app.py` - Added health check + system status API
- ✅ `src/google_sheets.py` - Added update_system_status()
- ✅ `.github/workflows/faculty_monitor.yml` - Added monitoring
- ✅ `templates/index.html` - Added status dashboard

### Files Unchanged
- ✅ `src/main.py` - Scraper works as-is
- ✅ `src/scrapers/*` - All scrapers work as-is
- ✅ `src/email_notifier.py` - Email works as-is

---

## ⚠️ Important Notes

### Render Free Tier
- Apps sleep after 15 min of inactivity
- First request takes 30-60 seconds to wake up
- This is normal and expected
- Upgrade to Starter ($7/mo) for always-on if needed

### GitHub Actions
- Scheduled runs are on UTC time
- Manual triggers available in Actions tab
- Logs kept for 30 days
- Check Actions tab if run fails

### Google Sheets
- SYSTEM_STATUS sheet created on first run
- All sheets update automatically
- No manual intervention needed

---

## 🆘 Troubleshooting

### Web UI won't load
1. Check Render logs for errors
2. Verify environment variables are set
3. Test health endpoint: `/health` should return `{"status": "ok"}`

### GitHub Actions failing
1. Go to Actions tab → View logs
2. Check secrets are configured
3. Verify Google credentials are valid

### No emails received
1. Check spam folder
2. Verify SMTP credentials
3. Test with manual workflow run

### Status not showing
1. Wait for first automated run to create SYSTEM_STATUS sheet
2. Or manually trigger workflow
3. Check browser console for errors

---

## 📚 Documentation

- **DEPLOYMENT_GUIDE.md** - Detailed deployment steps
- **IMPLEMENTATION_SUMMARY.md** - Technical details of what was built
- **QUICK_START.md** - This file (fastest path to deployment)

---

## ✅ Success Checklist

You're done when:
- [ ] Web UI loads at public URL
- [ ] Can add universities via form
- [ ] Google Sheets updates automatically
- [ ] GitHub Actions runs on schedule
- [ ] Email notifications received
- [ ] System status shows in dashboard
- [ ] Buddy can use it without help

**Ready to deploy? Follow the steps above or see DEPLOYMENT_GUIDE.md for more details!**
