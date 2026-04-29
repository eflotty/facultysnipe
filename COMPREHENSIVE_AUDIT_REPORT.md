# 🔍 Comprehensive UI ↔ Google Sheets Audit Report
**Date:** 2026-04-28
**System:** FacultySnipe

---

## Executive Summary

Conducted full system audit comparing Google Sheets data vs UI display and API responses. Found **7 critical issues** affecting data accuracy, university grouping, and user experience.

**Status:**
- ✅ 2,480 contacts in database (1 NEW, 2,479 OLD)
- ⚠️ 39 unique university names in NEW CONTACTS
- ⚠️ 37 universities in CONFIG
- ❌ Multiple naming/grouping inconsistencies
- ❌ Recently Added tab failing to load
- ❌ SYSTEM_STATUS tracking incomplete

---

## 🚨 Critical Issues Found

### Issue #1: University Naming Mismatch (HIGH PRIORITY)

**Problem:** CONFIG and NEW CONTACTS have different university name formats, breaking UI grouping.

**Evidence:**

**CONFIG format:**
```
Anatomic Pathology »  Department of Pathology... » University of Florida
```

**NEW CONTACTS format:**
```
Anatomic Pathology »  Department of Pathology... » University of Florida - Pathology
```

**Impact:**
- 10+ universities have orphaned contacts (contacts in NEW CONTACTS but no matching CONFIG entry)
- UI grouping breaks down because names don't match
- Browse Contacts shows mismatched data

**Affected Universities:**
1. `Faculty by Department »  College of Dentistry » University of Florida - Dental` (292 contacts) ❌ No CONFIG match
2. `Anatomic Pathology »  Department of Pathology... » University of Florida - Pathology` (73 contacts) ❌ No CONFIG match
3. `Experimental Pathology »  Department of Pathology... » University of Florida - Pathology` (47 contacts) ❌ No CONFIG match
4. `Faculty »  Center for NeuroGenetics » University of Florida - Neurogenetics` (54 contacts) ❌ No CONFIG match
5. `Faculty »  Department of Molecular Genetics & Microbiology » University of Florida - Faculty` (35 contacts) ❌ No CONFIG match
6. `Faculty »  Department of Physiology and Aging » University of Florida - Physiology` (88 contacts) ❌ No CONFIG match
7. `Meet the Team »  Division of Cardiovascular Medicine » University of Florida - Cardiology` (83 contacts) ❌ No CONFIG match
8. `Miami University - Biochemistry And Molecular Biology` (112 contacts) ❌ No CONFIG match
9. `Miami University - Cell Biology` (41 contacts) ❌ No CONFIG match
10. `Miami University - Dermatology` (93 contacts) ❌ No CONFIG match

**Total Orphaned Contacts:** 918 contacts (37% of database!)

**Root Cause:**
The scraper is appending department names (like `- Pathology`, `- Dental`) to university names when writing to NEW CONTACTS, but CONFIG doesn't have these suffixes.

**Location in Code:**
- `src/google_sheets.py` - `add_to_new_contacts()` method
- OR `src/main.py` - `_process_university()` method where enhanced_name is created

**Fix Required:**
- Standardize university naming across CONFIG and NEW CONTACTS
- Either: Remove suffixes from NEW CONTACTS, OR add suffixes to CONFIG
- Preferred: Use CONFIG university_name as-is without modification

---

### Issue #2: SYSTEM_STATUS "universities_processed" Always Shows 0 (MEDIUM PRIORITY)

**Problem:** SYSTEM_STATUS sheet shows `universities_processed: 0` for all recent scrape runs.

**Evidence:**
```
Run #18 (2026-04-27): Universities: 0, New Faculty: 1120 ❌
Run #19 (2026-04-23): Universities: 0, New Faculty: 1286 ❌
Run #20 (2026-04-20): Universities: 0, New Faculty: 1292 ❌
Run #21 (2026-04-16): Universities: 0, New Faculty: 1005 ❌
Run #22 (2026-04-13): Universities: 0, New Faculty: 1179 ❌
```

