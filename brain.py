"""
brain.py - Optimized Email Generation Engine with Groq API

Combines deterministic validation logic with AI-powered content generation.
- Validates recipients & events
- Matches topics
- Uses Groq API for high-quality email generation
- Follows Russell Brunson's 7-day framework

Usage:
    python brain.py                    # Generate Day 1 emails (demo)
    python brain.py --all              # Generate all 7 days
    python brain.py --day 3            # Generate specific day
"""

import json
import os
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dateutil import parser as dateparse
import pytz
from groq import Groq

# Import your templates
try:
    from templates import (
        SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE,
        EMAIL_TYPES,
        VALIDATION_RULES
    )
except ImportError:
    print("⚠️  Warning: templates.py not found. Using embedded validation rules.")
    VALIDATION_RULES = {
        "required_recipient_fields": ["recipient_id", "name", "email", "organization", "topics", "engagement_score", "opt_out"],
        "required_event_fields": ["event_id", "title", "start_date", "tags", "organizer", "metadata"],
        "required_metadata_fields": ["amount_range", "application_deadline"],
        "topic_match_threshold": {"high": 2, "medium": 1, "none": 0},
        "engagement_thresholds": {"high": 0.7, "low": 0.5}
    }

IST = pytz.timezone("Asia/Kolkata")


# =============================
# Configuration
# =============================
class Config:
    """Centralized configuration"""
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    USE_AI = os.getenv("USE_AI", "true").lower() == "true"  # Toggle AI on/off
    RECIPIENTS_FILE = "./data/recipients.json"
    EVENTS_FILE = "./data/grant_events.json"
    OUTPUT_DIR = "./data/generated"


# =============================
# Groq AI Integration
# =============================
class GroqEmailGenerator:
    """Handles AI-powered email generation using Groq"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        self.api_key = api_key or Config.GROQ_API_KEY
        self.model = model or Config.GROQ_MODEL
        
        if not self.api_key:
            raise ValueError(
                "Groq API key required!\n"
                "Get one free at: https://console.groq.com/keys\n"
                "Then set: export GROQ_API_KEY='your-key-here'"
            )
        
        self.client = Groq(api_key=self.api_key)
        print(f"🤖 Groq AI initialized with model: {self.model}")
    
    def generate_email_content(self, recipient: Dict, event: Dict, day_number: str) -> Dict:
        """Generate email using Groq API with your templates"""
        
        try:
            # Get email configuration from templates
            email_config = EMAIL_TYPES.get(day_number, EMAIL_TYPES.get(int(day_number), {}))
            
            # Build user prompt
            user_prompt = USER_PROMPT_TEMPLATE.format(
                day_number=day_number,
                email_type=email_config.get("type", "Custom"),
                purpose=email_config.get("purpose", "Engage recipient"),
                principle=email_config.get("principle", "Personalized outreach"),
                subject_formula=email_config.get("subject_formula", "Custom subject"),
                structure="\n".join(f"- {item}" for item in email_config.get("structure", ["Standard email structure"])),
                recipient_json=json.dumps(recipient, indent=2),
                event_json=json.dumps(event, indent=2)
            )
            
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=4096,
                response_format={"type": "json_object"},  # Force JSON
            )
            
            response_text = chat_completion.choices[0].message.content
            
            # Clean and parse JSON
            if response_text.strip().startswith("```"):
                response_text = response_text.strip().split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            return json.loads(response_text.strip())
            
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}")
            return self._fallback_email(recipient, event, day_number, f"JSON parse error: {e}")
        except Exception as e:
            print(f"⚠️  API error: {e}")
            return self._fallback_email(recipient, event, day_number, f"API error: {e}")
    
    def _fallback_email(self, recipient: Dict, event: Dict, day_number: str, error: str) -> Dict:
        """Fallback to deterministic email if API fails"""
        return {
            "internal_reasoning": {
                "email_type": "Fallback",
                "error": error,
                "match_decision": "send"
            },
            "email": {
                "subject": f"{event.get('title')} - Opportunity for {recipient.get('organization')}",
                "body": self._generate_simple_body(recipient, event, day_number)
            },
            "verification": {
                "all_data_from_json": True,
                "fallback_used": True
            },
            "warnings": [f"Used fallback due to: {error}"]
        }
    
    def _generate_simple_body(self, recipient: Dict, event: Dict, day_number: str) -> str:
        """Simple deterministic body for fallback"""
        name = recipient.get("name", "there")
        title = event.get("title", "this opportunity")
        organizer = event.get("organizer", "the organizer")
        amount = event.get("metadata", {}).get("amount_range", "[amount]")
        deadline = event.get("metadata", {}).get("application_deadline", "[deadline]")
        
        return f"""Hi {name},

I wanted to share {title} organised by {organizer}.

