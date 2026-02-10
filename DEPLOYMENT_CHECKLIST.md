# FacultySnipe Deployment Checklist

Use this checklist to ensure successful deployment.

## ✅ Pre-Deployment

- [ ] All code changes committed locally
- [ ] .env file has all required environment variables:
  - [ ] GOOGLE_SHEETS_CREDENTIALS
  - [ ] GOOGLE_SHEET_ID
  - [ ] SMTP_HOST
  - [ ] SMTP_PORT
  - [ ] SMTP_USERNAME
  - [ ] SMTP_PASSWORD
  - [ ] SENDER_EMAIL
- [ ] GitHub repository exists and is accessible
- [ ] Google Sheets service account has edit access to your sheet

## 🔨 GitHub Setup

- [ ] Code pushed to GitHub repository
- [ ] GitHub Actions secrets configured:
  - [ ] GOOGLE_SHEETS_CREDENTIALS
  - [ ] GOOGLE_SHEET_ID
  - [ ] SMTP_HOST
  - [ ] SMTP_PORT
  - [ ] SMTP_USERNAME
  - [ ] SMTP_PASSWORD
  - [ ] SENDER_EMAIL
- [ ] GitHub Actions workflow file present (.github/workflows/faculty_monitor.yml)
- [ ] Test manual workflow run (optional, but recommended)

## 🚀 Render Deployment

### Account Setup
- [ ] Created account at https://render.com
- [ ] Connected GitHub account to Render
- [ ] Verified repository access

### Web Service Configuration
- [ ] Created new Web Service
- [ ] Connected correct repository
- [ ] Configured service settings:
  - [ ] Name: facultysnipe-web (or your choice)
  - [ ] Build Command: `pip install -r requirements-web.txt`
  - [ ] Start Command: `gunicorn app:app`
  - [ ] Instance Type: Free
  - [ ] Health Check Path: `/health`

### Environment Variables (Render)
- [ ] GOOGLE_SHEETS_CREDENTIALS (full JSON)
- [ ] GOOGLE_SHEET_ID
- [ ] SMTP_HOST
- [ ] SMTP_PORT
- [ ] SMTP_USERNAME
- [ ] SMTP_PASSWORD
- [ ] SENDER_EMAIL
- [ ] LOG_LEVEL = INFO
- [ ] PORT = 10000

### Deployment
- [ ] Clicked "Create Web Service"
- [ ] Waited for deployment to complete (2-3 minutes)
- [ ] No build errors in logs
- [ ] Service shows "Live" status

## 🧪 Testing

### Web UI Tests
- [ ] Can access public URL (https://your-app.onrender.com)
- [ ] Health endpoint works (/health returns JSON)
- [ ] Main page loads without errors
- [ ] System status banner displays
- [ ] Statistics show (even if 0)
- [ ] Universities list loads (may be empty)

### Functionality Tests
- [ ] Can submit "Add University" form
- [ ] Google Sheets CONFIG tab updates with new row
- [ ] New row has URL and enabled=TRUE
- [ ] No errors in browser console

### GitHub Actions Tests
- [ ] Manual workflow trigger works
- [ ] Workflow completes successfully
- [ ] Google Sheets updates:
  - [ ] Individual university sheets created
  - [ ] Faculty data populated
  - [ ] NEW CONTACTS tab updated
  - [ ] SYSTEM_STATUS tab created ← NEW!
  - [ ] CONFIG last_run and last_status updated
- [ ] Email notifications received:
  - [ ] Success email (if new faculty found)
  - [ ] OR failure email (if errors occurred)

### System Status Tests
- [ ] Web UI shows last run information
- [ ] Recent runs icons display (✅ or ❌)
- [ ] Success rate calculates correctly
- [ ] Next run time displays
- [ ] Status auto-refreshes (wait 30 seconds)

## 📊 Google Sheets Verification

- [ ] CONFIG tab exists with universities
- [ ] Individual university sheets created
- [ ] NEW CONTACTS tab populated
- [ ] SYSTEM_STATUS tab created with:
  - [ ] Headers: timestamp, status, universities_processed, etc.
  - [ ] At least one row of data
  - [ ] Status is SUCCESS or FAILURE
  - [ ] GitHub Actions URL present

## 📧 Email Verification

- [ ] Admin email received success summary (if new faculty)
- [ ] OR admin email received failure alert (if error)
- [ ] Email contains:
  - [ ] Run statistics
  - [ ] Link to GitHub Actions logs
  - [ ] Timestamp
- [ ] Sales rep emails sent for new faculty (check with test)

## 🔄 Scheduled Runs

- [ ] Verified schedule in GitHub Actions (Mon/Thu 3 AM UTC)
- [ ] Workflow not disabled
- [ ] Next run date visible in web UI

## 📱 User Handoff

- [ ] Public URL documented and ready to share
- [ ] Simple instructions prepared for buddy:
  - [ ] URL to access
  - [ ] How to add universities (paste + click)
  - [ ] When system runs (Mon/Thu 3 AM UTC)
  - [ ] What to expect (email notifications)

## 📄 Documentation

- [ ] QUICK_START.md reviewed
- [ ] DEPLOYMENT_GUIDE.md available for reference
- [ ] IMPLEMENTATION_SUMMARY.md explains technical details
- [ ] This checklist completed!

## 🎉 Go Live!

Once all items are checked:

1. ✅ Share URL with buddy
2. ✅ Monitor first scheduled run
3. ✅ Verify emails arrive as expected
4. ✅ Check system status updates correctly
5. ✅ Celebrate! 🎊

---

## 🆘 If Something Goes Wrong

### Render deployment fails
→ Check logs in Render dashboard
→ Verify all environment variables set
→ Ensure requirements-web.txt is valid
→ Test locally with `gunicorn app:app`

### GitHub Actions fails
→ Check Actions tab for error logs
→ Verify all secrets configured
→ Test Google Sheets access manually
→ Check SMTP credentials

### No emails sent
→ Check spam folder
→ Verify SMTP credentials
→ Test with manual workflow run
→ Check email quota not exceeded

### System status not showing
→ Wait for first run to create sheet
→ Check browser console for errors
→ Verify /api/system-status returns data
→ Manually trigger workflow to populate

### Web UI sleeping (Render free tier)
→ Normal behavior after 15 min inactivity
→ First request takes 30-60s to wake
→ Consider Starter plan ($7/mo) for always-on

---

**Need help?** Review DEPLOYMENT_GUIDE.md troubleshooting section.