**Expected:** Should show 36 (number of enabled universities scraped)

**Impact:**
- Dashboard shows misleading "0 directories scraped" message
- Unable to track scraping coverage
- Can't verify all universities were processed

**Root Cause:**
`src/main.py` is not correctly incrementing or writing the universities_processed counter to SYSTEM_STATUS sheet.

**Location in Code:**
- `src/main.py` - `run()` method where SYSTEM_STATUS is updated
- Look for `log_run_to_system_status()` or similar

**Fix Required:**
- Add counter for successfully processed universities
- Write accurate count to SYSTEM_STATUS sheet

---

### Issue #3: Recently Added Tab Fails to Load (CRITICAL - USER REPORTED)

**Problem:** User reports "most recent new failed to load for all time lengths (30/60/90 days, all time buttons)"

**Status:** ⚠️ Needs investigation

**What I Found:**
- JavaScript code looks correct (`loadRecentContacts()` function exists)
- `switchTab('recent')` calls `loadRecentContacts(90)` correctly
- API endpoint `/api/contacts?limit=100` returns data correctly locally
- Time filter buttons have onclick handlers

**Possible Causes:**
1. API endpoint not working on Render deployment
2. CORS issue
3. JavaScript error in browser console
4. Render service not fully deployed yet

**Next Steps:**
1. Check browser console for errors
2. Verify `/api/contacts` endpoint is accessible on Render
3. Test with: `curl https://facultysnipe.onrender.com/api/contacts?limit=10`

---

### Issue #4: Duplicate Contacts in Database (MEDIUM PRIORITY)

**Problem:** Same person appears multiple times with different faculty_ids.

**Evidence:**
```
Name: Alexandria B Marciante
Faculty ID 1: 6df0a44890455d2e
Faculty ID 2: 46e9db935c8f559c
Both: University of Florida - Neuroscience, same email (amarciante@phhp.ufl.edu)
```

**Impact:**
- Inflated contact counts
- Duplicate emails sent to sales reps
- Confusing for users browsing contacts

**Root Cause:**
Faculty ID hashing algorithm creates different hashes for same person when:
- Title changes
- Name formatting changes (with/without middle initial)
- Profile is listed on multiple department pages

**Current Hashing:**
```python
faculty_id = hash(name + email + title)
```

**Issue:** Title can change, creating new ID for same person.

**Fix Required:**
- Change hashing to use only stable identifiers: `hash(name + email)`
- OR: Use email as primary key (if always present)
- Add deduplication check before inserting

**Location in Code:**
- `src/scrapers/` - wherever `faculty_id` is generated
- Check `universal_scraper.py`, `dynamic_scraper.py`, `ai_scraper.py`

---

### Issue #5: Stanford University Has Empty "Enabled" Field (LOW PRIORITY)

**Problem:** Row 2 in CONFIG (stanford_biology) has empty "enabled" column.

**Evidence:**
```
Row 2: stanford_biology | Stanford - Biology | Enabled: [EMPTY]
```

**Expected:** Should be `TRUE` or `FALSE`

**Impact:**
- Unclear if Stanford should be scraped
- May cause scraper to skip it or error out
- Inconsistent with other CONFIG rows

**Fix Required:**
- Manually update CONFIG sheet Row 2, Column E to `TRUE` or `FALSE`
- Add validation in `auto_fill_config_rows()` to never leave enabled empty

---

### Issue #6: Contact Count Discrepancy (LOW PRIORITY)

**Problem:** Slight mismatch between reported and actual contact counts.

**Evidence:**
- Google Sheets NEW CONTACTS: **2,480 rows** (excluding header)
- UI previously showed: **2,458 contacts**
- Difference: **22 contacts**

