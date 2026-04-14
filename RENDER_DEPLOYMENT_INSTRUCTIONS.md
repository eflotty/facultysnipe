# Render Deployment Instructions

## Current Status

✅ **Backend Fixed:** All 2,458 contacts restored and working locally
✅ **Code Pushed:** Latest commit `8f5837c` pushed to GitHub
⏳ **Render Status:** Service not responding (404 errors)

**Latest test (just now):**
```bash
$ curl https://facultysnipe.onrender.com/health
Not Found (404)

$ curl https://facultysnipe.onrender.com/
Not Found (404)
```

This indicates the Render service is either:
1. **Still deploying** (wait 2-3 more minutes)
2. **Suspended** (free tier sleep - needs manual wake up)
3. **Deploy failed** (check logs for errors)
4. **Wrong URL** (need to verify correct Render URL)

---

## What You Need To Do Right Now

### Step 1: Log into Render Dashboard

1. Go to https://dashboard.render.com
2. Log in with your account
3. Find the FacultySnipe service

### Step 2: Check Service Status

Look for one of these statuses:

#### ✅ If Status = "Live"
- Service is running but URL might be wrong
- Check what the actual URL is in the dashboard
- Try that URL instead of `facultysnipe.onrender.com`

#### ⏳ If Status = "Deploying" or "Building"
- Wait for deployment to complete (usually 2-5 minutes)
- Watch the build logs for any errors
- Once it shows "Live", test the app

#### 😴 If Status = "Suspended"
**This is most likely the issue** (free tier sleeps after 15 min inactivity)

**How to fix:**
1. Click on the service
2. Click "Resume" button
3. Wait 30-60 seconds for service to wake up
4. Test URL again

#### ❌ If Status = "Deploy Failed"
**Check the error:**
1. Click on the service
2. Go to "Logs" tab
3. Look for red error messages
4. Common issues:
   - Missing environment variables
   - Build command failed
   - Start command failed
   - Gunicorn error

**Possible fixes:**
- Click "Manual Deploy" → "Clear build cache & deploy"
- Check environment variables are set
- Look at error logs and report back

### Step 3: Verify Environment Variables

Click on your service → "Environment" tab

**Required variables:**
- `GOOGLE_SHEETS_CREDENTIALS` or `GOOGLE_SHEETS_CREDENTIALS_BASE64`
- `GOOGLE_SHEET_ID` or `SPREADSHEET_ID`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SENDER_EMAIL`

**If any are missing:**
1. Click "Add Environment Variable"
2. Add the missing ones
3. Trigger new deployment

### Step 4: Check Correct URL

In the Render dashboard:
1. Click on your service
2. Look at the top - you'll see the URL
3. It might be different from `facultysnipe.onrender.com`
4. Use the exact URL shown

Common patterns:
- `facultysnipe.onrender.com`
- `facultysnipe-web.onrender.com`
- `your-custom-name.onrender.com`

---

## If Deployment is Successful

Once you see "Live" status and the URL responds:

### Test 1: Health Check
```bash
curl https://YOUR-RENDER-URL.onrender.com/health
```

**Expected response:**
```json
{"status": "ok", "timestamp": "2026-04-08T..."}
```

### Test 2: Browse Contacts
1. Open browser to `https://YOUR-RENDER-URL.onrender.com`
2. Click "Browse Contacts" tab
3. Click "Research Faculty » Lillian S. Wells..."
4. Click "Neurosurgery"
5. **Should see:** 64 OLD contacts

### Test 3: API Endpoint
```bash
curl "https://YOUR-RENDER-URL.onrender.com/api/contacts?university_name=Miami%20University%20-%20Cell%20Biology&limit=3"
```

**Expected:** JSON with 40 total contacts

---

## Common Render Issues & Fixes

### Issue 1: Free Tier Sleep
**Symptom:** Service shows "Suspended" or takes 30+ seconds to respond

**Fix:**
- Upgrade to paid tier ($7/mo) for always-on
- Or accept 30-60 second wake-up time on first request
- Click "Resume" in dashboard when suspended

### Issue 2: Build Failed
**Symptom:** Logs show "Build failed" or red error messages

**Common causes:**
- Missing dependency in `requirements.txt`
- Playwright install failed (needs system deps)
- Python version mismatch

**Fix:**
- Check logs for specific error
- Click "Manual Deploy" → "Clear build cache & deploy"
- Make sure `render.yaml` build command includes:
  ```
  pip install -r requirements.txt && playwright install-deps chromium && playwright install chromium
  ```

### Issue 3: Start Failed
**Symptom:** Build succeeds but service won't start

**Common causes:**
- Gunicorn can't find app
- Port binding issue
- Missing environment variables

**Fix:**
- Check start command in render.yaml: `gunicorn app:app`
- Verify `app.py` exists and has `app = Flask(__name__)`
- Check environment variables are set

### Issue 4: Wrong URL
**Symptom:** 404 errors on all endpoints

**Fix:**
- Verify exact URL in Render dashboard
- Service name might be different
- Check if custom domain is configured

---

## What I Already Did

✅ **Fixed contacts:** Restored 1,248 missing from backup → 2,458 total
✅ **Tested locally:** All endpoints working perfectly
✅ **Pushed to GitHub:** 3 commits pushed (`937c8b3`, `9e83e30`, `8f5837c`)
✅ **Triggered deployment:** Empty commit to force redeploy
✅ **Verified code:** Backend returns correct data

**What I can't do:**
❌ Access your Render dashboard
❌ Check deployment logs
❌ Resume suspended services
❌ Verify environment variables

**Only you can:**
- Log into Render dashboard
- Check service status
- Resume if suspended
- Read deployment logs
- Verify correct URL

---

## Quick Checklist

Go through this in order:

- [ ] Log into https://dashboard.render.com
- [ ] Find FacultySnipe service
- [ ] Check status (Live/Deploying/Suspended/Failed)
- [ ] If Suspended → Click "Resume"
- [ ] If Deploy Failed → Check logs, then "Manual Deploy"
- [ ] If Live → Verify correct URL
- [ ] Test health endpoint: `https://YOUR-URL/health`
- [ ] Open browser and test Browse Contacts
- [ ] Report back what status you see

---

## Next Steps Based On Status

### If you see "Live" status:
1. Share the exact URL from dashboard
2. Test that URL in browser
3. If still 404, we'll debug further

### If you see "Suspended":
1. Click "Resume"
2. Wait 30-60 seconds
3. Test URL again
4. Should work now

### If you see "Deploying":
1. Wait for it to finish (2-3 minutes)
2. Watch for "Live" status
3. Then test URL

### If you see "Deploy Failed":
1. Go to Logs tab
2. Copy the error message
3. Share it with me
4. We'll fix the issue

---

## Summary

**What's Working:**
✅ All 2,458 contacts restored in Google Sheets
✅ Backend API tested and working locally
✅ Code pushed to GitHub
✅ Deployment triggered

**What's Pending:**
⏳ Render service needs to deploy/wake up
⏳ Only you can check Render dashboard
⏳ Only you can resume if suspended

**Next Action:**
👉 **You:** Go to Render dashboard and report status
👉 **Me:** Will help based on what you find

The backend is 100% ready. Just need Render to deploy it! 🚀
