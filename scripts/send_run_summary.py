"""
Send run summary email and update SYSTEM_STATUS sheet
"""
import sys
import os
import argparse
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets import GoogleSheetsManager
from config import SENDER_EMAIL, setup_logging
from email_notifier import EmailNotifier


def send_run_summary(status, universities_processed=0, new_faculty_count=0,
                     changed_faculty_count=0, execution_time=0, errors=None):
    """
    Send run summary email and update SYSTEM_STATUS sheet

    Args:
        status: 'success' or 'failure'
        universities_processed: Number of universities processed
        new_faculty_count: Number of new faculty detected
        changed_faculty_count: Number of faculty with changes
        execution_time: Execution time in seconds
        errors: List of error messages (if any)
    """
    logger = setup_logging('RunSummary')

    try:
        # Initialize Google Sheets
        sheets = GoogleSheetsManager()

        # Update SYSTEM_STATUS sheet
        github_run_url = os.environ.get('GITHUB_SERVER_URL', '') + '/' + \
                        os.environ.get('GITHUB_REPOSITORY', '') + '/actions/runs/' + \
                        os.environ.get('GITHUB_RUN_ID', '')

        sheets.update_system_status(
            status=status.upper(),
            universities_processed=universities_processed,
            new_faculty_count=new_faculty_count,
            changed_faculty_count=changed_faculty_count,
            execution_time=execution_time,
            errors=errors or [],
            github_url=github_run_url if os.environ.get('GITHUB_RUN_ID') else ''
        )

        # Send email notification
        email_notifier = EmailNotifier()
        admin_email = SENDER_EMAIL  # Send to admin

        if status == 'success':
            subject = f"✅ FacultySnipe Run Successful - {new_faculty_count} New Faculty"

            body = f"""
FacultySnipe monitoring completed successfully.

Summary:
- Status: SUCCESS
- Universities Processed: {universities_processed}
- New Faculty Detected: {new_faculty_count}
- Changed Faculty: {changed_faculty_count}
- Execution Time: {execution_time:.1f} seconds

{f'GitHub Actions: {github_run_url}' if github_run_url else ''}

Next run: Monday or Thursday at 3 AM UTC
            """

            # Only send success email if new faculty were found
            if new_faculty_count > 0:
                email_notifier.send_email(
                    to_email=admin_email,
                    subject=subject,
                    body=body
                )
                logger.info(f"Success summary sent to {admin_email}")
            else:
                logger.info("No new faculty - skipping success email")

        else:
            subject = "❌ FacultySnipe Run Failed"

            error_details = "\n".join(errors) if errors else "Unknown error"

            body = f"""
FacultySnipe monitoring failed.

Summary:
- Status: FAILURE
- Universities Processed: {universities_processed}
- Execution Time: {execution_time:.1f} seconds

Errors:
{error_details}

{f'GitHub Actions Logs: {github_run_url}' if github_run_url else ''}

Please check the logs for more details.
            """

            email_notifier.send_email(
                to_email=admin_email,
                subject=subject,
                body=body
            )
            logger.info(f"Failure alert sent to {admin_email}")

    except Exception as e:
        logger.error(f"Failed to send run summary: {e}")
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send FacultySnipe run summary')
    parser.add_argument('--status', required=True, choices=['success', 'failure'],
                       help='Run status')
    parser.add_argument('--universities', type=int, default=0,
                       help='Number of universities processed')
    parser.add_argument('--new-faculty', type=int, default=0,
                       help='Number of new faculty detected')
    parser.add_argument('--changed-faculty', type=int, default=0,
                       help='Number of changed faculty')
    parser.add_argument('--execution-time', type=float, default=0,
                       help='Execution time in seconds')
    parser.add_argument('--errors', nargs='*', default=[],
                       help='Error messages')

    args = parser.parse_args()

    send_run_summary(
        status=args.status,
        universities_processed=args.universities,
        new_faculty_count=args.new_faculty,
        changed_faculty_count=args.changed_faculty,
        execution_time=args.execution_time,
        errors=args.errors
    )