**Possible Causes:**
1. Empty rows in Google Sheets
2. API filtering out contacts with missing fields
3. Contacts with malformed data
4. Counting logic difference

**Investigation Needed:**
- Check if any rows have missing Name or Faculty ID
- Verify API `get_contacts_from_new_contacts_sheet()` filtering logic

---

### Issue #7: Universities in CONFIG with No Contacts (MEDIUM PRIORITY)

**Problem:** 13 universities in CONFIG have zero contacts in NEW CONTACTS.

**Evidence:**
```
Universities with 0 contacts:
1. Our Faculty »  Division of Infectious Diseases & Global Medicine » University of Florida
2. Primary Faculty »  Department of Neuroscience » University of Florida
3. Primary Faculty »  Department of Pharmacology & Therapeutics » University of Florida
4. Research Faculty »  Lillian S. Wells Department of Neurosurgery » University of Florida
5. Ufl University
6. University of Florida, Institute of Food and Agricultural Sciences
... (7 more)
```

**Impact:**
- CONFIG expects these to have contacts but they don't
- Either scraping failed, or university names don't match (see Issue #1)
- Wasted scraping cycles on directories that yield no contacts

**Root Cause:**
Likely related to Issue #1 (naming mismatch). These universities may have contacts under different names.

**Example:**
- CONFIG: `Research Faculty »  Lillian S. Wells Department of Neurosurgery » University of Florida`
- NEW CONTACTS: `Research Faculty »  Lillian S. Wells Department of Neurosurgery » University of Florida - Neurosurgery`

**Fix Required:**
- Resolve naming mismatch from Issue #1
- Verify these universities actually have faculty on their websites
- Disable in CONFIG if they're empty directories

---

## 📊 Data Quality Summary

### Google Sheets State
```
NEW CONTACTS Sheet:
├─ Total Rows: 2,480
├─ NEW Status: 1
├─ OLD Status: 2,479
├─ Empty Status: 0
├─ Duplicate Faculty IDs: 0 (but duplicates exist with different IDs)
├─ Missing Name: 0
├─ Missing University: 0
└─ Missing Faculty ID: 0

CONFIG Sheet:
├─ Total Universities: 37
├─ Enabled: 35 (1 empty, 1 assumed enabled)
├─ Disabled: 0
├─ First Scrape Completed: 37 (100% ✅)
└─ Empty "enabled" field: 1 (stanford_biology)

SYSTEM_STATUS Sheet:
├─ Total Runs: 22
├─ Last Run: 2026-04-27 21:03:48
├─ Status: SUCCESS
├─ Universities Processed: 0 ❌ (INCORRECT)
└─ New Faculty: 1120
```

### The 1 NEW Contact
```
Name: Chris Geiger
Title: Instructional Associate Professor & Associate Chair for Undergraduate Studies
University: Ufl University - Bme
Email: cgeiger@bme.ufl.edu
Date Added: 2026-04-27 21:02:39
Status: NEW ✅
```

This is correct! This was discovered in the most recent scrape (4/27) and properly marked NEW.

---

## 🔧 Recommended Fixes (Priority Order)

### 1. Fix University Naming Mismatch (Issue #1) - HIGH PRIORITY

**Goal:** Standardize university names between CONFIG and NEW CONTACTS.

**Approach A (Recommended):**
- Modify scraper to use CONFIG `university_name` exactly as-is
- Don't append department suffixes when writing to NEW CONTACTS
- Ensures CONFIG and NEW CONTACTS always match

**Approach B:**
- Update CONFIG to include department suffixes
- Requires manual editing of 37 CONFIG rows
- More error-prone

**Implementation:**
1. Locate where enhanced_name is created in `src/main.py`
2. Change from: `enhanced_name = f"{university_name} - {department}"`
3. Change to: `enhanced_name = university_name`
4. OR use CONFIG university_name directly without modification

