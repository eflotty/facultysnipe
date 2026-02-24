"""
Main orchestration script for FacultySnipe
Coordinates scraping, change detection, and notifications
Supports parallel processing for faster execution
"""
import sys
import os
import argparse
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# Load environment variables FIRST before any other imports
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(env_path)

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import setup_logging, validate_environment
from google_sheets import GoogleSheetsManager
from email_notifier import EmailNotifier
from scrapers.registry import ScraperRegistry


class FacultyMonitor:
    """
    Main orchestration class for faculty monitoring
    """

    def __init__(self, max_workers: int = 3):
        """Initialize monitor

        Args:
            max_workers: Maximum number of universities to process in parallel (default: 3)
        """
        self.logger = setup_logging('FacultyMonitor')
        self.sheets = GoogleSheetsManager()
        self.notifier = EmailNotifier()
        self.max_workers = max_workers
        self.stats = {
            'total_universities': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_new_faculty': 0,
            'total_changed_faculty': 0
        }
        # Thread lock for updating shared resources (stats, NEW CONTACTS sheet)
        self.stats_lock = threading.Lock()
        self.new_contacts_lock = threading.Lock()

    def run(self, university_filter: str = None, parallel: bool = None):
        """
        Main execution workflow

        Args:
            university_filter: Optional - only process this university_id
            parallel: If True/False, force parallel mode. If None, auto-detect (default)
        """
        self.logger.info("=" * 60)
        self.logger.info("FacultySnipe - Automated Faculty Monitoring")
        self.logger.info(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)

        try:
            # Auto-fill any incomplete rows in CONFIG (new URLs added)
            self.logger.info("Checking for incomplete CONFIG rows...")
            filled = self.sheets.auto_fill_config_rows()
            if filled > 0:
                self.logger.info(f"✓ Auto-filled {filled} new universities")

            # Load university configurations
            universities = self.sheets.get_universities_config()

            # Filter if specified
            if university_filter:
                universities = [u for u in universities if u['university_id'] == university_filter]
                if not universities:
                    self.logger.error(f"University '{university_filter}' not found or not enabled")
                    return

            self.stats['total_universities'] = len(universities)

            # Mark previous run's NEW contacts as OLD BEFORE starting this run
            # This ensures only contacts from THIS run will show as NEW
            self.logger.info("Marking previous contacts as OLD...")
            self.sheets.mark_new_contacts_as_old()

            # Auto-detect parallel mode if not specified
            if parallel is None:
                # Use parallel automatically if 4+ universities
                parallel = len(universities) >= 4

            # Auto-adjust workers based on university count
            if parallel:
                if len(universities) >= 20:
                    self.max_workers = 5
                elif len(universities) >= 10:
                    self.max_workers = 4
                else:
                    self.max_workers = 3

            # Log processing mode
            if parallel and len(universities) > 1:
                self.logger.info(f"Processing {len(universities)} universities in PARALLEL ({self.max_workers} workers)")
            else:
                self.logger.info(f"Processing {len(universities)} universities SEQUENTIALLY")

            # Process universities (parallel or sequential)
            if parallel and len(universities) > 1:
                self._process_universities_parallel(universities)
            else:
                self._process_universities_sequential(universities)

            # Print summary
            self._print_summary()

        except Exception as e:
            self.logger.error(f"Fatal error in main workflow: {e}", exc_info=True)
            sys.exit(1)

    def _process_universities_sequential(self, universities: List[Dict]):
        """
        Process universities one at a time (original behavior)

        Args:
            universities: List of university configs
        """
        for university in universities:
            self._process_university(university)

    def _process_universities_parallel(self, universities: List[Dict]):
        """
        Process universities in parallel using thread pool

        Args:
            universities: List of university configs
        """
        self.logger.info(f"Starting parallel processing with {self.max_workers} workers...")

        # Use ThreadPoolExecutor for I/O-bound tasks (web scraping, API calls)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all universities for processing
            future_to_university = {
                executor.submit(self._process_university, univ): univ
                for univ in universities
            }

            # Process results as they complete
            for future in as_completed(future_to_university):
                university = future_to_university[future]
                university_name = university.get('university_name', university.get('university_id'))

                try:
                    future.result()  # This will raise any exception that occurred
                except Exception as e:
                    self.logger.error(f"Exception processing {university_name}: {e}", exc_info=True)

        self.logger.info("✓ Parallel processing complete")

    def _process_university(self, config: Dict):
        """
        Process a single university

        Args:
            config: University configuration from CONFIG sheet
        """
        university_id = config.get('university_id')
        university_name = config.get('university_name')
        scraper_class = config.get('scraper_class')
        url = config.get('url')
        sales_rep_email = config.get('sales_rep_email')

        self.logger.info("")
        self.logger.info("-" * 60)
        self.logger.info(f"Processing: {university_name} ({university_id})")
        self.logger.info("-" * 60)

        try:
            # Validate configuration (scraper_class is optional now - will use HybridScraper if empty)
            if not all([university_id, url]):
                self.logger.error(f"Invalid configuration for {university_id}")
                with self.stats_lock:
                    self.stats['skipped'] += 1
                self.sheets.update_run_status(university_id, 'SKIPPED')
                return

            # Load scraper
            scraper = ScraperRegistry.get_scraper(
                scraper_class=scraper_class,
                url=url,
                university_id=university_id
            )

            if not scraper:
                self.logger.error(f"Failed to load scraper class: {scraper_class}")
                with self.stats_lock:
                    self.stats['failed'] += 1
                self.sheets.update_run_status(university_id, 'FAILED')
                return

            # Scrape faculty data
            self.logger.info(f"Scraping faculty from {url}")
            faculty_list = scraper.scrape()

            if not faculty_list:
                self.logger.warning(f"No faculty data found for {university_id}")
                with self.stats_lock:
                    self.stats['successful'] += 1
                self.sheets.update_run_status(university_id, 'SUCCESS')
                return

            self.logger.info(f"Scraped {len(faculty_list)} faculty members")

            # Detect changes
            self.logger.info("Detecting changes...")
            new_faculty, changed_faculty, removed_ids = self.sheets.update_faculty(
                university_id=university_id,
                faculty_list=faculty_list,
                university_name=university_name
            )

            # Update statistics (thread-safe)
            with self.stats_lock:
                self.stats['total_new_faculty'] += len(new_faculty)
                self.stats['total_changed_faculty'] += len(changed_faculty)

            # Add new faculty to centralized NEW CONTACTS sheet (thread-safe)
            if new_faculty:
                with self.new_contacts_lock:
                    self.sheets.add_to_new_contacts(university_name, new_faculty)

            # Send notifications ONLY if NEW faculty found (not just changes)
            if new_faculty and sales_rep_email:
                self.logger.info(f"Sending notification to {sales_rep_email} ({len(new_faculty)} new faculty)")
                success = self.notifier.send_new_faculty_alert(
                    recipient=sales_rep_email,
                    university_name=university_name,
                    new_faculty=new_faculty,
                    changed_faculty=changed_faculty
                )

                if success:
                    self.logger.info("✓ Notification sent successfully")
                else:
                    self.logger.warning("✗ Failed to send notification")

            elif new_faculty and not sales_rep_email:
                self.logger.warning(f"⚠ {len(new_faculty)} new faculty found but no sales_rep_email configured")
            elif changed_faculty and not new_faculty:
                self.logger.info(f"No new faculty (only {len(changed_faculty)} updates) - no notification sent")

            # Update run status
            self.sheets.update_run_status(university_id, 'SUCCESS')
            with self.stats_lock:
                self.stats['successful'] += 1

            self.logger.info(f"✓ {university_name} completed successfully")

        except Exception as e:
            self.logger.error(f"Failed to process {university_id}: {e}", exc_info=True)
            with self.stats_lock:
                self.stats['failed'] += 1

            try:
                self.sheets.update_run_status(university_id, 'FAILED')
            except Exception:
                pass  # Don't fail if status update fails

    def _print_summary(self):
        """Print execution summary"""
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("EXECUTION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Universities: {self.stats['total_universities']}")
        self.logger.info(f"Successful: {self.stats['successful']}")
        self.logger.info(f"Failed: {self.stats['failed']}")
        self.logger.info(f"Skipped: {self.stats['skipped']}")
        self.logger.info(f"Total New Faculty: {self.stats['total_new_faculty']}")
        self.logger.info(f"Total Changed Faculty: {self.stats['total_changed_faculty']}")
        self.logger.info("=" * 60)

        # Exit with error code if failures
        if self.stats['failed'] > 0:
            self.logger.warning("Some universities failed - check logs above")
            sys.exit(1)


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='FacultySnipe - Automated Faculty Monitoring')
    parser.add_argument(
        '--university',
        type=str,
        help='Process only this university_id',
        default=None
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        dest='parallel',
        help='Force parallel processing (overrides auto-detection)'
    )
    parser.add_argument(
        '--sequential',
        action='store_false',
        dest='parallel',
        help='Force sequential processing (overrides auto-detection)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=3,
        help='Number of parallel workers (default: 3, recommended: 3-5)'
    )
    parser.set_defaults(parallel=None)  # None = auto-detect based on university count
    args = parser.parse_args()

    # Validate environment
    try:
        validate_environment()
    except ValueError as e:
        print(f"ERROR: {e}")
        print("\nPlease ensure all required environment variables are set.")
        print("See .env.example for reference.")
        sys.exit(1)

    # Run monitor
    monitor = FacultyMonitor(max_workers=args.workers)
    monitor.run(university_filter=args.university, parallel=args.parallel)


if __name__ == '__main__':
    main()
