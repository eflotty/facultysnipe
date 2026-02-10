# FacultySnipe Deployment Guide

## Overview

This guide will walk you through deploying FacultySnipe to Render.com for free, giving you:
- **Public web UI** accessible from anywhere (no terminal needed)
- **Automatic scraping** 2x per week (Monday & Thursday at 3 AM UTC)
- **Email alerts** for new faculty and failures
- **System monitoring** dashboard with run history

**Total Cost: $0/month** (within free tiers)

---

## Prerequisites

Before you begin, make sure you have:

1. GitHub account with this repository
2. Google Cloud credentials (service account JSON)
3. Google Sheet ID
4. SMTP credentials for email notifications
5. All environment variables from your `.env` file

---

## Step 1: Push Code to GitHub

If you haven't already, push your code to GitHub:

```bash
cd /Users/eddieflottemesch/Desktop/FacultySnipe

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - FacultySnipe with Render deployment"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/FacultySnipe.git

# Push
git push -u origin main
```

---

## Step 2: Deploy to Render.com

### 2.1 Sign Up for Render

1. Go to https://render.com
2. Click "Get Started" or "Sign Up"
3. Sign up with your GitHub account (recommended for easy integration)

### 2.2 Create New Web Service

1. Click "New +" button in top right
2. Select "Web Service"
3. Connect your GitHub repository:
   - Click "Connect Account" if needed
   - Select your FacultySnipe repository
   - Click "Connect"

### 2.3 Configure Web Service

Fill in the following settings:

**Basic Settings:**
- **Name:** `facultysnipe-web` (or your preferred name)
- **Region:** Choose closest to you (e.g., Oregon, USA)
- **Branch:** `main`
- **Root Directory:** Leave empty
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements-web.txt`
- **Start Command:** `gunicorn app:app`

**Instance Type:**
- Select **Free** ($0/month - 750 hours/month)

### 2.4 Add Environment Variables

Scroll down to "Environment Variables" and add each of these:

Click "Add Environment Variable" for each:

| Key | Value | Where to get it |
|-----|-------|----------------|
| `GOOGLE_SHEETS_CREDENTIALS` | Your service account JSON | Copy from `.env` file |
| `GOOGLE_SHEET_ID` | Your Google Sheet ID | Copy from `.env` file |
| `SMTP_HOST` | SMTP server (e.g., smtp.gmail.com) | Copy from `.env` file |
| `SMTP_PORT` | SMTP port (e.g., 587) | Copy from `.env` file |
| `SMTP_USERNAME` | SMTP username | Copy from `.env` file |
| `SMTP_PASSWORD` | SMTP password | Copy from `.env` file |
| `SENDER_EMAIL` | Sender email address | Copy from `.env` file |
| `LOG_LEVEL` | INFO | Set manually |
| `PORT` | 10000 | Set manually (Render default) |

**IMPORTANT for GOOGLE_SHEETS_CREDENTIALS:**
- Copy the ENTIRE JSON content from your `.env` file
- Make sure it's valid JSON (starts with `{` and ends with `}`)
- Remove any line breaks or extra quotes

### 2.5 Deploy

1. Click "Create Web Service"
2. Render will start building and deploying
3. Wait 2-3 minutes for first deployment
4. You'll see logs in real-time

### 2.6 Get Your Public URL

Once deployed successfully:
- Your app URL will be: `https://facultysnipe-web.onrender.com`
  (or whatever name you chose)
- Click the URL to test your web UI
- You should see the FacultySnipe interface!

---

## Step 3: Configure GitHub Actions Secrets

Your GitHub Actions workflow needs the same environment variables:

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

Add these secrets (same values as Render):
- `GOOGLE_SHEETS_CREDENTIALS`
- `GOOGLE_SHEET_ID`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SENDER_EMAIL`

**Note:** These are already configured if you've run GitHub Actions before. Just verify they're all set.

---

## Step 4: Create SYSTEM_STATUS Sheet in Google Sheets

The monitoring dashboard needs a SYSTEM_STATUS sheet:

1. Open your Google Sheet
2. The sheet will be created automatically on the first run
3. Or manually create a new tab called `SYSTEM_STATUS` with these columns:
   - `timestamp`
   - `status`
   - `universities_processed`
   - `new_faculty`
   - `changed_faculty`
   - `execution_time`
   - `errors`
   - `github_url`

---

## Step 5: Test End-to-End

### 5.1 Test Web UI

1. Visit your Render URL: `https://facultysnipe-web.onrender.com`
2. You should see:
   - System status banner (will show "No runs yet" initially)
   - Add University form
   - Statistics dashboard
   - List of monitored universities

### 5.2 Add a Test University

1. Paste a faculty URL (e.g., `https://biology.stanford.edu/people/faculty`)
2. Enter your email
3. Click "Add University"
4. Check Google Sheets CONFIG tab - should see new row

### 5.3 Trigger Manual GitHub Actions Run

1. Go to GitHub repository → **Actions** tab
2. Click **Faculty Monitor** workflow
3. Click **Run workflow** button
4. Select `main` branch
5. Click **Run workflow**
6. Wait 5-10 minutes for completion

### 5.4 Verify Results