**Testing:**
- Add new university and verify CONFIG name matches NEW CONTACTS entry
- Check Browse Contacts grouping works correctly

---

### 2. Fix "Recently Added" Tab (Issue #3) - CRITICAL

**Immediate Actions:**
1. Check browser console when clicking "Recently Added" tab
2. Test API endpoint: `curl https://facultysnipe.onrender.com/api/contacts?limit=10`
3. Verify Render deployment completed successfully

**If API works:**
- JavaScript error in browser console
- Fix frontend code

**If API fails:**
- Render deployment issue
- Check Render logs for errors

---

### 3. Fix SYSTEM_STATUS universities_processed (Issue #2) - MEDIUM

**Goal:** Accurately track how many universities were processed in each run.

**Implementation:**
1. Find `run()` method in `src/main.py`
2. Add counter: `universities_processed = 0`
3. Increment for each successful university scrape
4. Write to SYSTEM_STATUS: `universities_processed` column

**Testing:**
- Run manual scrape: `python3 src/main.py`
- Check SYSTEM_STATUS shows correct count (should be 36)

---

### 4. Add Deduplication Check (Issue #4) - MEDIUM

**Goal:** Prevent same person from being added multiple times.

**Options:**

**Option A:** Change faculty_id hashing
```python
# OLD: faculty_id = hash(name + email + title)
# NEW: faculty_id = hash(name + email)  # Title can change
```

**Option B:** Use email as primary key
```python
# Check if email already exists before inserting
existing_ids = {row[4]: row[9] for row in NEW CONTACTS if row[4].strip()}
if email in existing_ids:
    skip or update existing entry
```

**Recommendation:** Option B is safer (emails are unique, names can have variations)

---

### 5. Fix Stanford "enabled" Field (Issue #5) - LOW

**Quick Fix:**
1. Open Google Sheets CONFIG
2. Row 2 (stanford_biology), Column E
3. Set to `TRUE`

**Code Fix:**
In `auto_fill_config_rows()`, ensure enabled is never left empty:
```python
if not row[4]:  # If enabled is empty
    row[4] = 'TRUE'  # Default to enabled
```

---

### 6. Investigate Contact Count Discrepancy (Issue #6) - LOW

**Steps:**
1. Check for empty rows in NEW CONTACTS sheet
2. Review API filtering logic in `get_contacts_from_new_contacts_sheet()`
3. Verify all 2,480 rows have required fields

---

### 7. Resolve Empty Universities (Issue #7) - MEDIUM

**After fixing Issue #1:**
- Re-check which universities have 0 contacts
- Manually verify if their websites have faculty listings
- Disable in CONFIG if they're truly empty

---

## 🧪 Testing Checklist

After implementing fixes:

### Test 1: University Naming Consistency
- [ ] Add a new university to CONFIG
- [ ] Run scraper
- [ ] Verify NEW CONTACTS entry has exact same university name as CONFIG
- [ ] Check Browse Contacts shows correct grouping

### Test 2: Recently Added Tab
- [ ] Click "Recently Added" tab
- [ ] Verify contacts load (no "Failed to load" error)
- [ ] Click "Last 30 Days" - should filter correctly
- [ ] Click "All Time" - should show all recent contacts
- [ ] Verify status badges show (NEW/OLD)

### Test 3: SYSTEM_STATUS Tracking
- [ ] Run manual scrape: `python3 src/main.py`
- [ ] Check SYSTEM_STATUS sheet
- [ ] Verify `universities_processed` shows correct count (36)
- [ ] Verify `new_faculty` count is accurate

### Test 4: No Duplicates
- [ ] Run scraper twice on same university
- [ ] Verify no duplicate contacts created
- [ ] Check same email doesn't appear multiple times with different faculty_ids

### Test 5: Browse Contacts Grouping
- [ ] Open Browse Contacts tab
- [ ] Verify all universities show correct contact counts
- [ ] Click into a university - verify all directories visible
- [ ] Click into a directory - verify all contacts load
- [ ] Verify no "Failed to load" or "No contacts found" errors on directories that should have contacts

