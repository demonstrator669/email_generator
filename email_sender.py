"""
email_sender.py - Send Generated Emails via SMTP

Supports:
- Gmail, Outlook, custom SMTP
- Rate limiting to avoid spam filters
- Delivery tracking
- Retry logic for failed sends

Setup:
1. Set environment variables:
   export EMAIL_HOST="smtp.gmail.com"
   export EMAIL_PORT="587"
   export EMAIL_USER="your-email@gmail.com"
   export EMAIL_PASSWORD="your-app-password"
   export EMAIL_FROM_NAME="Priya Singh"

2. For Gmail: Use App Password (https://myaccount.google.com/apppasswords)
   Not your regular Gmail password!

Usage:
    python email_sender.py --day 1                    # Send Day 1 emails
    python email_sender.py --day 1 --dry-run          # Test without sending
    python email_sender.py --file day_1_emails.json   # Send from specific file
"""

import json
import os
import time
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import pytz

IST = pytz.timezone("Asia/Kolkata")


# =============================
# Configuration
# =============================
class EmailConfig:
    """Email configuration from environment variables"""
    
    # SMTP Settings
    HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    PORT = int(os.getenv("EMAIL_PORT", "587"))
    USER = os.getenv("EMAIL_USER")
    PASSWORD = os.getenv("EMAIL_PASSWORD")
    USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
    
    # Sender Info
    FROM_EMAIL = os.getenv("EMAIL_FROM", USER)
    FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Priya Singh")
    REPLY_TO = os.getenv("EMAIL_REPLY_TO", FROM_EMAIL)
    
    # Rate Limiting (to avoid spam filters)
    RATE_LIMIT = int(os.getenv("EMAIL_RATE_LIMIT", "10"))  # emails per minute
    BATCH_SIZE = int(os.getenv("EMAIL_BATCH_SIZE", "50"))  # pause after this many
    BATCH_PAUSE = int(os.getenv("EMAIL_BATCH_PAUSE", "60"))  # seconds to pause
    
    # Retry Logic
    MAX_RETRIES = int(os.getenv("EMAIL_MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("EMAIL_RETRY_DELAY", "5"))  # seconds
    
    # Paths
    INPUT_DIR = os.getenv("EMAIL_INPUT_DIR", "./data/generated")
    LOG_DIR = os.getenv("EMAIL_LOG_DIR", "./data/sent_logs")
    
    @classmethod
    def validate(cls) -> Tuple[bool, List[str]]:
        """Validate configuration"""
        errors = []
        
        if not cls.USER:
            errors.append("EMAIL_USER not set")
        if not cls.PASSWORD:
            errors.append("EMAIL_PASSWORD not set")
        if not cls.FROM_EMAIL:
            errors.append("EMAIL_FROM not set")
        
        return len(errors) == 0, errors


# =============================
# Email Sender
# =============================
class EmailSender:
    """Handles SMTP email sending with rate limiting and retry logic"""
    
    def __init__(self, config: EmailConfig = EmailConfig, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.stats = {
            "attempted": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0
        }
        
        if not dry_run:
            is_valid, errors = config.validate()
            if not is_valid:
                raise ValueError(f"Invalid email configuration:\n" + "\n".join(f"  • {e}" for e in errors))
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and authenticate SMTP connection"""
        smtp = smtplib.SMTP(self.config.HOST, self.config.PORT, timeout=30)
        smtp.ehlo()
        
        if self.config.USE_TLS:
            smtp.starttls()
            smtp.ehlo()
        
        smtp.login(self.config.USER, self.config.PASSWORD)
        return smtp
    
    def _build_email_message(self, to_email: str, to_name: str, subject: str, body: str) -> MIMEMultipart:
        """Build email message with proper headers"""
        msg = MIMEMultipart("alternative")
        
        msg["From"] = f"{self.config.FROM_NAME} <{self.config.FROM_EMAIL}>"
        msg["To"] = f"{to_name} <{to_email}>"
        msg["Subject"] = subject
        msg["Reply-To"] = self.config.REPLY_TO
        
        # Add plain text body
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        return msg
    
    def send_single_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
        smtp_connection: Optional[smtplib.SMTP] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Send a single email
        
        Returns: (success, error_message)
        """
        
        if self.dry_run:
            print(f"   [DRY RUN] Would send to: {to_email}")
            print(f"             Subject: {subject}")
            return True, None
        
        close_connection = False
        if smtp_connection is None:
            smtp_connection = self._create_smtp_connection()
            close_connection = True
        
        try:
            msg = self._build_email_message(to_email, to_name, subject, body)
            smtp_connection.send_message(msg)
            
            if close_connection:
                smtp_connection.quit()
            
            return True, None
            
        except Exception as e:
            if close_connection and smtp_connection:
                try:
                    smtp_connection.quit()
                except:
                    pass
            
            return False, str(e)
    
    def send_with_retry(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
        smtp_connection: Optional[smtplib.SMTP] = None
    ) -> Tuple[bool, Optional[str], int]:
        """
        Send email with retry logic
        
        Returns: (success, error_message, attempts)
        """
        
        for attempt in range(1, self.config.MAX_RETRIES + 1):
            success, error = self.send_single_email(to_email, to_name, subject, body, smtp_connection)
            
            if success:
                return True, None, attempt
            
            if attempt < self.config.MAX_RETRIES:
                print(f"      ⚠️  Attempt {attempt} failed: {error}. Retrying in {self.config.RETRY_DELAY}s...")
                time.sleep(self.config.RETRY_DELAY)
            else:
                return False, error, attempt
        
        return False, "Max retries exceeded", self.config.MAX_RETRIES
    
    def send_batch(self, emails: List[Dict]) -> Dict:
        """
        Send a batch of emails with rate limiting
        
        Args:
            emails: List of email dicts with keys: recipient_email, recipient_name, subject, body
        
        Returns: Statistics dict
        """
        
        if not emails:
            print("⚠️  No emails to send")
            return self.stats
        
        print(f"\n📧 {'[DRY RUN] ' if self.dry_run else ''}Sending {len(emails)} emails...")
        if not self.dry_run:
            print(f"   Rate limit: {self.config.RATE_LIMIT} emails/minute")
            print(f"   Batch size: {self.config.BATCH_SIZE} (pause {self.config.BATCH_PAUSE}s after)")
        
        # Calculate delay between emails
        delay_between = 60.0 / self.config.RATE_LIMIT if self.config.RATE_LIMIT > 0 else 0
        
        smtp_connection = None
        if not self.dry_run:
            try:
                smtp_connection = self._create_smtp_connection()
                print("   ✅ SMTP connection established")
            except Exception as e:
                print(f"   ❌ Failed to connect to SMTP: {e}")
                return self.stats
        
        try:
            for idx, email_data in enumerate(emails, 1):
                self.stats["attempted"] += 1
                
                # Extract email details
                to_email = email_data.get("recipient_email")
                to_name = email_data.get("recipient_name", "there")
                subject = email_data.get("subject")
                body = email_data.get("body")
                
                if not to_email or not subject or not body:
                    print(f"   ⛔ [{idx}/{len(emails)}] Skipped: Missing required fields")
                    self.stats["skipped"] += 1
                    continue
                
                # Send email
                success, error, attempts = self.send_with_retry(
                    to_email, to_name, subject, body, smtp_connection
                )
                
                if success:
                    self.stats["sent"] += 1
                    print(f"   ✅ [{idx}/{len(emails)}] Sent to {to_name} ({to_email})")
                else:
                    self.stats["failed"] += 1
                    print(f"   ❌ [{idx}/{len(emails)}] Failed to {to_name}: {error}")
                
                # Rate limiting
                if idx < len(emails):  # Don't delay after last email
                    if idx % self.config.BATCH_SIZE == 0:
                        print(f"   ⏸️  Batch pause: {self.config.BATCH_PAUSE}s...")
                        time.sleep(self.config.BATCH_PAUSE)
                    elif delay_between > 0:
                        time.sleep(delay_between)
        
        finally:
            if smtp_connection:
                try:
                    smtp_connection.quit()
                    print("   ✅ SMTP connection closed")
                except:
                    pass
        
        return self.stats


# =============================
# Load & Transform Generated Emails
# =============================
def load_generated_emails(file_path: str) -> List[Dict]:
    """
    Load generated emails from JSON and transform to sendable format
    
    Returns: List of dicts with recipient_email, recipient_name, subject, body
    """
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    emails = []
    
    for item in data.get("emails", []):
        # Skip blocked emails
        if item.get("meta", {}).get("status") != "generated":
            continue
        
        # Skip if no email content
        if not item.get("email") or not item["email"].get("subject") or not item["email"].get("body"):
            continue
        
        # Extract recipient info from verification or meta
        verification = item.get("verification", {})
        personalization = verification.get("personalization_fields", {})
        
        email_dict = {
            "recipient_email": personalization.get("email", "MISSING"),
            "recipient_name": personalization.get("name", "there"),
            "subject": item["email"]["subject"],
            "body": item["email"]["body"],
            "meta": item.get("meta", {})
        }
        
        emails.append(email_dict)
    
    return emails


# =============================
# Logging
# =============================
def save_send_log(day: str, stats: Dict, emails_sent: List[Dict], dry_run: bool):
    """Save sending log for tracking"""
    
    os.makedirs(EmailConfig.LOG_DIR, exist_ok=True)
    
    log_file = os.path.join(
        EmailConfig.LOG_DIR,
        f"{'dryrun_' if dry_run else ''}day_{day}_sent_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    log_data = {
        "day": day,
        "dry_run": dry_run,
        "sent_at": datetime.now(IST).isoformat(),
        "statistics": stats,
        "emails": emails_sent
    }
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Log saved: {log_file}")


# =============================
# CLI Interface
# =============================
def main():
    parser = argparse.ArgumentParser(description="Send generated grant emails")
    parser.add_argument("--day", type=str, help="Day number to send (0, 1, 3, 5, 6, 7a, 7b)")
    parser.add_argument("--file", type=str, help="Specific JSON file to send from")
    parser.add_argument("--dry-run", action="store_true", help="Test without actually sending")
    parser.add_argument("--limit", type=int, help="Limit number of emails to send (for testing)")
    
    args = parser.parse_args()
    
    # Determine input file
    if args.file:
        input_file = args.file
    elif args.day:
        input_file = os.path.join(EmailConfig.INPUT_DIR, f"day_{args.day}_emails.json")
    else:
        print("❌ Error: Must specify --day or --file")
        return 1
    
    # Check file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: File not found: {input_file}")
        return 1
    
    print(f"📂 Loading emails from: {input_file}")
    
    try:
        # Load emails
        emails = load_generated_emails(input_file)
        
        if not emails:
            print("⚠️  No valid emails found to send")
            return 1
        
        print(f"   ✅ Found {len(emails)} emails ready to send")
        
        # Apply limit if specified
        if args.limit:
            emails = emails[:args.limit]
            print(f"   ⚠️  Limited to first {args.limit} emails")
        
        # Initialize sender
        sender = EmailSender(dry_run=args.dry_run)
        
        # Send emails
        stats = sender.send_batch(emails)
        
        # Print summary
        print(f"\n📊 SENDING SUMMARY")
        print(f"   Total attempted: {stats['attempted']}")
        print(f"   Successfully sent: {stats['sent']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Skipped: {stats['skipped']}")
        
        # Save log
        save_send_log(args.day or "custom", stats, emails, args.dry_run)
        
        print("\n✅ Email sending complete!")
        
        return 0 if stats['failed'] == 0 else 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())