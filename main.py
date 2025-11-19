import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict

# Add current directory to path so we can import src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.core.generator import EmailGenerator
from src.core.sender import EmailSender

def load_data():
    """Load recipients and events"""
    print(f"📂 Loading data...")
    try:
        with open(Config.RECIPIENTS_FILE, 'r', encoding='utf-8') as f:
            recipients = json.load(f)
        with open(Config.EVENTS_FILE, 'r', encoding='utf-8') as f:
            events = json.load(f)
        print(f"   ✅ {len(recipients)} recipients")
        print(f"   ✅ {len(events)} events")
        return recipients, events
    except FileNotFoundError as e:
        print(f"❌ Error loading data: {e}")
        sys.exit(1)

def save_generated_emails(day: str, emails: List[Dict]):
    """Save generated emails to JSON"""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    output_file = Config.OUTPUT_DIR / f"day_{day}_emails.json"
    
    data = {
        "day": day,
        "generated_at": datetime.now().isoformat(),
        "statistics": {
            "total": len(emails),
            "generated": sum(1 for e in emails if e["meta"]["status"] == "generated"),
            "blocked": sum(1 for e in emails if e["meta"]["status"] == "blocked")
        },
        "emails": emails
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"   💾 Saved to: {output_file}")
    return output_file

def prepare_emails_for_sending(generated_emails: List[Dict]) -> List[Dict]:
    """Convert generated output to sendable format"""
    sendable = []
    for item in generated_emails:
        if item.get("meta", {}).get("status") != "generated":
            continue
            
        email_content = item.get("email", {})
        verification = item.get("verification", {})
        personalization = verification.get("personalization_fields", {})
        
        if email_content and email_content.get("subject") and email_content.get("body"):
            sendable.append({
                "recipient_email": personalization.get("email"),
                "recipient_name": personalization.get("name"),
                "subject": email_content.get("subject"),
                "body": email_content.get("body"),
                "meta": item.get("meta")
            })
    return sendable

def main():
    parser = argparse.ArgumentParser(description="Email Generator & Sender (Modular + LangChain)")
    parser.add_argument("--day", type=str, required=True, help="Day number (0, 1, 3, 5, 6, 7a, 7b)")
    parser.add_argument("--send", action="store_true", help="Actually send the emails (default: generate only)")
    parser.add_argument("--preview", action="store_true", help="Dry run for sending (simulate sending)")
    
    args = parser.parse_args()
    
    # 1. Load Data
    recipients, events = load_data()
    
    # 2. Initialize Generator
    generator = EmailGenerator()
    
    # 3. Generate Emails
    print(f"\n🚀 Generating Day {args.day} emails...")
    generated_results = []
    
    for recipient in recipients:
        # For demo, we match each recipient with the first event (or logic to match all)
        # Assuming 1-to-many or 1-to-1. Let's do all pairs like original.
        for event in events:
            result = generator.generate_email(recipient, event, args.day)
            generated_results.append(result)
            
            status = result["meta"]["status"]
            name = recipient.get("name")
            if status == "generated":
                print(f"   ✅ Generated for {name}")
            else:
                print(f"   ⛔ Blocked for {name}: {result['meta']['reason']}")

    # 4. Save Results
    save_generated_emails(args.day, generated_results)
    
    # 5. Send Emails (if requested)
    if args.send or args.preview:
        sendable_emails = prepare_emails_for_sending(generated_results)
        
        if not sendable_emails:
            print("\n⚠️  No valid emails to send.")
            return
            
        print(f"\n📤 Preparing to send {len(sendable_emails)} emails...")
        sender = EmailSender(dry_run=args.preview)
        sender.send_batch(sendable_emails)
        
    else:
        print("\n✨ Generation complete. Use --send to send emails.")

if __name__ == "__main__":
    main()
