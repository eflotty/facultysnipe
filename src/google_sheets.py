"""
Google Sheets integration for data storage and configuration
"""
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Tuple, Optional, Any
import json
from datetime import datetime
from scrapers.base_scraper import Faculty
import sys
import os
import time
from functools import wraps
sys.path.insert(0, os.path.dirname(__file__))
from config import GOOGLE_SHEETS_CREDENTIALS, GOOGLE_SHEET_ID, CONFIG_SHEET_NAME, setup_logging
from sheet_ux_helper import SheetUXHelper


def retry_on_failure(max_retries=3, delay=2, backoff=2):
    """
    Retry decorator for handling transient failures

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_delay = delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # Get logger from self if available
                        logger = None
                        if args and hasattr(args[0], 'logger'):
                            logger = args[0].logger

                        if logger:
                            logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay}s...")

                        time.sleep(retry_delay)
                        retry_delay *= backoff
                    else:
                        if logger:
                            logger.error(f"{func.__name__} failed after {max_retries} attempts")
                        raise

            raise last_exception

        return wrapper
    return decorator


class GoogleSheetsManager:
    """
    Manages all Google Sheets operations
    """

    def __init__(self):
        """Initialize Google Sheets client"""
        self.logger = setup_logging('GoogleSheets')

        # Authenticate
        # Try to decode from base64 first (for Render compatibility)
        try:
            import base64
            creds_str = base64.b64decode(GOOGLE_SHEETS_CREDENTIALS).decode()
            creds_dict = json.loads(creds_str)
        except:
            # Fall back to direct JSON parsing (for local .env)
            creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS)

        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        self.client = gspread.authorize(creds)

        # Open spreadsheet
        self.spreadsheet = self.client.open_by_key(GOOGLE_SHEET_ID)
        self.logger.info(f"Connected to Google Sheet: {self.spreadsheet.title}")

        # Initialize UX helper
        self.ux_helper = SheetUXHelper()

    @retry_on_failure(max_retries=3, delay=2)
    def get_universities_config(self) -> List[Dict[str, str]]:
        """
        Load enabled universities from CONFIG sheet

        Returns:
            List of university configuration dictionaries
        """
        try:
            config_sheet = self.spreadsheet.worksheet(CONFIG_SHEET_NAME)

            # Get all values (to clean headers)
            all_values = config_sheet.get_all_values()

            if not all_values:
                self.logger.warning("CONFIG sheet is empty")
                return []

            # Clean headers (remove trailing/leading spaces)
            headers = [str(h).strip() for h in all_values[0]]

            # Build records manually with cleaned headers
            records = []
            for row in all_values[1:]:
                if not any(row):  # Skip empty rows
                    continue
                record = {headers[i]: str(row[i]).strip() if i < len(row) else ''
                         for i in range(len(headers))}
                records.append(record)

            # Filter for enabled universities
            enabled = [
                record for record in records
                if record.get('enabled', '').upper() == 'TRUE'
            ]

            self.logger.info(f"Loaded {len(enabled)} enabled universities from CONFIG (total: {len(records)})")
            return enabled

        except gspread.WorksheetNotFound:
            self.logger.error(f"CONFIG sheet not found. Creating template...")
            self._create_config_sheet()
            return []

    def _create_config_sheet(self):
        """Create CONFIG sheet with template headers"""
        try:
            config_sheet = self.spreadsheet.add_worksheet(
                title=CONFIG_SHEET_NAME,
                rows=100,
                cols=10
            )

            # Set headers
            headers = [
                'university_id',
                'university_name',
                'scraper_class',
                'url',
                'enabled',
                'scraper_type',
                'sales_rep_email',
                'last_run',
                'last_status',
                'notes'
            ]
            config_sheet.update('A1:J1', [headers])

            self.logger.info("Created CONFIG sheet with headers")

        except Exception as e:
            self.logger.error(f"Failed to create CONFIG sheet: {e}")

    @retry_on_failure(max_retries=3, delay=2)
    def get_existing_faculty(self, university_id: str, university_name: str = None) -> Dict[str, Dict]:
        """
        Load existing faculty data from university sheet

        Args:
            university_id: University identifier
            university_name: University display name (optional)

        Returns:
            Dictionary mapping faculty_id to faculty data
        """
        worksheet = None

        # Try multiple sheet name formats
        sheet_names_to_try = []

        # Try university_name first if provided
        if university_name:
            sheet_names_to_try.append(self._sanitize_sheet_name(university_name))

        # Fallback to university_id
        sheet_names_to_try.append(university_id)

        for sheet_name in sheet_names_to_try:
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                break
            except gspread.WorksheetNotFound:
                continue

        if not worksheet:
            self.logger.info(f"Sheet not found (tried: {', '.join(sheet_names_to_try)}). Will create new sheet.")
            return {}

        try:
            records = worksheet.get_all_records()

            # Convert to dict keyed by faculty_id
            existing = {
                record['faculty_id']: record
                for record in records
                if record.get('faculty_id')
            }

            self.logger.info(f"Loaded {len(existing)} existing faculty from '{worksheet.title}'")
            return existing

        except Exception as e:
            self.logger.error(f"Failed to read existing faculty: {e}")
            return {}

    def update_faculty(
        self,
        university_id: str,
        faculty_list: List[Faculty],
        university_name: str = None
    ) -> Tuple[List[Faculty], List[Faculty], List[str]]:
        """
        Update faculty data and detect changes

        Args:
            university_id: University identifier
            faculty_list: List of currently scraped faculty

        Returns:
            Tuple of (new_faculty, changed_faculty, removed_faculty_ids)
        """
        # Get existing data
        existing = self.get_existing_faculty(university_id, university_name)

        # Detect changes
        new_faculty = []
        changed_faculty = []
        current_ids = set()

        for faculty in faculty_list:
            current_ids.add(faculty.faculty_id)

            if faculty.faculty_id not in existing:
                # New faculty member
                new_faculty.append(faculty)
            else:
                # Check for changes
                old_data = existing[faculty.faculty_id]
                if self._has_changed(faculty, old_data):
                    changed_faculty.append(faculty)

        # Detect removed faculty
        removed_ids = [
            fid for fid in existing.keys()
            if fid not in current_ids
        ]

        self.logger.info(
            f"Changes detected - New: {len(new_faculty)}, "
            f"Changed: {len(changed_faculty)}, Removed: {len(removed_ids)}"
        )

        # Update sheet (use university_name for sheet title if provided)
        sheet_title = university_name or university_id
        self._write_faculty_data(university_id, faculty_list, new_faculty, sheet_title)

        return new_faculty, changed_faculty, removed_ids

    def _has_changed(self, faculty: Faculty, old_data: Dict) -> bool:
        """
        Check if faculty data has changed

        Args:
            faculty: New faculty data
            old_data: Existing faculty data

        Returns:
            True if data has changed
        """
        # Compare key fields
        fields_to_compare = ['name', 'title', 'email', 'profile_url', 'department']

        for field in fields_to_compare:
            new_value = getattr(faculty, field, '')
            old_value = old_data.get(field, '')

            # Normalize for comparison
            new_value = str(new_value).strip() if new_value else ''
            old_value = str(old_value).strip() if old_value else ''

            if new_value != old_value:
                return True

        return False

    @retry_on_failure(max_retries=3, delay=2)
    def _write_faculty_data(
        self,
        university_id: str,
        faculty_list: List[Faculty],
        new_faculty: List[Faculty],
        sheet_title: str = None
    ):
        """
        Write faculty data to sheet

        Args:
            university_id: University identifier (for lookups)
            faculty_list: All current faculty
            new_faculty: Newly detected faculty (for first_seen timestamp)
            sheet_title: Display name for sheet tab (defaults to university_id)
        """
        # Use sheet_title if provided, otherwise fallback to university_id
        sheet_name = sheet_title or university_id

        # Sanitize sheet name (Google Sheets limits)
        sheet_name = self._sanitize_sheet_name(sheet_name)

        try:
            # Get or create worksheet
            try:
                # Try to find existing sheet by either name
                worksheet = None
                try:
                    worksheet = self.spreadsheet.worksheet(sheet_name)
                except gspread.WorksheetNotFound:
                    # Try with university_id (for backwards compatibility)
                    try:
                        worksheet = self.spreadsheet.worksheet(university_id)
                        # Rename to new format
                        worksheet.update_title(sheet_name)
                        self.logger.info(f"Renamed sheet '{university_id}' to '{sheet_name}'")
                    except gspread.WorksheetNotFound:
                        pass

                if worksheet:
                    worksheet.clear()  # Clear existing data
                else:
                    raise gspread.WorksheetNotFound(sheet_name)

            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=15
                )

            # Prepare headers
            headers = [
                'faculty_id', 'name', 'title', 'email', 'profile_url',
                'department', 'phone', 'research_interests',
                'first_seen', 'last_verified', 'status', 'raw_data'
            ]

            # Prepare data rows
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_ids = {f.faculty_id for f in new_faculty}

            rows = [headers]
            for faculty in faculty_list:
                row = [
                    faculty.faculty_id,
                    faculty.name,
                    faculty.title or '',
                    faculty.email or '',
                    faculty.profile_url or '',
                    faculty.department or '',
                    faculty.phone or '',
                    faculty.research_interests or '',
                    now if faculty.faculty_id in new_ids else '',  # first_seen
                    now,  # last_verified
                    'ACTIVE',
                    json.dumps(faculty.raw_data) if faculty.raw_data else ''
                ]
                rows.append(row)

            # Write all data at once
            worksheet.update(f'A1:L{len(rows)}', rows)

            self.logger.info(f"Updated '{sheet_name}' sheet with {len(faculty_list)} faculty")

        except Exception as e:
            self.logger.error(f"Failed to write faculty data to '{sheet_name}': {e}")
            raise

    def _sanitize_sheet_name(self, name: str) -> str:
        """
        Sanitize sheet name for Google Sheets requirements

        Args:
            name: Desired sheet name

        Returns:
            Sanitized sheet name
        """
        # Google Sheets limits: 100 chars, no [ ] * ? : / \
        # Remove/replace invalid characters
        sanitized = name.replace('[', '(').replace(']', ')').replace('*', '').replace('?', '').replace(':', '-').replace('/', '-').replace('\\', '-')

        # Limit to 100 characters
        if len(sanitized) > 100:
            sanitized = sanitized[:97] + '...'

        return sanitized

    @retry_on_failure(max_retries=3, delay=2)
    def update_run_status(
        self,
        university_id: str,
        status: str,
        timestamp: Optional[str] = None
    ):
        """
        Update last run status in CONFIG sheet

        Args:
            university_id: University identifier
            status: Run status (SUCCESS/FAILED/SKIPPED)
            timestamp: Optional timestamp (defaults to now)
        """
        try:
            config_sheet = self.spreadsheet.worksheet(CONFIG_SHEET_NAME)

            # Get all values to find the row
            all_values = config_sheet.get_all_values()

            if not all_values:
                self.logger.warning("CONFIG sheet is empty")
                return

            # Clean headers
            headers = [str(h).strip() for h in all_values[0]]

            # Find column indices
            try:
                univ_id_col = headers.index('university_id')
                last_run_col = headers.index('last_run')
                last_status_col = headers.index('last_status')
            except ValueError as e:
                self.logger.error(f"Missing required column in CONFIG sheet: {e}")
                return

            # Find row for this university
            for row_idx, row in enumerate(all_values[1:], start=2):  # Start at 2 (after header)
                if row_idx - 2 < len(all_values) - 1 and univ_id_col < len(row):
                    row_univ_id = str(row[univ_id_col]).strip()

                    if row_univ_id == university_id:
                        # Update last_run and last_status
                        timestamp = timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # Convert column index to letter
                        import string
                        def col_to_letter(col):
                            result = ""
                            while col >= 0:
                                result = string.ascii_uppercase[col % 26] + result
                                col = col // 26 - 1
                            return result

                        last_run_cell = f"{col_to_letter(last_run_col)}{row_idx}"
                        last_status_cell = f"{col_to_letter(last_status_col)}{row_idx}"

                        # Batch update both cells at once
                        config_sheet.batch_update([
                            {'range': last_run_cell, 'values': [[timestamp]]},
                            {'range': last_status_cell, 'values': [[status]]}
                        ])

                        self.logger.debug(f"Updated {university_id} status: {status} at {timestamp}")
                        return

            self.logger.warning(f"University {university_id} not found in CONFIG sheet")

        except Exception as e:
            self.logger.error(f"Failed to update run status for {university_id}: {e}")

    def auto_fill_config_rows(self) -> int:
        """
        Auto-fill incomplete rows in CONFIG sheet
        If a row only has URL field filled, auto-generate other fields

        Returns:
            Number of rows auto-filled
        """
        try:
            config_sheet = self.spreadsheet.worksheet(CONFIG_SHEET_NAME)

            # Get all values
            all_values = config_sheet.get_all_values()

            if not all_values or len(all_values) < 2:
                self.logger.info("No rows to auto-fill")
                return 0

            # Clean headers
            headers = [str(h).strip() for h in all_values[0]]

            # Find column indices
            col_indices = {}
            for col_name in ['university_id', 'university_name', 'scraper_class', 'url',
                            'enabled', 'scraper_type', 'sales_rep_email', 'notes']:
                try:
                    col_indices[col_name] = headers.index(col_name)
                except ValueError:
                    self.logger.warning(f"Column '{col_name}' not found in CONFIG sheet")

            if 'url' not in col_indices:
                self.logger.error("URL column not found - cannot auto-fill")
                return 0

            # Process each row
            filled_count = 0
            updates = []

            for row_idx, row in enumerate(all_values[1:], start=2):
                # Pad row to match header length
                while len(row) < len(headers):
                    row.append('')

                url = str(row[col_indices['url']]).strip() if col_indices['url'] < len(row) else ''

                # Check if this row needs auto-filling
                if not url:
                    continue  # No URL, skip

                university_id = str(row[col_indices.get('university_id', -1)]).strip() if 'university_id' in col_indices else ''

                # Auto-fill if university_id is empty (indicates incomplete row)
                if not university_id:
                    self.logger.info(f"Auto-filling row {row_idx} with URL: {url}")

                    # Generate fields
                    auto_data = self.ux_helper.auto_fill_from_url(url)

                    # Prepare update for this row
                    import string
                    def col_to_letter(col):
                        result = ""
                        while col >= 0:
                            result = string.ascii_uppercase[col % 26] + result
                            col = col // 26 - 1
                        return result

                    # Update each field
                    for field_name, field_value in auto_data.items():
                        if field_name in col_indices:
                            col_idx = col_indices[field_name]
                            cell = f"{col_to_letter(col_idx)}{row_idx}"
                            updates.append({
                                'range': cell,
                                'values': [[field_value]]
                            })

                    filled_count += 1

            # Apply all updates in batch
            if updates:
                config_sheet.batch_update(updates)
                self.logger.info(f"✓ Auto-filled {filled_count} rows in CONFIG sheet")
            else:
                self.logger.info("No rows needed auto-filling")

            return filled_count

        except Exception as e:
            self.logger.error(f"Failed to auto-fill CONFIG rows: {e}")
            return 0

    def create_instructions_tab(self):
        """
        Create INSTRUCTIONS tab with user guidance
        """
        try:
            # Check if INSTRUCTIONS tab already exists
            try:
                instructions_sheet = self.spreadsheet.worksheet('INSTRUCTIONS')
                self.logger.info("INSTRUCTIONS tab already exists")
                return
            except gspread.WorksheetNotFound:
                pass

            # Create new worksheet
            instructions_sheet = self.spreadsheet.add_worksheet(
                title='INSTRUCTIONS',
                rows=50,
                cols=1
            )

            # Add instructions
            instructions = [
                ["FacultySnipe - Quick Start Guide"],
                [""],
                ["HOW TO ADD A NEW UNIVERSITY"],
                ["1. Go to the CONFIG tab"],
                ["2. Add a new row with ONLY the URL field filled in:"],
                ["   - Paste the faculty directory URL (e.g., https://biology.stanford.edu/faculty)"],
                ["3. Save the sheet"],
                ["4. Run the auto-fill command (done automatically on next run)"],
                ["5. The system will auto-generate:"],
                ["   - university_id (unique identifier)"],
                ["   - university_name (extracted from page)"],
                ["   - scraper_type (static or dynamic)"],
                ["   - enabled (set to TRUE)"],
                ["6. Manually fill in:"],
                ["   - sales_rep_email (your email address for notifications)"],
                [""],
                ["FIELD DESCRIPTIONS"],
                [""],
                ["university_id: Auto-generated unique identifier (e.g., 'stanford_biology')"],
                ["university_name: Auto-extracted display name (e.g., 'Stanford - Biology')"],
                ["scraper_class: Leave EMPTY (system will use smart scraper)"],
                ["url: Faculty directory URL - THIS IS THE ONLY REQUIRED FIELD"],
                ["enabled: TRUE to monitor, FALSE to skip"],
                ["scraper_type: 'static' or 'dynamic' (auto-detected)"],
                ["sales_rep_email: Your email for new faculty alerts"],
                ["last_run: Auto-updated timestamp of last check"],
                ["last_status: Auto-updated SUCCESS/FAILED/SKIPPED"],
                ["notes: Optional notes for your reference"],
                [""],
                ["TIPS"],
                ["- The system runs automatically twice per week (Monday & Thursday)"],
                ["- New faculty are detected within 3-4 days of being added to university sites"],
                ["- You'll receive an email alert when new faculty are found"],
                ["- Each university gets its own data tab in this spreadsheet"],
                ["- No coding required - just paste URLs!"],
                [""],
                ["TROUBLESHOOTING"],
                ["- If scraping fails, check the last_status column for errors"],
                ["- Try enabling/disabling to re-trigger scraping"],
                ["- Contact support if issues persist"],
                [""],
                ["For more help, see: https://github.com/yourusername/FacultySnipe"],
            ]

            # Write instructions
            instructions_sheet.update('A1:A' + str(len(instructions)), instructions)

            # Format the sheet
            instructions_sheet.format('A1', {
                'textFormat': {'bold': True, 'fontSize': 14}
            })

            self.logger.info("✓ Created INSTRUCTIONS tab")

        except Exception as e:
            self.logger.error(f"Failed to create INSTRUCTIONS tab: {e}")

    def add_to_new_contacts(
        self,
        university_name: str,
        new_faculty: List[Faculty]
    ):
        """
        Add new faculty to centralized NEW CONTACTS sheet

        Args:
            university_name: Display name of university
            new_faculty: List of new faculty members
        """
        if not new_faculty:
            return

        try:
            # Get or create NEW CONTACTS sheet
            try:
                contacts_sheet = self.spreadsheet.worksheet('NEW CONTACTS')
            except gspread.WorksheetNotFound:
                # Create new sheet
                contacts_sheet = self.spreadsheet.add_worksheet(
                    title='NEW CONTACTS',
                    rows=1000,
                    cols=12
                )

                # Set headers
                headers = [
                    'Date Added', 'University', 'Name', 'Title', 'Email',
                    'Profile URL', 'Department', 'Phone', 'Research Interests',
                    'Faculty ID', 'Status', 'Notes'
                ]
                contacts_sheet.update('A1:L1', [headers])

                # Format header row
                contacts_sheet.format('A1:L1', {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.2, 'green': 0.7, 'blue': 0.3}
                })

                self.logger.info("✓ Created NEW CONTACTS sheet")

            # Load existing faculty_ids from NEW CONTACTS to prevent duplicates
            existing_rows = contacts_sheet.get_all_values()
            if len(existing_rows) > 1:
                # Faculty ID is column J (index 9)
                existing_contact_ids = {
                    row[9].strip()
                    for row in existing_rows[1:]
                    if len(row) > 9 and row[9].strip()
                }
            else:
                existing_contact_ids = set()

            # Prepare rows to add - skip any already in NEW CONTACTS
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            rows = []
            skipped = 0

            for faculty in new_faculty:
                if faculty.faculty_id in existing_contact_ids:
                    skipped += 1
                    self.logger.debug(f"Skipping duplicate in NEW CONTACTS: {faculty.name} ({faculty.faculty_id})")
                    continue
                row = [
                    now,                                    # Date Added
                    university_name,                        # University
                    faculty.name,                          # Name
                    faculty.title or '',                   # Title
                    faculty.email or '',                   # Email
                    faculty.profile_url or '',             # Profile URL
                    faculty.department or '',              # Department
                    faculty.phone or '',                   # Phone
                    faculty.research_interests or '',      # Research Interests
                    faculty.faculty_id,                    # Faculty ID
                    'NEW',                                 # Status
                    ''                                      # Notes (for sales rep)
                ]
                rows.append(row)

            if skipped:
                self.logger.info(f"Skipped {skipped} already-existing contacts in NEW CONTACTS")

            if not rows:
                self.logger.info("No truly new contacts to add (all already in NEW CONTACTS)")
                return

            # Append only genuinely new contacts
            contacts_sheet.append_rows(rows)

            self.logger.info(f"✓ Added {len(rows)} new contacts to NEW CONTACTS sheet")

        except Exception as e:
            self.logger.error(f"Failed to add to NEW CONTACTS sheet: {e}")

    @retry_on_failure(max_retries=3, delay=2)
    def mark_new_contacts_as_old(self):
        """
        Mark all contacts with status 'NEW' as 'OLD' in the NEW CONTACTS sheet.
        This should be called at the end of each successful run to prevent
        re-notifying about contacts that have already been seen.
        """
        try:
            # Get NEW CONTACTS sheet
            try:
                contacts_sheet = self.spreadsheet.worksheet('NEW CONTACTS')
            except gspread.WorksheetNotFound:
                self.logger.debug("NEW CONTACTS sheet doesn't exist yet - nothing to mark as old")
                return

            # Get all rows
            all_values = contacts_sheet.get_all_values()
            if len(all_values) <= 1:
                self.logger.debug("NEW CONTACTS sheet is empty - nothing to mark as old")
                return

            # Find Status column (should be column K, index 10)
            headers = all_values[0]
            try:
                status_col_idx = headers.index('Status')
            except ValueError:
                self.logger.error("Status column not found in NEW CONTACTS sheet")
                return

            # Find all rows with 'NEW' status and prepare batch update
            updates = []
            marked_count = 0

            for row_idx, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
                if len(row) > status_col_idx and row[status_col_idx] == 'NEW':
                    # Convert column index to letter (A=0, B=1, ... K=10)
                    col_letter = chr(ord('A') + status_col_idx)
                    cell = f"{col_letter}{row_idx}"
                    updates.append({
                        'range': cell,
                        'values': [['OLD']]
                    })
                    marked_count += 1

            # Batch update all NEW -> OLD changes
            if updates:
                contacts_sheet.batch_update(updates)
                self.logger.info(f"✓ Marked {marked_count} contacts as OLD in NEW CONTACTS sheet")
            else:
                self.logger.debug("No NEW contacts to mark as OLD")

        except Exception as e:
            self.logger.error(f"Failed to mark contacts as OLD: {e}")

    @retry_on_failure(max_retries=3, delay=2)
    def get_contacts_from_new_contacts_sheet(
        self,
        university_name: str = None,
        status: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieve contacts from NEW CONTACTS sheet with filtering and pagination

        Args:
            university_name: Filter by university (optional)
            status: Filter by 'NEW' or 'OLD' (optional)
            limit: Max results to return
            offset: Pagination offset

        Returns:
            {
                'total': int,
                'returned': int,
                'contacts': [
                    {
                        'date_added': str,
                        'university': str,
                        'name': str,
                        'title': str,
                        'email': str,
                        'profile_url': str,
                        'department': str,
                        'phone': str,
                        'research_interests': str,
                        'faculty_id': str,
                        'status': str,
                        'notes': str
                    }
                ]
            }
        """
        try:
            # Get NEW CONTACTS sheet
            try:
                contacts_sheet = self.spreadsheet.worksheet('NEW CONTACTS')
            except gspread.WorksheetNotFound:
                return {'total': 0, 'returned': 0, 'contacts': []}

            # Get all records
            all_records = contacts_sheet.get_all_records()

            # Filter by university_name if provided
            if university_name:
                all_records = [
                    r for r in all_records
                    if r.get('University', '').strip() == university_name.strip()
                ]

            # Filter by status if provided
            if status:
                all_records = [
                    r for r in all_records
                    if r.get('Status', '').strip().upper() == status.strip().upper()
                ]

            total = len(all_records)

            # Apply pagination
            paginated_records = all_records[offset:offset + limit]

            # Format contacts
            contacts = []
            for record in paginated_records:
                contact = {
                    'date_added': record.get('Date Added', ''),
                    'university': record.get('University', ''),
                    'name': record.get('Name', ''),
                    'title': record.get('Title', ''),
                    'email': record.get('Email', ''),
                    'profile_url': record.get('Profile URL', ''),
                    'department': record.get('Department', ''),
                    'phone': record.get('Phone', ''),
                    'research_interests': record.get('Research Interests', ''),
                    'faculty_id': record.get('Faculty ID', ''),
                    'status': record.get('Status', ''),
                    'notes': record.get('Notes', '')
                }
                contacts.append(contact)

            return {
                'total': total,
                'returned': len(contacts),
                'contacts': contacts
            }

        except Exception as e:
            self.logger.error(f"Failed to get contacts from NEW CONTACTS sheet: {e}")
            return {'total': 0, 'returned': 0, 'contacts': []}

    @retry_on_failure(max_retries=3, delay=2)
    def get_contact_counts_by_university(self) -> Dict[str, Dict[str, int]]:
        """
        Get NEW and OLD contact counts for each university

        Returns:
            {
                'University of Miami - Microbiology': {'new': 12, 'old': 45},
                'Stanford University - Biology': {'new': 5, 'old': 120},
                ...
            }
        """
        try:
            # Get NEW CONTACTS sheet
            try:
                contacts_sheet = self.spreadsheet.worksheet('NEW CONTACTS')
            except gspread.WorksheetNotFound:
                return {}

            # Get all records
            all_records = contacts_sheet.get_all_records()

            # Count by university and status
            counts = {}
            for record in all_records:
                university = record.get('University', '').strip()
                status = record.get('Status', '').strip().upper()

                if not university:
                    continue

                if university not in counts:
                    counts[university] = {'new': 0, 'old': 0}

                if status == 'NEW':
                    counts[university]['new'] += 1
                elif status == 'OLD':
                    counts[university]['old'] += 1

            return counts

        except Exception as e:
            self.logger.error(f"Failed to get contact counts by university: {e}")
            return {}

    @retry_on_failure(max_retries=3, delay=2)
    def get_grouped_universities(self) -> Dict[str, Any]:
        """
        Get universities grouped by parent institution with contact counts
        Groups universities by domain to handle variations like:
        - "Miami University" and "University of Miami" from miami.edu -> same group
        - "Miami University" from miamioh.edu -> different group

        Returns:
            {
                'University of Miami': {
                    'directories': [
                        {
                            'university_id': 'miami_microbiology',
                            'university_name': 'University of Miami - Microbiology',
                            'department': 'Microbiology',
                            'url': 'https://...',
                            'enabled': True,
                            'last_status': 'SUCCESS',
                            'contacts': {'new': 12, 'old': 45}
                        }
                    ],
                    'total_new': 45,
                    'total_old': 234
                }
            }
        """
        try:
            from urllib.parse import urlparse

            # Get universities from CONFIG
            universities = self.get_universities_config()

            # Get contact counts
            contact_counts = self.get_contact_counts_by_university()

            # Helper function to extract base domain (e.g., miami.edu from biology.miami.edu)
            def extract_base_domain(url):
                """Extract base domain from URL (e.g., miami.edu from biology.miami.edu)"""
                try:
                    parsed_url = urlparse(url)
                    hostname = parsed_url.netloc.lower()
                    # Remove 'www.' prefix if present
                    if hostname.startswith('www.'):
                        hostname = hostname[4:]

                    # Split by dots and get last 2 parts (domain.tld)
                    parts = hostname.split('.')
                    if len(parts) >= 2:
                        # Handle special cases like .edu.au, .ac.uk
                        if len(parts) >= 3 and parts[-2] in ['edu', 'ac', 'co']:
                            return '.'.join(parts[-3:])
                        else:
                            return '.'.join(parts[-2:])
                    return hostname
                except Exception:
                    return None

            # Helper function to extract department name from URL
            def extract_department_from_url(url):
                """Extract department name from URL path (e.g., 'cell-biology' -> 'Cell Biology')"""
                try:
                    parsed_url = urlparse(url)
                    path = parsed_url.path.lower()

                    # Common patterns for department URLs
                    # /departments/cell-biology/
                    # /department/biochemistry/
                    # /academics/departments/chemistry/

                    # Look for common department indicators
                    if '/departments/' in path:
                        dept = path.split('/departments/')[1].split('/')[0]
                    elif '/department/' in path:
                        dept = path.split('/department/')[1].split('/')[0]
                    elif '/academics/departments/' in path:
                        dept = path.split('/academics/departments/')[1].split('/')[0]
                    else:
                        # Try to extract from subdomain
                        hostname = parsed_url.netloc.lower()
                        if hostname.startswith('www.'):
                            hostname = hostname[4:]
                        parts = hostname.split('.')
                        if len(parts) > 2:
                            dept = parts[0]
                        else:
                            return None

                    # Clean up and format the department name
                    # 'cell-biology' -> 'Cell Biology'
                    # 'biochemistry-and-molecular-biology' -> 'Biochemistry and Molecular Biology'
                    dept = dept.replace('-', ' ').replace('_', ' ')
                    dept = ' '.join(word.capitalize() for word in dept.split())

                    return dept if dept else None

                except Exception:
                    return None

            # First pass: Group by domain to identify which universities should be combined
            domain_to_parents = {}

            for uni in universities:
                university_name = uni.get('university_name', '')
                url = uni.get('url', '')

                # Extract base domain from URL
                domain = extract_base_domain(url)
                if not domain:
                    self.logger.warning(f"Failed to parse domain from URL '{url}'")
                    continue

                # Extract parent institution name
                if ' - ' in university_name:
                    parent = university_name.split(' - ', 1)[0].strip()
                else:
                    parent = university_name.strip()

                # Track which parent names are used for each domain
                if domain not in domain_to_parents:
                    domain_to_parents[domain] = []
                if parent not in domain_to_parents[domain]:
                    domain_to_parents[domain].append(parent)

            # Second pass: Choose canonical parent name for each domain
            # Use the longest/most complete name as canonical
            domain_to_canonical = {}
            for domain, parents in domain_to_parents.items():
                if len(parents) == 1:
                    domain_to_canonical[domain] = parents[0]
                else:
                    # Pick the longest name as canonical (usually more complete)
                    # e.g., "University of Miami" is more complete than "Miami"
                    domain_to_canonical[domain] = max(parents, key=len)
                    self.logger.info(f"Combining variants for {domain}: {parents} -> '{domain_to_canonical[domain]}'")

            # Third pass: Group directories using canonical parent names
            grouped = {}

            for uni in universities:
                university_id = uni.get('university_id', '')
                university_name = uni.get('university_name', '')
                url = uni.get('url', '')
                enabled = uni.get('enabled', '').upper() == 'TRUE'
                last_status = uni.get('last_status', '')

                # Extract base domain
                domain = extract_base_domain(url)

                # Use canonical parent name for this domain
                if domain and domain in domain_to_canonical:
                    parent = domain_to_canonical[domain]
                else:
                    # Fallback if domain lookup fails
                    if ' - ' in university_name:
                        parent = university_name.split(' - ', 1)[0].strip()
                    else:
                        parent = university_name.strip()

                # Extract department
                if ' - ' in university_name:
                    department = university_name.split(' - ', 1)[1].strip()
                else:
                    # Try to extract from URL if not in name
                    department = extract_department_from_url(url) or ''

                # Get contact counts for this university
                uni_contacts = contact_counts.get(university_name, {'new': 0, 'old': 0})

                # Log if all directories have the same count (debugging)
                if uni_contacts['new'] > 0:
                    self.logger.debug(f"Counts for '{university_name}': {uni_contacts}")

                # Create directory entry
                directory = {
                    'university_id': university_id,
                    'university_name': university_name,
                    'department': department or university_name,
                    'url': url,
                    'enabled': enabled,
                    'last_status': last_status,
                    'contacts': uni_contacts
                }

                # Add to grouped structure
                if parent not in grouped:
                    grouped[parent] = {
                        'directories': [],
                        'total_new': 0,
                        'total_old': 0
                    }

                grouped[parent]['directories'].append(directory)
                grouped[parent]['total_new'] += uni_contacts['new']
                grouped[parent]['total_old'] += uni_contacts['old']

            return grouped

        except Exception as e:
            self.logger.error(f"Failed to get grouped universities: {e}")
            return {}

    @retry_on_failure(max_retries=3, delay=2)
    def update_system_status(
        self,
        status: str,
        universities_processed: int,
        new_faculty_count: int,
        changed_faculty_count: int,
        execution_time: float,
        errors: list,
        github_url: str = ''
    ):
        """
        Update SYSTEM_STATUS tab with run results

        Args:
            status: Run status (SUCCESS/FAILURE)
            universities_processed: Number of universities processed
            new_faculty_count: Number of new faculty detected
            changed_faculty_count: Number of changed faculty
            execution_time: Execution time in seconds
            errors: List of error messages
            github_url: GitHub Actions run URL
        """
        try:
            # Get or create SYSTEM_STATUS sheet
            try:
                status_sheet = self.spreadsheet.worksheet('SYSTEM_STATUS')
            except gspread.WorksheetNotFound:
                # Create new sheet
                status_sheet = self.spreadsheet.add_worksheet(
                    title='SYSTEM_STATUS',
                    rows=1000,
                    cols=10
                )

                # Set headers
                headers = [
                    'timestamp',
                    'status',
                    'universities_processed',
                    'new_faculty',
                    'changed_faculty',
                    'execution_time',
                    'errors',
                    'github_url'
                ]
                status_sheet.update('A1:H1', [headers])

                # Format header row
                status_sheet.format('A1:H1', {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8}
                })

                self.logger.info("Created SYSTEM_STATUS sheet")

            # Prepare row data
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            error_text = '; '.join(errors) if errors else ''

            row = [
                now,
                status,
                universities_processed,
                new_faculty_count,
                changed_faculty_count,
                round(execution_time, 1),
                error_text,
                github_url
            ]

            # Append row
            status_sheet.append_row(row)

            self.logger.info(f"Updated SYSTEM_STATUS: {status} - {new_faculty_count} new faculty")

        except Exception as e:
            self.logger.error(f"Failed to update SYSTEM_STATUS: {e}")
            raise

    def create_dashboard_sheet(self, force_refresh=False):
        """
        Create DASHBOARD sheet with summary statistics

        Args:
            force_refresh: If True, delete and recreate existing dashboard
        """
        try:
            # Check if DASHBOARD already exists
            try:
                dashboard_sheet = self.spreadsheet.worksheet('DASHBOARD')

                if force_refresh:
                    self.logger.info("Refreshing DASHBOARD sheet...")
                    self.spreadsheet.del_worksheet(dashboard_sheet)
                else:
                    self.logger.info("DASHBOARD sheet already exists (use force_refresh=True to recreate)")
                    return
            except gspread.WorksheetNotFound:
                pass

            # Create new worksheet
            dashboard_sheet = self.spreadsheet.add_worksheet(
                title='DASHBOARD',
                rows=50,
                cols=6
            )

            # Add dashboard content - use batch_update for proper formula handling
            # First, add static content
            static_content = [
                ["FacultySnipe - Dashboard", "", "", "", "", ""],
                ["", "", "", "", "", ""],
                ["Quick Stats", "", "", "", "", ""],
                ["Total Universities Monitored:", "", "", "", "", ""],
                ["Active Universities:", "", "", "", "", ""],
                ["Total New Contacts:", "", "", "", "", ""],
                ["Contacts This Week:", "", "", "", "", ""],
                ["", "", "", "", "", ""],
                ["Recent Activity", "", "", "", "", ""],
                ["Last 10 New Contacts:", "", "", "", "", ""],
                ["", "", "", "", "", ""],
                ["University", "Name", "Title", "Email", "Date Added", ""],
            ]

            # Add placeholder rows for last 10 contacts
            for i in range(10):
                static_content.append(["", "", "", "", "", ""])

            static_content.extend([
                ["", "", "", "", "", ""],
                ["", "", "", "", "", ""],
                ["University Status", "", "", "", "", ""],
                ["University", "Last Run", "Status", "Faculty Count", "", ""],
            ])

            # Write static content first
            dashboard_sheet.update('A1:F' + str(len(static_content)), static_content)

            # Now add formulas using batch_update with proper user_entered_value
            formula_updates = [
                {
                    'range': 'B4',
                    'values': [['=COUNTA(CONFIG!A2:A)']]
                },
                {
                    # SUMPRODUCT handles both text "TRUE" and boolean TRUE in enabled column
                    'range': 'B5',
                    'values': [['=SUMPRODUCT((CONFIG!E2:E1000="TRUE")+(CONFIG!E2:E1000=TRUE)>0)']]
                },
                {
                    'range': 'B6',
                    'values': [['=COUNTA(\'NEW CONTACTS\'!A2:A)']]
                },
                {
                    # Dates stored as text strings - use SUMPRODUCT+DATEVALUE for reliable comparison
                    'range': 'B7',
                    'values': [['=SUMPRODUCT((IFERROR(DATEVALUE(LEFT(\'NEW CONTACTS\'!A2:A1000,10)),0)>=TODAY()-7)*(\'NEW CONTACTS\'!K2:K1000="NEW"))']]
                },
            ]

            # Add formulas for last 10 contacts
            # Uses COUNTA to find actual last filled row (ROWS() returns total sheet rows, not data rows)
            for i in range(1, 11):
                row = 12 + i
                coa = "COUNTA('NEW CONTACTS'!A:A)"
                cond = f"COUNTA('NEW CONTACTS'!A2:A)>={i}"
                idx = f"{coa}+1-{i}"
                formula_updates.extend([
                    {
                        'range': f'A{row}',
                        'values': [[f"=IF({cond},INDEX('NEW CONTACTS'!B:B,{idx}),\"\")"]]
                    },
                    {
                        'range': f'B{row}',
                        'values': [[f"=IF({cond},INDEX('NEW CONTACTS'!C:C,{idx}),\"\")"]]
                    },
                    {
                        'range': f'C{row}',
                        'values': [[f"=IF({cond},INDEX('NEW CONTACTS'!D:D,{idx}),\"\")"]]
                    },
                    {
                        'range': f'D{row}',
                        'values': [[f"=IF({cond},INDEX('NEW CONTACTS'!E:E,{idx}),\"\")"]]
                    },
                    {
                        'range': f'E{row}',
                        'values': [[f"=IF({cond},INDEX('NEW CONTACTS'!A:A,{idx}),\"\")"]]
                    },
                ])

            # Batch update all formulas
            dashboard_sheet.batch_update(formula_updates, value_input_option='USER_ENTERED')

            # Format the dashboard
            dashboard_sheet.format('A1', {
                'textFormat': {'bold': True, 'fontSize': 16}
            })

            dashboard_sheet.format('A3', {
                'textFormat': {'bold': True, 'fontSize': 14}
            })

            dashboard_sheet.format('A9', {
                'textFormat': {'bold': True, 'fontSize': 14}
            })

            dashboard_sheet.format('A12:F12', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
            })

            self.logger.info("✓ Created DASHBOARD sheet")

        except Exception as e:
            self.logger.error(f"Failed to create DASHBOARD sheet: {e}")
