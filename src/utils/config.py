import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration"""
    # Base Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    OUTPUT_DIR = DATA_DIR / "generated"
    LOG_DIR = DATA_DIR / "sent_logs"
    
    # Files
    RECIPIENTS_FILE = DATA_DIR / "recipients.json"
    EVENTS_FILE = DATA_DIR / "grant_events.json"
    
    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Email Settings
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Priya Singh")
    EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)
    EMAIL_REPLY_TO = os.getenv("EMAIL_REPLY_TO", EMAIL_FROM)
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
    
    # Rate Limiting
    RATE_LIMIT = int(os.getenv("EMAIL_RATE_LIMIT", "10"))
    BATCH_SIZE = int(os.getenv("EMAIL_BATCH_SIZE", "50"))
    BATCH_PAUSE = int(os.getenv("EMAIL_BATCH_PAUSE", "60"))
    MAX_RETRIES = int(os.getenv("EMAIL_MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("EMAIL_RETRY_DELAY", "5"))

    @classmethod
    def validate_email_config(cls):
        """Validate email configuration"""
        errors = []
        if not cls.EMAIL_USER:
            errors.append("EMAIL_USER not set")
        if not cls.EMAIL_PASSWORD:
            errors.append("EMAIL_PASSWORD not set")
        return errors
