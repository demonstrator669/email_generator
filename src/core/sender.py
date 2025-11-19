import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Tuple, Optional

from src.utils.config import Config

class EmailSender:
    """Handles SMTP email sending with rate limiting and retry logic"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.stats = {
            "attempted": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0
        }
        
        if not dry_run:
            errors = Config.validate_email_config()
            if errors:
                raise ValueError(f"Invalid email configuration:\n" + "\n".join(f"  • {e}" for e in errors))

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and authenticate SMTP connection"""
        smtp = smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT, timeout=30)
        smtp.ehlo()
        
        if Config.EMAIL_USE_TLS:
            smtp.starttls()
            smtp.ehlo()
        
        smtp.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
        return smtp

    def send_batch(self, emails: List[Dict]) -> Dict:
        """Send a batch of emails"""
        
        if not emails:
            print("⚠️  No emails to send")
            return self.stats
            
        print(f"\n📧 {'[DRY RUN] ' if self.dry_run else ''}Sending {len(emails)} emails...")
        
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
                
                # Extract data
                to_email = email_data.get("recipient_email")
                to_name = email_data.get("recipient_name", "there")
                subject = email_data.get("subject")
                body = email_data.get("body")
                
                if not to_email or not subject or not body:
                    print(f"   ⛔ [{idx}/{len(emails)}] Skipped: Missing fields")
                    self.stats["skipped"] += 1
                    continue
                    
                # Send
                success, error = self._send_single_with_retry(to_email, to_name, subject, body, smtp_connection)
                
                if success:
                    self.stats["sent"] += 1
                    print(f"   ✅ [{idx}/{len(emails)}] Sent to {to_name} ({to_email})")
                else:
                    self.stats["failed"] += 1
                    print(f"   ❌ [{idx}/{len(emails)}] Failed to {to_name}: {error}")
                
                # Rate Limiting
                if not self.dry_run and idx < len(emails):
                    if idx % Config.BATCH_SIZE == 0:
                        print(f"   ⏸️  Batch pause: {Config.BATCH_PAUSE}s...")
                        time.sleep(Config.BATCH_PAUSE)
                    else:
                        time.sleep(60.0 / Config.RATE_LIMIT if Config.RATE_LIMIT > 0 else 0)
                        
        finally:
            if smtp_connection:
                try:
                    smtp_connection.quit()
                    print("   ✅ SMTP connection closed")
                except:
                    pass
                    
        return self.stats

    def _send_single_with_retry(self, to_email, to_name, subject, body, smtp) -> Tuple[bool, Optional[str]]:
        """Send single email with retry"""
        if self.dry_run:
            return True, None
            
        for attempt in range(1, Config.MAX_RETRIES + 1):
            try:
                msg = MIMEMultipart("alternative")
                msg["From"] = f"{Config.EMAIL_FROM_NAME} <{Config.EMAIL_FROM}>"
                msg["To"] = f"{to_name} <{to_email}>"
                msg["Subject"] = subject
                msg["Reply-To"] = Config.EMAIL_REPLY_TO
                msg.attach(MIMEText(body, "plain", "utf-8"))
                
                smtp.send_message(msg)
                return True, None
                
            except Exception as e:
                if attempt < Config.MAX_RETRIES:
                    time.sleep(Config.RETRY_DELAY)
                else:
                    return False, str(e)
        return False, "Max retries exceeded"
