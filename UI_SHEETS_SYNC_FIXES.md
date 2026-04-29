# UI ↔ Google Sheets Synchronization Fixes

## Issues Fixed

### ❌ **Problem 1: Dashboard showed old run data as "current"**

**Before:**
```
Most Recent Run: Successful
2026-04-27 21:03:48 UTC
1120 new faculty detected
```

This was showing data from the SYSTEM_STATUS sheet (historical run data), making it look like there are 1120 NEW contacts currently, when actually there are 2,458 OLD contacts and 0 NEW.

**After:**
- Added **"Current Database"** section showing LIVE counts from NEW CONTACTS sheet
- Changed **"Most Recent Run"** to **"Last Scrape Run"** to clarify it's historical
- Changed "new faculty detected" to "contacts added in that run" to clarify it's from the past run

**New Dashboard Layout:**
```
📊 Current Database
Total Contacts: 2,458
NEW: 0
OLD (Baseline): 2,458
Universities: 38

⏱️ Last Scrape Run
Status: Successful
2026-04-27 21:03:48 UTC
36 directories scraped
1120 contacts added in that run
```

---

### ❌ **Problem 2: "Most Recent New" tab showed only 1 contact**

**Issue:** The tab was filtering by `status=NEW`, which returned 0 contacts since everything is baseline (OLD).

**Before:**
```javascript
let apiUrl = `/api/contacts?status=NEW&limit=100`;
```

This would only show contacts with Status=NEW in the NEW CONTACTS sheet. Since all 2,458 contacts are marked OLD (baseline), it showed "No new contacts found".

**After:**
```javascript
let apiUrl = `/api/contacts?limit=100`;
```

Now it shows the most **recently ADDED** contacts (by Date Added column), regardless of NEW/OLD status.

**New Features:**
- Shows contacts sorted by Date Added (most recent first)
- Displays STATUS badge (NEW or OLD) on each contact card
- Renamed tab title from "Most Recent New Contacts" to "Recently Added Contacts"
- Updated subtitle to clarify it shows "contacts added to database (sorted by date added)"

---

### ❌ **Problem 3: No way to see current database state**

**Before:** Only historical run data was visible (from SYSTEM_STATUS sheet)

**After:** Added new `loadCurrentDatabaseStats()` function that:
- Calls `/api/contacts/summary` endpoint
- Shows live counts from NEW CONTACTS sheet:
  - Total contacts
  - NEW count
  - OLD count
  - Number of universities
- Refreshes every 30 seconds (same as other dashboard data)

---

## Changes Made

### 1. Dashboard HTML (templates/index.html)

**Added "Current Database" section:**
```html
<div class="card" style="background: rgba(52, 211, 153, 0.1);">
    <div style="font-size: 18px;">📊 Current Database</div>
    <div id="current-total-contacts">2,458</div>
    <div id="current-new-contacts">0</div>
    <div id="current-old-contacts">2,458</div>
    <div id="current-universities">38</div>
</div>
```

**Updated "System Status" section:**
- Changed title from "Most Recent Run" to "Last Scrape Run"
- Added "directories scraped" count
- Changed "new faculty detected" to "contacts added in that run"

### 2. JavaScript Functions

**Added `loadCurrentDatabaseStats()`:**
```javascript
async function loadCurrentDatabaseStats() {
    const response = await fetch('/api/contacts/summary');
    const data = await response.json();

    document.getElementById('current-total-contacts').textContent =
        data.summary.total_contacts.toLocaleString();
    document.getElementById('current-new-contacts').textContent =
        data.summary.total_new.toLocaleString();
    document.getElementById('current-old-contacts').textContent =
        data.summary.total_old.toLocaleString();
    document.getElementById('current-universities').textContent =
        Object.keys(data.by_university).length;
}
```

**Updated `loadRecentContacts()`:**
- Removed `status=NEW` filter
- Now fetches all recent contacts sorted by date
- Still respects `days_back` filter (30/60/90 days)

**Updated `renderRecentContacts()`:**
- Shows STATUS badge (NEW in green, OLD in gray)
- Changed "No new contacts found" to "No recent contacts found"

### 3. Auto-refresh Logic

```javascript
// Load data on page load
loadUniversities();
loadSystemStatus();
loadCurrentDatabaseStats(); // NEW

// Auto-refresh every 30 seconds
setInterval(() => {
    loadUniversities();
    loadSystemStatus();
    loadCurrentDatabaseStats(); // NEW
}, 30000);
```

