# CONFIG Sheet Field Guide

## Quick Reference for Adding Universities

| Column | Field Name | Required? | What to Enter | Examples |
|--------|------------|-----------|---------------|----------|
| **A** | `university_id` | ✅ YES | Short, unique identifier (lowercase, underscores only) | `miami_microbio`<br>`stanford_bio`<br>`uf_biochem` |
| **B** | `university_name` | ✅ YES | Display name for emails and reports | `Miami - Microbiology`<br>`Stanford - Biology`<br>`UF - Biochemistry` |
| **C** | `scraper_class` | ✅ YES | Python class name (exact match required) | `MiamiMicrobiologyScraper`<br>`StanfordBiologyScraper`<br>`UFBiochemScraper` |
| **D** | `url` | ✅ YES | Full URL to the faculty page | `https://med.miami.edu/departments/microbiology-and-immunology/faculty-and-staff` |
| **E** | `enabled` | ✅ YES | Turn monitoring on/off | `TRUE` = monitoring active<br>`FALSE` = skip this university |
| **F** | `scraper_type` | ✅ YES | Type of scraper to use | `static` = fast (most sites)<br>`dynamic` = Playwright (JavaScript sites) |
| **G** | `sales_rep_email` | ✅ YES | Who receives notifications | `rep@company.com`<br>`yourname@gmail.com` |
| **H** | `last_run` | ⚙️ AUTO | System fills this automatically | `2026-02-04 10:30:00` |
| **I** | `last_status` | ⚙️ AUTO | System fills this automatically | `SUCCESS`<br>`FAILED`<br>`SKIPPED` |
| **J** | `notes` | ❌ OPTIONAL | Your notes/comments | `Test university`<br>`Needs review`<br>`Production ready` |

---

## Column Details

### A - university_id
**What:** Unique identifier for the university/department
**Rules:**
- Must be unique (no duplicates)
- Lowercase letters only
- Use underscores (_) instead of spaces
- No special characters
- Short and descriptive

**Good:** `miami_microbio`, `stanford_chemistry`, `uf_biology`
**Bad:** `Miami Micro`, `stanford-chem`, `UF Bio!`

---

### B - university_name
**What:** Human-readable name shown in emails and reports
**Rules:**
- Can include spaces, capitals, hyphens
- Format: `University - Department`
- Clear and professional

**Examples:**
- `Miami - Microbiology`
- `Stanford - Chemistry`
- `Harvard Medical School - Neuroscience`

---

### C - scraper_class
**What:** Name of the Python scraper class (must match exactly!)
**Rules:**
- Must match the class name in `src/universities/your_file.py`
- Case-sensitive (capital letters matter!)
- No spaces
- Ask developer for correct name

**Examples:**
- `MiamiMicrobiologyScraper`
- `StanfordChemistryScraper`
- `UFBiochemScraper`

**Important:** Leave blank if scraper isn't built yet. Set `enabled` to `FALSE`.

---

### D - url
**What:** Web address of the faculty listing page
**Rules:**
- Must be full URL starting with `https://`
- Should be the main faculty directory page
- Test the URL in your browser first

**Examples:**
- `https://med.miami.edu/departments/microbiology-and-immunology/faculty-and-staff`
- `https://biology.stanford.edu/people/faculty`

---

### E - enabled
**What:** Controls whether this university is monitored
**Rules:**
- Only two values allowed: `TRUE` or `FALSE`
- Must be ALL CAPS
- Use `FALSE` while testing or if scraper isn't ready

**When to use TRUE:**
- Scraper is built and tested
- Ready for production monitoring

**When to use FALSE:**
- Scraper not built yet
- Testing in progress
- Temporarily disable monitoring

---

### F - scraper_type
**What:** Which scraping method to use
**Rules:**
- Only two values: `static` or `dynamic`
- Must be lowercase

**Use `static` when:**
- Page loads instantly
- You can see faculty names in "View Source"
- No loading spinners or "Loading..." text
- Most university sites (90%)

**Use `dynamic` when:**
- Page has loading animations
- Content loads after page appears
- Built with React/Vue/Angular
- "View Source" shows mostly empty divs

**Not sure?** Start with `static` - it's faster and works for most sites.

---

### G - sales_rep_email
**What:** Email address to receive new faculty notifications
**Rules:**
- Must be valid email address
- Can be same email for multiple universities
- Notifications only sent when new faculty detected

**Examples:**
- `john.smith@company.com`
- `sales.team@company.com`
- Multiple universities can share one email

---

### H - last_run
**What:** Timestamp of last successful check
**Auto-filled:** System updates this automatically
**Format:** `YYYY-MM-DD HH:MM:SS`

**Do not edit manually!**

---

### I - last_status
**What:** Result of last check
**Auto-filled:** System updates this automatically
**Values:**
- `SUCCESS` - Scraper ran successfully
- `FAILED` - Error occurred (check logs)
- `SKIPPED` - University disabled or error in config

**Do not edit manually!**

---

### J - notes
**What:** Optional notes for your reference
**Rules:**
- Any text you want
- Not used by system
- Good for tracking status

**Examples:**
- `Test university - remove after testing`
- `Production ready - high priority`
- `Contact: Dr. Smith for questions`
- `Review scraper monthly`

---

## Adding a New University - Quick Checklist

1. ✅ Get faculty page URL
2. ✅ Choose unique `university_id`
3. ✅ Enter `university_name` for emails
4. ✅ Set `enabled` to `FALSE` (until scraper ready)
5. ✅ Choose `static` or `dynamic` scraper type
6. ✅ Enter `sales_rep_email`
7. ✅ Leave `scraper_class` blank initially
8. ✅ Add notes about status
9. ✅ Notify developer to build scraper
10. ✅ After testing, set `enabled` to `TRUE`

---

## Example Rows

### Production Ready
```
miami_microbio | Miami - Microbiology | MiamiMicrobiologyScraper | https://med.miami.edu/... | TRUE | static | rep1@company.com | 2026-02-04 10:30:00 | SUCCESS | Production
```

### In Development
```
stanford_bio | Stanford - Biology | StanfordBiologyScraper | https://biology.stanford.edu/people | FALSE | static | rep2@company.com | | | Scraper in progress
```

### Template for New Entry
```
your_id | Your University | | https://university.edu/faculty | FALSE | static | your@email.com | | | New - needs scraper
```

---

## Troubleshooting

**"System not finding my university"**
- Check `enabled` is `TRUE`
- Check no typos in `university_id`

**"Getting FAILED status"**
- Check URL is still valid
- Check `scraper_class` matches exactly
- Check logs in GitHub Actions

**"Not receiving emails"**
- Check `sales_rep_email` is correct
- Check spam folder
- Emails only sent when NEW faculty detected

---

**Need help?** See SETUP_GUIDE.md or CONTRIBUTING.md
