# FacultySnipe Utility Scripts

This directory contains utility scripts for managing the FacultySnipe system.

## Baseline Management Scripts

### 1. `convert_new_to_old_baseline.py` ⭐ **RUN THIS FIRST**

**Purpose:** Fix the current issue where contacts are marked as NEW when they should be OLD (baseline).

**What it does:**
1. Converts all NEW contacts to OLD in the NEW CONTACTS sheet
2. Marks all universities as `first_scrape_completed=TRUE`

**When to use:**
- **NOW** - to fix the current issue where 112+ contacts are showing as NEW when they should be OLD
- After a baseline reset if contacts were incorrectly marked as NEW

**How to run:**
```bash
python3 scripts/convert_new_to_old_baseline.py
```

**Example output:**
```
✅ Converted 112 contacts from NEW to OLD (baseline)
✅ Marked 36 universities as baseline complete
```

---

### 2. `reset_baseline.py`

**Purpose:** Completely reset the baseline for all universities (nuclear option).

**What it does:**
1. Backs up current NEW CONTACTS sheet
2. Creates fresh NEW CONTACTS sheet (empty)
3. Sets ALL universities to `first_scrape_completed=FALSE`
4. Next scrape will add all contacts as OLD (baseline)

**When to use:**
- When you want to start completely fresh
- When you want to re-establish baseline across all universities
- **NOT recommended** unless you really want to clear all contact history

**How to run:**
```bash
python3 scripts/reset_baseline.py
```

---

### 3. `add_first_scrape_column.py`

**Purpose:** One-time migration to add `first_scrape_completed` column to CONFIG sheet.

**When to use:**
- Only needed once when first implementing the baseline system
- **Already completed** - you don't need to run this again

**How to run:**
```bash
python3 scripts/add_first_scrape_column.py
```

---

### 4. `migrate_first_scrape_flag.py`

**Purpose:** Set all universities to `first_scrape_completed=TRUE`.

**When to use:**
- After initial deployment to mark existing universities as already baselined
- When you want to mark all universities as "baseline complete" without touching contacts
- **Already completed** - you don't need to run this again unless adding new baseline

**How to run:**
```bash
python3 scripts/migrate_first_scrape_flag.py
```

---

## Current Issue Fix

### Problem

Directory cards show "112 NEW" with "0 contacts", and clicking shows "No contacts found".

**Root causes:**
1. Contacts are marked as NEW when they should be OLD (baseline)
2. University name mismatch between CONFIG and NEW CONTACTS prevented display

### Solution

**Step 1:** Convert NEW contacts to OLD baseline

```bash
cd /Users/eddieflottemesch/Desktop/FacultySnipe
python3 scripts/convert_new_to_old_baseline.py
```

Type `yes` when prompted.

**Step 2:** Verify the fix

1. Refresh the web interface
2. Navigate to Browse Contacts → University of Miami → Biochemistry And Molecular Biology
3. You should now see:
   - Directory card shows "112 total contacts" (no NEW badge)
   - Clicking in shows all 112 contacts marked as OLD
   - Future scrapes will mark new discoveries as NEW

---

## How the Baseline System Works

### First Scrape (Baseline)

When a university is first scraped:
1. `first_scrape_completed` = FALSE in CONFIG
2. Scraper detects this is first scrape
3. ALL contacts are marked as OLD (baseline)
4. `first_scrape_completed` set to TRUE
5. No email notification sent (it's baseline)

### Subsequent Scrapes

After baseline is established:
1. `first_scrape_completed` = TRUE in CONFIG
2. Scraper detects this is NOT first scrape
3. Only NEW faculty are marked as NEW
4. Email notifications sent for NEW faculty

### Contact Status

- **OLD**: Part of baseline or previously seen
- **NEW**: Newly discovered since baseline

### Time Filters

Users can filter contacts by:
- Last 30 Days
- Last 60 Days
- Last 90 Days
- Since Added (all time) - default

This allows users to see recent contacts regardless of NEW/OLD status.

---

## Troubleshooting

### "No contacts found" when clicking directory

**Fix:** Run `convert_new_to_old_baseline.py` - this was caused by university name mismatch, now fixed in code.

### Contacts showing as NEW when they should be OLD

**Fix:** Run `convert_new_to_old_baseline.py` to convert them to baseline.

### Want to start completely fresh

**Fix:** Run `reset_baseline.py` - this will clear all contacts and re-establish baseline on next scrape.

---

## Script Execution Order

If you need to completely rebuild the baseline system:

```bash
# 1. (Optional) Add first_scrape_completed column if not exists
python3 scripts/add_first_scrape_column.py

# 2. Reset to fresh baseline
python3 scripts/reset_baseline.py

# 3. Wait for next scheduled scrape (Mon/Thu 8 PM UTC) or run manually
cd src && python3 main.py

# All contacts will be marked as OLD (baseline)
# Future scrapes will mark new discoveries as NEW
```

If you just need to fix the current NEW/OLD issue:

```bash
# Convert existing NEW contacts to OLD baseline
python3 scripts/convert_new_to_old_baseline.py
```
