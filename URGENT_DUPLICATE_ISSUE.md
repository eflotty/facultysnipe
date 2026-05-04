# 🚨 URGENT: Duplicate Contact Issue - Action Required

**Status:** CRITICAL - Immediate cleanup needed
**Your Dashboard Shows:** 4,373 total contacts (should be ~2,480)
**Problem:** ~1,893 duplicate contacts added on April 30 scrape

---

## 🔍 What You're Seeing

Your dashboard shows:
```
Total Contacts: 4,373  ⚠️  WRONG
NEW: 1,893            ⚠️  WRONG (inflated by duplicates)
OLD: 2,480            ✅  CORRECT (this is the real baseline)
```

**Last Scrape Run:**
- "2079 contacts added in that run" ← These are DUPLICATES, not real new hires

---

## ❓ What Happened

The **sheet lookup bug** I just fixed caused this on April 30:

1. System tried to find existing faculty in university sheets
2. Lookup FAILED (tried wrong sheet name)
3. Returned empty list `{}`
4. System thought everyone was "new"
5. Added 2,079 people AGAIN to NEW CONTACTS (duplicates!)

**Real numbers:**
- Actual unique faculty: ~2,480
- Duplicate entries: ~1,893
- Total rows: 4,373

---

## ✅ What's Fixed

I just deployed fixes that prevent this from happening again:

1. **Sheet lookup fix** - Now tries `university_id` first (primary key)
2. **Email deduplication** - Prevents people listed twice
3. **Variable scope fix** - Prevents crashes

**Next scrape (May 6) will NOT create duplicates.**

---

## ⚠️ But Existing Duplicates Need Cleanup

The code fix prevents FUTURE duplicates, but doesn't clean up EXISTING ones.

**You need to:**
1. Run deduplication script
2. Remove ~1,893 duplicate rows
3. Restore correct count of ~2,480

---

## 🔧 How to Fix (2 Steps)

### Step 1: Check What Will Be Removed (Safe - Dry Run)

```bash
python3 scripts/deduplicate_contacts.py
```

This will show:
- How many duplicates found
- Which faculty members appear multiple times
- What will be removed (but doesn't delete anything yet)

**Expected output:**
```
Total rows in NEW CONTACTS: 4,373
Unique faculty members: 2,480
Faculty members with duplicates: 1,893
Total duplicate rows to remove: 1,893

DRY RUN MODE - No changes made
```

### Step 2: Remove Duplicates (After Reviewing)

If Step 1 looks correct, execute cleanup:

```bash
python3 scripts/deduplicate_contacts.py --execute
```

Type `yes` to confirm.

**This will:**
- Delete ~1,893 duplicate rows
- Keep earliest entry for each person
- Reduce total to ~2,480 (correct count)

---

## 📊 Before & After

### Before Cleanup (Now)
```
Total: 4,373
NEW: 1,893 (duplicates)
OLD: 2,480
```

### After Cleanup (Target)
```
Total: ~2,480 ✅
NEW: 0 (or small number)
OLD: ~2,480 ✅
```

---

## 🎯 Why This Is Safe

The script:
- ✅ Runs in dry-run mode by default (shows what it will do)
- ✅ Asks for confirmation before deleting
- ✅ Keeps the EARLIEST entry (preserves original data)
- ✅ Only removes EXACT duplicates (same faculty_id)
- ✅ Doesn't touch individual university sheets

**Recommendation:** Make a backup copy of NEW CONTACTS sheet before running.

---

## 📝 Summary

**The Bug:** Sheet lookup failed → everyone marked as "new" → 2,079 duplicates added April 30

**The Fix (Done):** Code deployed that prevents future duplicates

**The Cleanup (You):** Run deduplication script to remove existing ~1,893 duplicates

**Timeline:**
- ✅ NOW: Code fixed and deployed
- 👉 NEXT: Run deduplication script (you)
- ✅ MAY 6: Next scrape will NOT create duplicates

---

## 🚀 Quick Start

```bash
# 1. See what will be removed (safe, no changes)
python3 scripts/deduplicate_contacts.py

# 2. If it looks good, execute cleanup
python3 scripts/deduplicate_contacts.py --execute

# 3. Refresh your dashboard - should show ~2,480 total
```

**Full details:** See `DUPLICATE_CLEANUP_GUIDE.md`

---

## ❓ Questions

**Q: Will this delete real data?**
A: No - it only removes DUPLICATE entries (same faculty_id appearing multiple times). Keeps the earliest entry for each person.

**Q: What if I don't run cleanup?**
A: The duplicates stay in the database, inflating your counts. Future scrapes won't add MORE duplicates (that's fixed), but the existing ~1,893 will remain.

**Q: Can I undo this?**
A: Make a backup copy of the NEW CONTACTS sheet first (File → Make a copy). Then you can restore if needed.

**Q: How long does cleanup take?**
A: ~2-5 minutes to delete 1,893 rows via Google Sheets API.

**Q: Will emails be affected?**
A: No - the email bug is FIXED. Next scrape will send correct emails (only actual new contacts, no duplicates).

---

**Action Required:** Run deduplication script to clean up existing duplicates!