### Test 6: Current Database Stats
- [ ] Check dashboard "Current Database" section
- [ ] Verify numbers match Google Sheets:
  - Total Contacts
  - NEW count
  - OLD count
  - Universities count

---

## 📈 Expected State After Fixes

### Google Sheets
```
NEW CONTACTS:
├─ All university names match CONFIG exactly ✅
├─ No duplicate contacts (same email = same faculty_id) ✅
└─ All contacts have proper status (NEW/OLD) ✅

CONFIG:
├─ All universities have "enabled" = TRUE or FALSE ✅
├─ All enabled universities have matching contacts in NEW CONTACTS ✅
└─ first_scrape_completed = TRUE for all established universities ✅

SYSTEM_STATUS:
├─ universities_processed shows accurate count (36) ✅
├─ new_faculty count is accurate ✅
└─ All runs properly tracked ✅
```

### UI
```
Dashboard:
├─ Current Database shows accurate live counts ✅
└─ Last Scrape Run shows correct universities_processed ✅

Browse Contacts:
├─ All universities group correctly ✅
├─ All directories show correct contact counts ✅
└─ No orphaned contacts ✅

Recently Added:
├─ Loads successfully (no errors) ✅
├─ Shows recent contacts sorted by date ✅
├─ Time filters work (30/60/90 days, All Time) ✅
└─ Status badges show correctly (NEW/OLD) ✅
```

---

## 🚀 Implementation Plan

### Phase 1: Critical Fixes (Do First)
1. Fix Recently Added tab (Issue #3) - USER REPORTED
2. Fix university naming mismatch (Issue #1) - BREAKS GROUPING

### Phase 2: Data Quality (Do Second)
3. Fix SYSTEM_STATUS universities_processed (Issue #2)
4. Add deduplication check (Issue #4)
5. Fix Stanford enabled field (Issue #5)

### Phase 3: Cleanup (Do Third)
6. Investigate contact count discrepancy (Issue #6)
7. Resolve empty universities (Issue #7)

---

## 📝 Files Requiring Changes

**High Priority:**
- `src/main.py` - Fix university naming, universities_processed counter
- `src/google_sheets.py` - Possibly modify add_to_new_contacts()
- `templates/index.html` - Debug Recently Added tab (if needed)

**Medium Priority:**
- `src/scrapers/universal_scraper.py` - Change faculty_id hashing
- `src/scrapers/dynamic_scraper.py` - Change faculty_id hashing
- `src/scrapers/ai_scraper.py` - Change faculty_id hashing
- `src/google_sheets.py` - Add deduplication logic

**Manual Tasks:**
- Google Sheets CONFIG: Fix Row 2 (stanford_biology) enabled field
- Test Render deployment

---

## Summary

**Found 7 issues:**
1. ❌ University naming mismatch (918 orphaned contacts - 37% of database!)
2. ❌ SYSTEM_STATUS universities_processed always 0
3. ❌ Recently Added tab fails to load (user reported)
4. ⚠️ Duplicate contacts with different faculty_ids
5. ⚠️ Stanford has empty "enabled" field
6. ⚠️ Contact count discrepancy (2480 vs 2458)
7. ⚠️ 13 universities in CONFIG with 0 contacts

**Most Critical:**
- Issue #1 (naming mismatch) affects 37% of database
- Issue #3 (Recently Added tab) breaks user experience

**Baseline System Status:** ✅ Working correctly
- All universities have first_scrape_completed = TRUE
- NEW/OLD status marking works correctly (1 NEW found in recent scrape)

**Next Actions:**
1. Debug Recently Added tab (check browser console)
2. Fix university naming mismatch in scraper code
3. Add universities_processed counter to scraper
4. Test all fixes thoroughly
