#!/usr/bin/env python3
"""
test_send_email.py - Send one test email to each recipient
"""

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys

# Load environment variables
def load_env():
    """Load environment variables from .env file"""
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present and handle comments
                        if '"' in value:
                            value = value.split('"')[1]
                        elif "'" in value:
                            value = value.split("'")[1]
                        else:
                            # Remove trailing comments
                            value = value.split('#')[0].strip()
                        env_vars[key] = value
    return env_vars

# Load environment
env = load_env()

EMAIL_HOST = env.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(env.get('EMAIL_PORT', '587'))
EMAIL_USER = env.get('EMAIL_USER', '')
EMAIL_PASSWORD = env.get('EMAIL_PASSWORD', '')
EMAIL_FROM_NAME = env.get('EMAIL_FROM_NAME', 'Sender')
EMAIL_FROM = env.get('EMAIL_FROM', EMAIL_USER)
EMAIL_RATE_LIMIT = int(env.get('EMAIL_RATE_LIMIT', '10'))

print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 TEST EMAIL SENDER - Russell Brunson 7-Day Framework
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# Validate configuration
if not EMAIL_USER or not EMAIL_PASSWORD:
    print("❌ ERROR: EMAIL_USER and EMAIL_PASSWORD must be set in .env file")
    sys.exit(1)

print(f"✅ Configuration loaded:")
print(f"   • Email Host: {EMAIL_HOST}:{EMAIL_PORT}")
print(f"   • From: {EMAIL_FROM_NAME} <{EMAIL_FROM}>")
print(f"   • Rate Limit: {EMAIL_RATE_LIMIT} emails/minute\n")

# Load recipients and events
print(f"📂 Loading data...")
with open('data/recipients.json', 'r') as f:
    recipients = json.load(f)
print(f"   ✅ Loaded {len(recipients)} recipients")

with open('data/grant_events.json', 'r') as f:
    events = json.load(f)
print(f"   ✅ Loaded {len(events)} events\n")

# Prepare test emails (one to each recipient, using first event and Day 1 template)
test_emails = []

for recipient in recipients:
    name = recipient.get('name', 'there')
    email = recipient.get('email', '')
    org = recipient.get('organization', 'your organization')
    topics = recipient.get('topics', ['funding'])
    
    if not email:
        print(f"⚠️  Skipping {name} - no email address")
        continue
    
    # Use first event
    event = events[0] if events else {}
    title = event.get('title', 'this opportunity')
    organizer = event.get('organizer', 'the organizer')
    amount = event.get('metadata', {}).get('amount_range', 'grants available')
    deadline = event.get('metadata', {}).get('application_deadline', 'the deadline')
    topic_str = topics[0].replace("_", " ").title()
    
    # Day 1 Subject and Body
    subject = f"The #1 mistake that kills 97% of {topic_str.lower()} applications"
    
    body = f"""Hi {name},

In my work with {org}-like organizations, I see the same pattern over and over.

The #1 mistake that kills 97% of {topic_str.lower()} applications isn't lack of merit. It's not even lack of funding sources.

It's applying to opportunities without understanding what funders actually want to see.

Most organizations scramble at the last minute, missing the nuances that make their application stand out. They don't realize that {title} — happening soon — is specifically designed to teach exactly this.

That's why I wanted to personally reach out.

{title} is happening with {organizer}, and they're revealing insider strategies funders use to evaluate applications. Grant amounts: {amount}. Application deadline: {deadline}.

This could be the turning point for your next funding cycle.

Mark your calendar. More details tomorrow.

Best regards,

Priya Singh
Grants Coordinator
Funding Forward

---
This is a test email for demonstration purposes.
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    test_emails.append({
        'recipient_name': name,
        'recipient_email': email,
        'subject': subject,
        'body': body
    })

print(f"📧 Prepared {len(test_emails)} test emails:\n")
for email_data in test_emails:
    print(f"   ✅ {email_data['recipient_name']} <{email_data['recipient_email']}>")

print(f"\n{'━'*80}")
print(f"📤 SENDING TEST EMAILS...")
print(f"{'━'*80}\n")

# Send emails
sent_count = 0
failed_count = 0
log_dir = "./data/sent_logs"
os.makedirs(log_dir, exist_ok=True)

sent_log = []

try:
    # Connect to SMTP server
    print(f"🔌 Connecting to {EMAIL_HOST}:{EMAIL_PORT}...")
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    print(f"✅ Connected and authenticated\n")
    
    # Send each email
    for email_data in test_emails:
        try:
            recipient_email = email_data['recipient_email']
            recipient_name = email_data['recipient_name']
            subject = email_data['subject']
            body = email_data['body']
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
            msg['To'] = recipient_email
            
            # Add body as plain text
            msg.attach(MIMEText(body, 'plain'))
            
            # Send
            server.send_message(msg)
            
            sent_count += 1
            status = "✅ SENT"
            print(f"{status}  {recipient_name} <{recipient_email}>")
            
            sent_log.append({
                'timestamp': datetime.now().isoformat(),
                'recipient_name': recipient_name,
                'recipient_email': recipient_email,
                'subject': subject,
                'status': 'sent'
            })
            
        except Exception as e:
            failed_count += 1
            status = "❌ FAILED"
            print(f"{status}  {email_data['recipient_name']} - {str(e)}")
            
            sent_log.append({
                'timestamp': datetime.now().isoformat(),
                'recipient_name': email_data['recipient_name'],
                'recipient_email': email_data['recipient_email'],
                'subject': email_data['subject'],
                'status': 'failed',
                'error': str(e)
            })
    
    server.quit()
    
except Exception as e:
    print(f"\n❌ Connection error: {e}")
    failed_count = len(test_emails)

# Save log
log_file = os.path.join(log_dir, f"test_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
with open(log_file, 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'total': len(test_emails),
        'sent': sent_count,
        'failed': failed_count,
        'emails': sent_log
    }, f, indent=2)

print(f"\n{'━'*80}")
print(f"📊 SUMMARY")
print(f"{'━'*80}")
print(f"   Total:  {len(test_emails)}")
print(f"   Sent:   {sent_count} ✅")
print(f"   Failed: {failed_count} ❌")
print(f"\n   📝 Log saved to: {log_file}")
print(f"\n✅ Test email sending complete!\n")
