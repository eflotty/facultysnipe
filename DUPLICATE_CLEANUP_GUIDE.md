# 🚨 CRITICAL: Duplicate Contacts Cleanup Guide

**Date:** 2026-05-03
**Issue:** April 30 scrape run added 2,079 duplicate contacts
**Status:** Root cause FIXED, cleanup REQUIRED

---

## 🔍 The Problem

**What Happened:**
- April 30, 2026 scrape run added 2,079 contacts as "new"
- These are **NOT** actually new - they're duplicates
- Total contacts now: **4,373** (should be ~2,480)
- NEW count: **1,893** (should be 0-10)
- Duplicates: **~1,893 entries**

**Root Cause:**
The sheet lookup bug (now FIXED) caused `get_existing_faculty()` to fail, returning empty `{}`. This made the system think everyone was "new" on every scrape, adding duplicates.

**Why This Happened:**
- Sheet lookup tried `university_name` first instead of `university_id`
- After university naming migration, sheet names didn't match lookup
- Lookup failed → no existing faculty found → everyone marked as "new"
- 2,079 contacts added to NEW CONTACTS (duplicates of baseline)

---

## ✅ What's Already Fixed

**Code Fix (Deployed):**
- ✅ Sheet lookup now tries `university_id` FIRST (primary key)
- ✅ Variable scope fix (is_first)
- ✅ Email deduplication logic
- ✅ This will prevent NEW duplicates from being created

**Impact:**
- Next scrape (May 6) will NOT create duplicates
- Sheet lookups will succeed
- Only actual new contacts will be marked as "new"

---

## ⚠️ What Needs Cleanup

**Existing Duplicates:**
- ~1,893 duplicate rows in NEW CONTACTS sheet
- Added on April 30, 2026 scrape run
- Same faculty_id appearing multiple times
- Inflating "NEW" count and total contacts

**Evidence:**
```
Current Database:
- Total Contacts: 4,373 (WRONG - should be ~2,480)
- NEW: 1,893 (WRONG - should be 0-10)
- OLD: 2,480 (CORRECT - this is the baseline)

Last Scrape Run:
- 2079 contacts added (these are DUPLICATES)
```

---

## 🔧 Cleanup Steps

### Step 1: Analyze Duplicates (DRY RUN)

Run the deduplication script in dry-run mode to see what would be removed:

```bash
python3 scripts/deduplicate_contacts.py
```

**Expected Output:**
```
DUPLICATE DETECTION REPORT
==================================================
Total rows in NEW CONTACTS: 4,373
Unique faculty members: 2,480
Faculty members with duplicates: 1,893
Total duplicate rows to remove: 1,893

Top 20 most duplicated faculty members:
Dr. John Doe - 2 entries (keeping row 123, removing 1)
Dr. Jane Smith - 2 entries (keeping row 456, removing 1)
...

DRY RUN MODE - No changes made
Would remove 1,893 duplicate rows
```

### Step 2: Review the Analysis

**Check:**
- Does the number of duplicates match expectations (~1,893)?
- Are the duplicate faculty_ids reasonable?
- Is the script keeping the EARLIEST entry for each person?

**Red Flags:**
- If "Would remove" is close to total rows (4,373) → STOP, something's wrong
- If unique faculty is very low → STOP, investigate further
- If top duplicated show 10+ entries → unusual, investigate

### Step 3: Execute Cleanup

If the dry-run looks correct, execute the cleanup:

```bash
python3 scripts/deduplicate_contacts.py --execute
```

**This will:**
- Permanently delete duplicate rows
- Keep only the EARLIEST entry for each faculty_id
- Update the sheet to have ~2,480 unique contacts

**Confirmation Prompt:**
```
⚠️  WARNING: This will PERMANENTLY DELETE duplicate rows!
Are you sure you want to continue? (yes/no): yes
```

**Expected Output:**
```
🔧 EXECUTING REMOVAL...
Deleting 1,893 rows...
  Deleted 10/1,893 rows...
  Deleted 20/1,893 rows...
  ...

✅ DEDUPLICATION COMPLETE
   Removed 1,893 duplicate rows
   Remaining unique contacts: 2,480
```

### Step 4: Verify Results

After cleanup, check the dashboard:

**Expected:**
```
Current Database:
- Total Contacts: ~2,480 ✅
- NEW: 0 ✅ (or small number if actual new contacts exist)
- OLD: ~2,480 ✅
```

**How to Verify:**
1. Refresh the FacultySnipe dashboard
2. Check "Current Database" section
3. Total should be ~2,480 (not 4,373)
4. NEW should be 0 or very small
5. OLD should match total

### Step 5: Verify Individual University Sheets

Check if individual university sheets also have duplicates:

```bash
# List all sheets
python3 -c "
import sys; sys.path.insert(0, 'src')
from google_sheets import GoogleSheetsManager
sheets = GoogleSheetsManager()
for sheet in sheets.spreadsheet.worksheets():
    print(sheet.title, sheet.row_count)
"
```

**Look for:**
- Sheets with unusually high row counts
- Duplicate entries for same faculty_id

**If duplicates found in individual sheets:**
These should NOT exist (individual sheets get overwritten on each scrape), but if found:
1. Check when they were last updated
2. Consider re-running scrape for that university
3. Or manually review and clean

---

## 🧪 Testing After Cleanup

### Test 1: Dashboard Shows Correct Counts

**Before Cleanup:**
- Total: 4,373
- NEW: 1,893
- OLD: 2,480