After the run completes, check:

**Google Sheets:**
- CONFIG tab: `last_run` and `last_status` updated
- Individual university sheet: Faculty data populated
- NEW CONTACTS tab: New faculty listed
- SYSTEM_STATUS tab: Run logged with stats

**Email:**
- Success email received (if new faculty found)
- Or failure alert (if errors occurred)

**Web UI:**
- Refresh your Render URL
- System status banner should show:
  - Last run time and status (✅ or ❌)
  - Next scheduled run
  - Success rate
  - Recent runs indicators

---

## Step 6: Share with Your Buddy

Send your buddy:

### Simple Instructions

```
Hi! Here's the FacultySnipe web interface:

URL: https://facultysnipe-web.onrender.com

How to add a university:
1. Paste the faculty directory URL
2. Enter your email (for new faculty alerts)
3. Click "Add University"

The system runs automatically every Monday and Thursday at 3 AM UTC.
You'll receive an email when new faculty are detected.

That's it! No coding or terminal needed.
```

---

## Troubleshooting

### Web UI Not Loading

1. Check Render logs:
   - Go to Render dashboard → Your service → Logs
   - Look for errors in deployment
2. Verify environment variables are set correctly
3. Check health endpoint: `https://your-app.onrender.com/health`
   - Should return: `{"status": "ok", "timestamp": "..."}`

### GitHub Actions Failing

1. Check workflow logs:
   - Go to GitHub → Actions → Failed run → View logs
2. Common issues:
   - Missing secrets
   - Invalid Google credentials
   - Playwright installation timeout (increase timeout if needed)

### No Emails Received

1. Check SMTP credentials in environment variables
2. Verify sender email is correct
3. Check spam folder
4. Test SMTP with a simple script

### System Status Not Showing

1. Check if SYSTEM_STATUS sheet exists in Google Sheets
2. Run workflow manually to populate data
3. Check browser console for JavaScript errors
4. Verify `/api/system-status` endpoint returns data

### Render Free Tier Sleeping

- Free tier apps sleep after 15 minutes of inactivity
- First request after sleeping takes 30-60 seconds to wake up
- Upgrade to Starter plan ($7/month) for always-on if needed

---

## Monitoring & Maintenance

### What You'll Receive

**Success Emails (only when new faculty found):**
- Subject: "✅ FacultySnipe Run Successful - X New Faculty"
- Summary of universities processed
- Count of new/changed faculty
- Link to GitHub Actions logs

**Failure Emails (always sent on failure):**
- Subject: "❌ FacultySnipe Run Failed"
- Error details
- Link to GitHub Actions logs

### Checking Status

**Web Dashboard:**
- Visit your Render URL anytime
- See recent run history (last 5 runs)
- Success rate percentage
- Next scheduled run time

**Google Sheets SYSTEM_STATUS:**
- Complete history of all runs
- Timestamps, statistics, errors
- Links to GitHub Actions logs

**GitHub Actions:**
- Go to Actions tab
- See all workflow runs
- Download logs as artifacts

---

## Upgrading (Optional)

### Render Starter Plan ($7/month)

Benefits:
- Custom domain (e.g., facultysnipe.yourdomain.com)
- Always-on (no sleeping)
- More resources (512 MB RAM → 2 GB RAM)

To upgrade:
1. Go to Render dashboard → Your service
2. Click "Upgrade" button
3. Select Starter plan

### Adding More Universities

Free tiers should handle:
- **Render:** 750 hours/month = 24/7 uptime for web UI
- **GitHub Actions:** 2,000 minutes/month = ~133 runs of 15 min each
- Current usage: ~8 runs/month × 10 min = 80 min/month

You can monitor **hundreds** of universities before hitting limits.

---

## Architecture Summary

```
┌─────────────────────────────────────────┐
│  Web UI (Render)                        │
│  - Public URL: https://your-app.com     │
│  - Add universities via form            │
│  - View system status & history         │
└────────────┬────────────────────────────┘
             │ Writes to CONFIG sheet
             ▼
┌─────────────────────────────────────────┐
│  Google Sheets (Data Storage)           │
│  - CONFIG: University list              │
│  - Individual sheets: Faculty data      │
│  - NEW CONTACTS: All new faculty        │
│  - SYSTEM_STATUS: Run history           │
└────────────┬────────────────────────────┘
             │ Reads CONFIG
             ▼
┌─────────────────────────────────────────┐
│  GitHub Actions (Scraper)               │
│  - Runs Mon/Thu at 3 AM UTC             │
│  - Scrapes all enabled universities     │
│  - Updates Google Sheets                │
│  - Sends email notifications            │
│  - Updates SYSTEM_STATUS                │
└─────────────────────────────────────────┘
```

---

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test web UI and add universities
3. ✅ Verify GitHub Actions runs successfully
4. ✅ Share URL with your buddy
5. ✅ Monitor email alerts

**You're all set!** The system will now run automatically 2x per week, and your buddy can add universities without any technical knowledge.

---

## Support

If you encounter issues:
1. Check troubleshooting section above
2. Review Render and GitHub Actions logs
3. Verify environment variables
4. Test Google Sheets connectivity

For questions or issues, create an issue on GitHub.
