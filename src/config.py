"""
Configuration and logging setup for FacultySnipe
"""
import logging
import os
from pathlib import Path

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Scraper configuration
SCRAPER_TIMEOUT = int(os.getenv('SCRAPER_TIMEOUT', '180'))  # Increased to 3 minutes for thoroughness
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
THOROUGH_MODE = True  # Prioritize completeness over speed

# Google Sheets configuration
GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
CONFIG_SHEET_NAME = 'CONFIG'

# Email configuration
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')


def setup_logging(name: str = 'FacultySnipe') -> logging.Logger:
    """
    Setup logging configuration

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


def validate_environment():
    """
    Validate that all required environment variables are set

    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = {
        'GOOGLE_SHEETS_CREDENTIALS': GOOGLE_SHEETS_CREDENTIALS,
        'GOOGLE_SHEET_ID': GOOGLE_SHEET_ID,
        'SMTP_USERNAME': SMTP_USERNAME,
        'SMTP_PASSWORD': SMTP_PASSWORD,
        'SENDER_EMAIL': SENDER_EMAIL
    }

    missing = [var for var, value in required_vars.items() if not value]

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
