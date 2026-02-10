# Google Sheets Template Structure

This document shows the expected structure for your FacultySnipe Google Sheet.

## Sheet 1: CONFIG

This is the master configuration sheet. Required name: **CONFIG**

### Column Headers (Row 1)

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| university_id | university_name | scraper_class | url | enabled | scraper_type | sales_rep_email | last_run | last_status | notes |

### Example Data

| university_id | university_name | scraper_class | url | enabled | scraper_type | sales_rep_email | last_run | last_status | notes |
|---------------|-----------------|---------------|-----|---------|--------------|-----------------|----------|-------------|-------|
| miami_microbio | Miami - Microbiology | MiamiMicrobiologyScraper | https://med.miami.edu/departments/microbiology-and-immunology/faculty-and-staff | TRUE | static | rep1@company.com | 2026-02-04 10:30:00 | SUCCESS | Production |
| uf_biochem | UF - Biochemistry | UFBiochemScraper | https://biochem.med.ufl.edu/faculty/ | TRUE | dynamic | rep2@company.com | 2026-02-04 10:35:00 | SUCCESS | Uses Playwright |
| stanford_bio | Stanford - Biology | StanfordBiologyScraper | https://biology.stanford.edu/people | FALSE | static | rep1@company.com | | | In development |

### Column Descriptions

- **university_id** (Required): Unique identifier, lowercase with underscores
- **university_name** (Required): Display name shown in emails
- **scraper_class** (Required): Python class name from src/universities/
- **url** (Required): Faculty page URL to scrape
- **enabled** (Required): TRUE to monitor, FALSE to skip
- **scraper_type** (Required): "static" or "dynamic"
- **sales_rep_email** (Required): Email address for notifications
- **last_run** (Auto-updated): Timestamp of last scrape
- **last_status** (Auto-updated): SUCCESS/FAILED/SKIPPED
- **notes** (Optional): Admin notes

---

## Per-University Sheets

For each enabled university, a separate sheet is created automatically.
Sheet name matches **university_id** (e.g., "miami_microbio")

### Column Headers (Row 1)

| A | B | C | D | E | F | G | H | I | J | K | L |
|---|---|---|---|---|---|---|---|---|---|---|---|
| faculty_id | name | title | email | profile_url | department | phone | research_interests | first_seen | last_verified | status | raw_data |

### Example Data: "miami_microbio" Sheet

| faculty_id | name | title | email | profile_url | department | phone | research_interests | first_seen | last_verified | status | raw_data |
|------------|------|-------|-------|-------------|------------|-------|-------------------|------------|---------------|--------|----------|
| a3f2e1b8c4d5e6f7 | John Smith | Professor | jsmith@miami.edu | https://med.miami.edu/faculty/john-smith | Microbiology | 305-123-4567 | Bacterial pathogenesis | 2026-01-15 09:00:00 | 2026-02-04 10:30:00 | ACTIVE | {} |
| b7c8d9e0f1a2b3c4 | Jane Doe | Associate Professor | jdoe@miami.edu | https://med.miami.edu/faculty/jane-doe | Immunology | 305-123-4568 | Viral immunity | 2026-02-04 10:30:00 | 2026-02-04 10:30:00 | ACTIVE | {} |

### Column Descriptions

- **faculty_id** (Auto-generated): Unique 16-char hash from name+email+title
- **name** (Required): Full name
- **title** (Optional): Position/rank
- **email** (Optional): Contact email
- **profile_url** (Optional): Link to faculty profile page
- **department** (Optional): Department or division
- **phone** (Optional): Phone number
- **research_interests** (Optional): Research areas
- **first_seen** (Auto-set): Timestamp when first detected
- **last_verified** (Auto-updated): Last check timestamp
- **status** (Auto-updated): ACTIVE/REMOVED/CHANGED
- **raw_data** (Optional): JSON for custom fields

---

## Creating Your Sheet

### Method 1: Manual Creation

1. Create new Google Sheet
2. Rename Sheet1 to "CONFIG"
3. Add column headers as shown above
4. Add your university configurations
5. Share with service account email (Editor access)
6. Get Sheet ID from URL
7. Add to .env: `GOOGLE_SHEET_ID="your-sheet-id"`

### Method 2: Template Copy (if available)

1. Make a copy of the template sheet
2. Share with your service account
3. Update CONFIG with your universities
4. Get Sheet ID and add to .env

---

## Tips

### CONFIG Sheet

- Keep enabled=FALSE until scraper is tested
- Use descriptive university_name for clarity
- Double-check scraper_class matches exactly
- sales_rep_email can be same for multiple universities
- Use notes column to track development status

### Per-University Sheets

- DO NOT manually edit these sheets (auto-managed)
- Data is overwritten on each run
- first_seen is preserved for new faculty
- To force re-detection, delete entire sheet

### Formatting

- Bold header row
- Freeze header row (View → Freeze → 1 row)
- Add filters (Data → Create a filter)
- Use alternating colors for readability
- Column widths: auto-resize (double-click column border)

### Data Validation (Optional)

Add validation to CONFIG sheet:

**enabled column:**
- Data validation: List from range: TRUE, FALSE

**scraper_type column:**
- Data validation: List from range: static, dynamic

---

## Troubleshooting

### Permission Denied
- Service account needs Editor access
- Check sharing settings
- Verify credentials JSON

### Sheet Not Found
- Check sheet name matches exactly (case-sensitive)
- CONFIG must be uppercase
- University sheets use lowercase university_id

### Data Not Updating
- Check last_status in CONFIG for errors
- Verify enabled=TRUE
- Check GitHub Actions logs
- Test scraper locally

---

## Example: Complete Setup

1. **Create sheet**: "FacultySnipe Master"
2. **CONFIG sheet** with 2 universities:
   - miami_microbio (enabled)
   - uf_biochem (enabled)
3. **First run creates**:
   - Sheet: "miami_microbio" (auto-created)
   - Sheet: "uf_biochem" (auto-created)
4. **Each contains** scraped faculty data
5. **CONFIG updated** with last_run timestamps

Your final sheet structure:
```
FacultySnipe Master
├── CONFIG (your configuration)
├── miami_microbio (auto-created, 47 faculty)
└── uf_biochem (auto-created, 32 faculty)
```

---

For more details, see [SETUP_GUIDE.md](../SETUP_GUIDE.md)