Grant amount: {amount}
Application deadline: {deadline}

This may be relevant for your work at {recipient.get('organization', 'your organization')}.

Best regards,

Priya Singh
Grants Coordinator
Funding Forward"""


# =============================
# Validation Functions
# =============================
def validate_recipient(recipient: Dict) -> List[str]:
    """Validate recipient data"""
    errors = []
    for field in VALIDATION_RULES["required_recipient_fields"]:
        if field not in recipient:
            errors.append(f"Missing recipient field: {field}")
    if "topics" in recipient and not isinstance(recipient["topics"], list):
        errors.append("recipient.topics must be a list")
    return errors


def validate_event(event: Dict) -> List[str]:
    """Validate event data"""
    errors = []
    for field in VALIDATION_RULES["required_event_fields"]:
        if field not in event:
            errors.append(f"Missing event field: {field}")
    if "metadata" in event:
        for m in VALIDATION_RULES["required_metadata_fields"]:
            if m not in event["metadata"]:
                errors.append(f"Missing event.metadata field: {m}")
    if "tags" in event and not isinstance(event["tags"], list):
        errors.append("event.tags must be a list")
    return errors


def is_deadline_passed(deadline_str: str) -> Tuple[bool, Optional[str]]:
    """Check if application deadline has passed"""
    try:
        dt = dateparse.parse(deadline_str)
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        dt = dt.astimezone(timezone.utc)
        return datetime.now(timezone.utc) > dt, None
    except Exception as e:
        return False, f"Invalid deadline format: {e}"


def topic_overlap(recipient_topics: List[str], event_tags: List[str]) -> List[str]:
    """Find overlapping topics (case-insensitive)"""
    r_lower = {t.strip().lower() for t in recipient_topics}
    e_lower = {t.strip().lower() for t in event_tags}
    return sorted([t for t in recipient_topics if t.strip().lower() in e_lower])


def should_send_email(recipient: Dict, event: Dict) -> Tuple[bool, str, List[str]]:
    """
    Determine if email should be sent
    Returns: (should_send, reason, warnings)
    """
    warnings = []
    
    # Validate
    r_errors = validate_recipient(recipient)
    e_errors = validate_event(event)
    warnings.extend(r_errors + e_errors)
    
    if r_errors or e_errors:
        return False, "validation_failed", warnings
    
    # Check opt-out
    if recipient.get("opt_out", False):
        return False, "opted_out", ["Recipient has opted out - DO NOT SEND"]
    
    # Check deadline
    deadline = event.get("metadata", {}).get("application_deadline")
    if deadline:
        passed, err = is_deadline_passed(deadline)
        if err:
            warnings.append(err)
        elif passed:
            return False, "deadline_passed", ["Application deadline has passed - DO NOT SEND"]
    
    # Check topic match
    overlap = topic_overlap(recipient.get("topics", []), event.get("tags", []))
    min_match = VALIDATION_RULES["topic_match_threshold"]["medium"]
    
    if len(overlap) < min_match:
        return False, "no_topic_match", [
            f"Insufficient topic overlap. "
            f"Recipient: {recipient.get('topics', [])} | "
            f"Event: {event.get('tags', [])} | "
            f"Overlap: {overlap}"
        ]
    
    return True, "approved", warnings


def tone_from_engagement(score: float) -> str:
    """Select tone based on engagement score"""
    if score >= VALIDATION_RULES["engagement_thresholds"]["high"]:
        return "enthusiastic"
    if score >= VALIDATION_RULES["engagement_thresholds"]["low"]:
        return "professional"
    return "gentle"


# =============================
# Main Generation Logic
# =============================
def generate_email_for_pair(
    recipient: Dict,
    event: Dict,
    day_number: str,
    ai_generator: Optional[GroqEmailGenerator] = None,
    use_ai: bool = True
) -> Dict:
    """
    Generate email for a recipient-event pair
    
    Returns complete email data structure
    """
    
    # Pre-flight checks
    should_send, reason, warnings = should_send_email(recipient, event)
    
    if not should_send:
        return {
            "meta": {
                "recipient_id": recipient.get("recipient_id"),
                "event_id": event.get("event_id"),
                "day": day_number,
                "status": "blocked",
                "reason": reason
            },
            "internal_reasoning": {
                "email_type": "N/A",
                "match_decision": reason,
                "recipient_topics": recipient.get("topics", []),
                "event_tags": event.get("tags", []),
                "topic_overlap": topic_overlap(recipient.get("topics", []), event.get("tags", []))
            },
            "email": None,
            "verification": None,
            "warnings": warnings
        }
    
    # Generate email content
    if use_ai and ai_generator:
        try:
            result = ai_generator.generate_email_content(recipient, event, day_number)
        except Exception as e:
            print(f"⚠️  AI generation failed: {e}, using fallback")
            result = ai_generator._fallback_email(recipient, event, day_number, str(e))
    else:
        # Use fallback (deterministic)
        result = GroqEmailGenerator(api_key="dummy")._fallback_email(recipient, event, day_number, "AI disabled")
    
    # Add metadata
    result["meta"] = {
        "recipient_id": recipient.get("recipient_id"),
        "event_id": event.get("event_id"),
        "day": day_number,
        "status": "generated",
        "generated_at": datetime.now(IST).isoformat(),
        "tone": tone_from_engagement(recipient.get("engagement_score", 0.5)),
        "topic_overlap": topic_overlap(recipient.get("topics", []), event.get("tags", []))
    }
    
    result["warnings"] = warnings + result.get("warnings", [])
    
    return result


# =============================
# Batch Processing
# =============================
def generate_batch(
    recipients_file: str = None,
    events_file: str = None,
    days: List[str] = ["1"],
    output_dir: str = None,
    use_ai: bool = True
) -> Dict[str, Any]:
    """
    Generate emails for all recipient-event pairs across specified days
    """
    
    recipients_file = recipients_file or Config.RECIPIENTS_FILE
    events_file = events_file or Config.EVENTS_FILE
    output_dir = output_dir or Config.OUTPUT_DIR
    
    # Load data
    print(f"\n📂 Loading data...")
    with open(recipients_file, 'r', encoding='utf-8') as f:
        recipients = json.load(f)
    with open(events_file, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    print(f"   ✅ {len(recipients)} recipients")
    print(f"   ✅ {len(events)} events")
    
    # Initialize AI generator if needed
    ai_gen = None
    if use_ai:
        try:
            ai_gen = GroqEmailGenerator()
        except ValueError as e:
            print(f"⚠️  {e}")
            print("   Falling back to deterministic generation")
            use_ai = False
    
    # Statistics
    stats = {
        "total": 0,
        "generated": 0,
        "blocked": 0,
        "by_reason": {}
    }
    
    # Generate for each day
    for day in days:
        print(f"\n📧 Generating Day {day} emails...")
        day_outputs = []
        
        for recipient in recipients:
            for event in events:
                stats["total"] += 1
                
                result = generate_email_for_pair(recipient, event, day, ai_gen, use_ai)
                
                # Update stats
                status = result["meta"]["status"]
                if status == "generated":
                    stats["generated"] += 1
                    print(f"   ✅ {recipient.get('name')} → {event.get('title')}")
                else:
                    stats["blocked"] += 1
                    reason = result["meta"]["reason"]
                    stats["by_reason"][reason] = stats["by_reason"].get(reason, 0) + 1
                    print(f"   ⛔ {recipient.get('name')} → {event.get('title')} ({reason})")
                
                day_outputs.append(result)
        
        # Save day's output
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"day_{day}_emails.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "day": day,
                "generated_at": datetime.now(IST).isoformat(),
                "statistics": {
                    "total": len(day_outputs),
                    "generated": sum(1 for e in day_outputs if e["meta"]["status"] == "generated"),
                    "blocked": sum(1 for e in day_outputs if e["meta"]["status"] == "blocked")
                },
                "emails": day_outputs
            }, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Saved to: {output_file}")
    
    # Final summary
    print(f"\n📊 SUMMARY")
    print(f"   Total pairs: {stats['total']}")
    print(f"   Generated: {stats['generated']}")
    print(f"   Blocked: {stats['blocked']}")
    if stats['by_reason']:
        print(f"   Block reasons:")
        for reason, count in stats['by_reason'].items():
            print(f"      • {reason}: {count}")
    
    return stats


# =============================
# CLI Interface
# =============================
def main():
    parser = argparse.ArgumentParser(description="Generate grant emails using Groq AI")
    parser.add_argument("--day", type=str, help="Generate specific day (0, 1, 3, 5, 6, 7a, 7b)")
    parser.add_argument("--all", action="store_true", help="Generate all 7 days")
    parser.add_argument("--no-ai", action="store_true", help="Use deterministic fallback (no API)")
    parser.add_argument("--recipients", type=str, help="Path to recipients.json")
    parser.add_argument("--events", type=str, help="Path to grant_events.json")
    
    args = parser.parse_args()
    
    # Determine which days to generate
    if args.all:
        days = ["0", "1", "3", "5", "6", "7a", "7b"]
    elif args.day:
        days = [args.day]
    else:
        days = ["1"]  # Default: Day 1 (Indoctrination)
    
    # Run generation
    try:
        generate_batch(
            recipients_file=args.recipients,
            events_file=args.events,
            days=days,
            use_ai=not args.no_ai
        )
        print("\n✅ Generation complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())