### 4. "Recently Added" Tab

**Renamed from:**
- "Most Recent New Contacts"
- "Newest faculty discoveries across all directories"

**Renamed to:**
- "Recently Added Contacts"
- "Most recent contacts added to database (sorted by date added)"

---

## How It Works Now

### Dashboard Data Sources

**Current Database (Live):**
- Source: `/api/contacts/summary` → `google_sheets.get_contact_counts_by_university()`
- Data: Current NEW CONTACTS sheet counts
- Shows: Real-time database state
- Updates: Every 30 seconds

**Last Scrape Run (Historical):**
- Source: `/api/system-status` → SYSTEM_STATUS sheet
- Data: Most recent run from scraping history
- Shows: What happened in the last automated run
- Purpose: Historical tracking, not current state

### Recently Added Contacts Tab

**How contacts are displayed:**
1. Fetches all contacts (no status filter)
2. Sorts by Date Added descending (newest first)
3. Applies time filter if selected (30/60/90 days)
4. Displays with STATUS badge:
   - GREEN badge: NEW (newly discovered in a scrape)
   - GRAY badge: OLD (baseline/previously seen)

**Example display:**
```
Dr. John Smith [NEW]
University of Miami - Biochemistry
Added: 4/28/2026

Dr. Jane Doe [OLD]
University of Florida - Cell Biology
Added: 4/06/2026
```

---

## Testing Verification

### Test 1: Dashboard shows correct current counts

**Expected:**
- Current Database section shows:
  - Total: 2,458
  - NEW: 0 (or current count from sheets)
  - OLD: 2,458 (or current count)
  - Universities: 38

**How to verify:**
1. Check Google Sheets NEW CONTACTS tab
2. Count NEW vs OLD contacts
3. Compare with dashboard numbers
4. Should match exactly

### Test 2: "Last Scrape Run" is clearly historical

**Expected:**
- Section title says "Last Scrape Run" (not "Current")
- Shows timestamp of when run happened
- Says "X contacts added in that run" (not "X new faculty detected")
- Clear it's about a past event, not current state

### Test 3: Recently Added shows all recent contacts

**Expected:**
- Shows contacts sorted by Date Added (newest first)
- Includes both NEW and OLD contacts
- Each contact shows STATUS badge
- Time filters work (30/60/90 days, All Time)

**How to verify:**
1. Go to "Recently Added" tab
2. See list of contacts sorted by date
3. Each should show NEW or OLD badge
4. Click "Last 30 Days" - should show only contacts added in last 30 days
5. Click "All Time" - should show all contacts (up to 100 limit)

---

## Current Database State (as of fix)

**NEW CONTACTS Sheet:**
- Total rows: 2,458
- NEW contacts: 0
- OLD contacts: 2,458
- Universities: 38

**SYSTEM_STATUS Sheet (Last Run):**
- Timestamp: 2026-04-27 21:03:48 UTC
- Status: SUCCESS
- Directories scraped: 36
- Contacts added in that run: 1,120 (historical data)

**Explanation:**
The last scrape added 1,120 contacts, but those were marked as OLD (baseline) because it was the first scrape for those directories. The dashboard now clarifies this by showing:
- **Current Database:** 2,458 OLD, 0 NEW (live state)
- **Last Scrape Run:** 1,120 added (historical event)

---

## Files Modified

- `templates/index.html`
  - Added Current Database section (HTML)
  - Added `loadCurrentDatabaseStats()` function
  - Updated `loadSystemStatus()` display text
  - Updated `loadRecentContacts()` to remove status filter
  - Updated `renderRecentContacts()` to show status badges
  - Updated tab title and subtitle
  - Added loadCurrentDatabaseStats to auto-refresh

---

## Summary

✅ **Fixed:** Dashboard now shows CURRENT database state separate from historical run data
✅ **Fixed:** "Recently Added" tab shows all recent contacts (not just status=NEW)
✅ **Fixed:** Clear distinction between "Current Database" and "Last Scrape Run"
✅ **Fixed:** Status badges show whether contacts are NEW or OLD (baseline)
✅ **Result:** UI now accurately reflects Google Sheets data in real-time

**No more confusion between:**
- Historical run data (what happened in the past)
- Current database state (what's in the sheets right now)