**After Cleanup:**
- Total: ~2,480 ✅
- NEW: 0 (or small number) ✅
- OLD: ~2,480 ✅

### Test 2: Browse Contacts Works

1. Go to "Browse Contacts" tab
2. Click on a university
3. Verify count matches expected
4. Check for duplicate names in list

### Test 3: No Duplicate Faculty IDs

Run verification query:

```python
python3 -c "
import sys; sys.path.insert(0, 'src')
from google_sheets import GoogleSheetsManager
sheets = GoogleSheetsManager()
contacts_sheet = sheets.spreadsheet.worksheet('NEW CONTACTS')
records = contacts_sheet.get_all_records()

faculty_ids = [r['Faculty ID'] for r in records if r.get('Faculty ID')]
unique_ids = set(faculty_ids)

print(f'Total rows: {len(records)}')
print(f'Unique faculty IDs: {len(unique_ids)}')
print(f'Duplicates: {len(faculty_ids) - len(unique_ids)}')

if len(faculty_ids) == len(unique_ids):
    print('✅ No duplicates!')
else:
    print(f'❌ Still {len(faculty_ids) - len(unique_ids)} duplicates')
"
```

### Test 4: Next Scrape Doesn't Create Duplicates

Wait for next scheduled scrape (May 6, 01:00 AM UTC):

**Expected:**
- 0-10 new contacts (actual new hires)
- No massive spike (not 2,000+)
- Logs show "Loaded X existing faculty from 'sheet_name'"
- No "Sheet not found" errors

---

## 📊 Timeline & Impact

### April 30, 2026 (BUG OCCURRED)
- Scrape run with sheet lookup bug
- 2,079 contacts added as duplicates
- Total inflated to 4,373
- NEW count inflated to 1,893

### May 3, 2026 (BUG FIXED)
- Sheet lookup bug fixed (commit `8043c96`)
- Email deduplication added
- Code deployed to production
- **Future scrapes will NOT create duplicates**

### May 3, 2026 (CLEANUP NEEDED)
- Run deduplication script
- Remove ~1,893 duplicate rows
- Restore correct counts (~2,480 total)

### May 6, 2026 (VERIFICATION)
- Next scheduled scrape runs
- Should add 0-10 new contacts (actual new hires)
- Email notifications should be correct
- No duplicates created

---

## 🎯 Expected Results

### Before Cleanup (Current State)
```
NEW CONTACTS sheet:
- Total rows: 4,373
- Unique faculty: ~2,480
- Duplicates: ~1,893
- NEW status: 1,893
- OLD status: 2,480
```

### After Cleanup (Target State)
```
NEW CONTACTS sheet:
- Total rows: ~2,480
- Unique faculty: ~2,480
- Duplicates: 0
- NEW status: 0 (or small number)
- OLD status: ~2,480
```

### After Next Scrape (May 6)
```
NEW CONTACTS sheet:
- Total rows: ~2,480 + (0-10 actual new hires)
- Unique faculty: ~2,480 + (0-10)
- Duplicates: 0
- NEW status: 0-10 (only actual new hires)
- OLD status: ~2,480
```

---

## ⚠️ Important Notes

### What the Deduplication Script Does
- ✅ Identifies duplicate faculty_ids in NEW CONTACTS
- ✅ Keeps the EARLIEST entry for each person
- ✅ Deletes all later duplicate entries
- ✅ Preserves all unique contacts

### What It Does NOT Do
- ❌ Does NOT modify individual university sheets
- ❌ Does NOT change STATUS (NEW/OLD) of kept entries
- ❌ Does NOT merge data between duplicates
- ❌ Does NOT affect CONFIG sheet

### Safety Features
- Dry-run mode by default (no changes unless --execute)
- Confirmation prompt before deleting
- Detailed report of what will be removed
- Deletes from bottom to top (avoids index shifting)

### Backup Recommendation
Before running cleanup:
1. Go to Google Sheets
2. File → Make a copy
3. Name it "NEW CONTACTS - Backup 2026-05-03"
4. Then run deduplication script

---

## 🚀 Quick Command Summary

```bash
# 1. Check for duplicates (dry-run)
python3 scripts/deduplicate_contacts.py

# 2. If looks good, execute cleanup
python3 scripts/deduplicate_contacts.py --execute

# 3. Verify results
python3 -c "
import sys; sys.path.insert(0, 'src')
from google_sheets import GoogleSheetsManager
s = GoogleSheetsManager()
c = s.spreadsheet.worksheet('NEW CONTACTS')
r = c.get_all_records()
ids = [x['Faculty ID'] for x in r if x.get('Faculty ID')]
print(f'Total: {len(r)}, Unique: {len(set(ids))}, Duplicates: {len(ids)-len(set(ids))}')
"
```

---

## 📞 Support

If you see unexpected results:

**Stop and investigate if:**
- Deduplication would remove > 2,000 rows (should be ~1,893)
- Unique faculty count is very low (should be ~2,480)
- Top duplicates show 10+ entries per person
- Any faculty member with unusual duplicate patterns

**Report:**
- Screenshot of dry-run output
- Current dashboard screenshot
- Any error messages

---

## Summary

**Problem:** April 30 scrape added 2,079 duplicates due to sheet lookup bug
**Root Cause:** Sheet lookup failed → everyone marked as "new"
**Fix Status:** Code fixed (deployed), cleanup REQUIRED
**Action:** Run deduplication script to remove ~1,893 duplicate rows
**Timeline:** Run cleanup now, verify after May 6 scrape

The code fix prevents FUTURE duplicates. The cleanup removes EXISTING duplicates.
