"""
Email notification system for new faculty alerts
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import time
from scrapers.base_scraper import Faculty
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    SENDER_EMAIL, setup_logging
)


class EmailNotifier:
    """
    Handles email notifications for new/changed faculty
    """

    def __init__(self):
        """Initialize email notifier"""
        self.logger = setup_logging('EmailNotifier')

    def send_new_faculty_alert(
        self,
        recipient: str,
        university_name: str,
        new_faculty: List[Faculty],
        changed_faculty: List[Faculty] = None
    ) -> bool:
        """
        Send email alert for new/changed faculty

        Args:
            recipient: Recipient email address
            university_name: University display name
            new_faculty: List of new faculty members
            changed_faculty: List of changed faculty members

        Returns:
            True if email sent successfully
        """
        changed_faculty = changed_faculty or []

        # Don't send if no changes
        if not new_faculty and not changed_faculty:
            self.logger.info(f"No changes to report for {university_name}")
            return True

        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"FacultySnipe Alert: {len(new_faculty)} New Faculty at {university_name}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient

        # Create HTML body
        html_body = self._create_html_body(university_name, new_faculty, changed_faculty)

        # Create plain text fallback
        text_body = self._create_text_body(university_name, new_faculty, changed_faculty)

        # Attach both versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Send email with retry logic
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                    server.starttls()
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                    server.send_message(msg)

                self.logger.info(f"✓ Sent notification to {recipient} for {university_name}")
                return True

            except smtplib.SMTPAuthenticationError as e:
                # Don't retry auth errors
                self.logger.error(f"✗ SMTP authentication failed for {recipient}: {e}")
                return False

            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Email send attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.logger.error(f"✗ Failed to send email to {recipient} after {max_retries} attempts: {e}")
                    return False

        return False

    def _create_html_body(
        self,
        university_name: str,
        new_faculty: List[Faculty],
        changed_faculty: List[Faculty]
    ) -> str:
        """
        Create HTML email body

        Args:
            university_name: University name
            new_faculty: New faculty list
            changed_faculty: Changed faculty list

        Returns:
            HTML string
        """
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                }}
                .faculty-card {{
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 10px 0;
                    background-color: #f9f9f9;
                }}
                .faculty-name {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .faculty-title {{
                    color: #7f8c8d;
                    font-style: italic;
                }}
                .faculty-email {{
                    color: #3498db;
                }}
                .section-title {{
                    font-size: 20px;
                    font-weight: bold;
                    margin-top: 20px;
                    color: #2c3e50;
                    border-bottom: 2px solid #4CAF50;
                    padding-bottom: 5px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #7f8c8d;
                    font-size: 12px;
                }}
                a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>FacultySnipe Alert</h1>
                <p>{university_name}</p>
            </div>
            <div class="content">
        """

        # New faculty section
        if new_faculty:
            html += f"""
                <div class="section-title">
                    🆕 {len(new_faculty)} New Faculty Member{'s' if len(new_faculty) != 1 else ''}
                </div>
            """

            for faculty in new_faculty:
                html += self._faculty_card_html(faculty)

        # Changed faculty section
        if changed_faculty:
            html += f"""
                <div class="section-title">
                    🔄 {len(changed_faculty)} Updated Faculty Profile{'s' if len(changed_faculty) != 1 else ''}
                </div>
            """

            for faculty in changed_faculty:
                html += self._faculty_card_html(faculty)

        # Footer
        html += """
                <div class="footer">
                    <p>This is an automated notification from FacultySnipe.</p>
                    <p>Faculty data is monitored twice weekly.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _faculty_card_html(self, faculty: Faculty) -> str:
        """
        Create HTML card for single faculty member

        Args:
            faculty: Faculty object

        Returns:
            HTML string
        """
        email_html = f'<div class="faculty-email">📧 <a href="mailto:{faculty.email}">{faculty.email}</a></div>' if faculty.email else ''
        profile_html = f'<div>🔗 <a href="{faculty.profile_url}" target="_blank">View Profile</a></div>' if faculty.profile_url else ''
        dept_html = f'<div>🏛️ {faculty.department}</div>' if faculty.department else ''
        phone_html = f'<div>📞 {faculty.phone}</div>' if faculty.phone else ''

        return f"""
            <div class="faculty-card">
                <div class="faculty-name">{faculty.name}</div>
                <div class="faculty-title">{faculty.title or 'Faculty Member'}</div>
                {email_html}
                {profile_html}
                {dept_html}
                {phone_html}
            </div>
        """

    def _create_text_body(
        self,
        university_name: str,
        new_faculty: List[Faculty],
        changed_faculty: List[Faculty]
    ) -> str:
        """
        Create plain text email body

        Args:
            university_name: University name
            new_faculty: New faculty list
            changed_faculty: Changed faculty list

        Returns:
            Plain text string
        """
        lines = [
            "FacultySnipe Alert",
            "=" * 60,
            f"University: {university_name}",
            ""
        ]

        if new_faculty:
            lines.append(f"NEW FACULTY ({len(new_faculty)}):")
            lines.append("-" * 60)
            for faculty in new_faculty:
                lines.append(f"\nName: {faculty.name}")
                if faculty.title:
                    lines.append(f"Title: {faculty.title}")
                if faculty.email:
                    lines.append(f"Email: {faculty.email}")
                if faculty.profile_url:
                    lines.append(f"Profile: {faculty.profile_url}")
                if faculty.department:
                    lines.append(f"Department: {faculty.department}")
                lines.append("")

        if changed_faculty:
            lines.append(f"\nUPDATED FACULTY ({len(changed_faculty)}):")
            lines.append("-" * 60)
            for faculty in changed_faculty:
                lines.append(f"\nName: {faculty.name}")
                if faculty.title:
                    lines.append(f"Title: {faculty.title}")
                if faculty.email:
                    lines.append(f"Email: {faculty.email}")
                if faculty.profile_url:
                    lines.append(f"Profile: {faculty.profile_url}")
                lines.append("")

        lines.append("=" * 60)
        lines.append("This is an automated notification from FacultySnipe.")
        lines.append("Faculty data is monitored twice weekly.")

        return "\n".join(lines)
