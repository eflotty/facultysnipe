#!/usr/bin/env python3
"""
Test email notification directly
"""
from dotenv import load_dotenv
import os
load_dotenv('.env')

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

print("Testing email notification...")

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')

print(f"SMTP Host: {SMTP_HOST}:{SMTP_PORT}")
print(f"Username: {SMTP_USERNAME}")
print(f"Sender: {SENDER_EMAIL}")
print(f"Password: {SMTP_PASSWORD[:4]}...{SMTP_PASSWORD[-4:]}")
print()

try:
    print("Connecting to SMTP server...")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.set_debuglevel(1)  # Show detailed debug info

    print("\nStarting TLS...")
    server.starttls()

    print("\nLogging in...")
    server.login(SMTP_USERNAME, SMTP_PASSWORD)

    print("\n✓ Login successful!")

    # Send test email
    msg = MIMEMultipart()
    msg['Subject'] = 'FacultySnipe Test Email'
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL  # Send to yourself

    body = "This is a test email from FacultySnipe. If you receive this, email notifications are working!"
    msg.attach(MIMEText(body, 'plain'))

    print(f"\nSending test email to {SENDER_EMAIL}...")
    server.send_message(msg)

    print("✓ Email sent successfully!")
    print(f"\nCheck your inbox at {SENDER_EMAIL}")

    server.quit()

except smtplib.SMTPAuthenticationError as e:
    print(f"\n✗ Authentication failed: {e}")
    print("\nPossible fixes:")
    print("1. Regenerate Gmail app password at: https://myaccount.google.com/apppasswords")
    print("2. Make sure 2FA is enabled on the Gmail account")
    print("3. Use the new 16-character password (no spaces)")

except Exception as e:
    print(f"\n✗ Error: {e}")
