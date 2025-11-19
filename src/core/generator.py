import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import pytz
from dateutil import parser as dateparse

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

from src.utils.config import Config
from src.templates.prompts import (
    SYSTEM_PROMPT_TEXT, 
    EMAIL_GENERATION_PROMPT, 
    EMAIL_TYPES, 
    VALIDATION_RULES
)

IST = pytz.timezone("Asia/Kolkata")

class EmailGenerator:
    """Handles AI-powered email generation using LangChain and Groq"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        self.api_key = api_key or Config.GROQ_API_KEY
        self.model = model or Config.GROQ_MODEL
        self.llm = None
        
        if self.api_key:
            try:
                self.llm = ChatGroq(
                    temperature=0.7,
                    model_name=self.model,
                    groq_api_key=self.api_key,
                    max_tokens=4096,
                    model_kwargs={"response_format": {"type": "json_object"}}
                )
                print(f"🤖 Groq AI initialized with model: {self.model}")
            except Exception as e:
                print(f"⚠️  Failed to initialize Groq AI: {e}")
        else:
            print("⚠️  No Groq API key found. AI features disabled.")

    def generate_email(self, recipient: Dict, event: Dict, day_number: str) -> Dict:
        """Generate email for a specific recipient and event"""
        
        # 1. Pre-flight Validation
        should_send, reason, warnings = self._validate_request(recipient, event)
        
        if not should_send:
            return self._create_blocked_response(recipient, event, day_number, reason, warnings)
            
        # 2. Generate Content (AI or Fallback)
        if self.llm:
            try:
                return self._generate_with_ai(recipient, event, day_number, warnings)
            except Exception as e:
                print(f"⚠️  AI generation failed: {e}, using fallback")
                return self._generate_fallback(recipient, event, day_number, warnings, error=str(e))
        else:
            return self._generate_fallback(recipient, event, day_number, warnings, error="AI disabled")

    def _generate_with_ai(self, recipient: Dict, event: Dict, day_number: str, warnings: List[str]) -> Dict:
        """Generate email using LangChain"""
        
        # Get configuration for this day
        email_config = EMAIL_TYPES.get(str(day_number), EMAIL_TYPES.get("1")) # Default to Day 1 if unknown
        
        # Format the prompt
        prompt_value = EMAIL_GENERATION_PROMPT.format_messages(
            day_number=day_number,
            email_type=email_config.get("type", "Custom"),
            purpose=email_config.get("purpose", "Engage recipient"),
            principle=email_config.get("principle", "Personalized outreach"),
            subject_formula=email_config.get("subject_formula", "Custom subject"),
            structure="\n".join(f"- {item}" for item in email_config.get("structure", [])),
            recipient_json=json.dumps(recipient, indent=2),
            event_json=json.dumps(event, indent=2)
        )
        
        # Add System Message
        messages = [SystemMessage(content=SYSTEM_PROMPT_TEXT)] + prompt_value
        
        # Invoke LLM
        response = self.llm.invoke(messages)
        content = response.content
        
        # Parse JSON
        try:
            # Clean potential markdown code blocks
            if "```" in content:
                content = content.split("```")[1]
                if content.strip().startswith("json"):
                    content = content.strip()[4:]
            
            result = json.loads(content.strip())
            
            # Add metadata
            result["meta"] = self._create_metadata(recipient, event, day_number, "generated")
            result["warnings"] = warnings + result.get("warnings", [])
            
            return result
            
        except json.JSONDecodeError as e:
            return self._generate_fallback(recipient, event, day_number, warnings, error=f"JSON parse error: {e}")

    def _generate_fallback(self, recipient: Dict, event: Dict, day_number: str, warnings: List[str], error: str = None) -> Dict:
        """Deterministic fallback generation"""
        
        email_config = EMAIL_TYPES.get(str(day_number), EMAIL_TYPES.get("1"))
        
        # Simple deterministic logic (ported from brain.py)
        subject = self._get_fallback_subject(recipient, event, day_number)
        body = self._get_fallback_body(recipient, event, day_number)
        
        result = {
            "internal_reasoning": {
                "email_type": email_config.get("type", "Custom"),
                "error": error,
                "match_decision": "send",
                "principle": email_config.get("principle", "Personalized outreach")
            },
            "email": {
                "subject": subject,
                "body": body
            },
            "verification": {
                "all_data_from_json": True,
                "fallback_used": True,
                "personalization_fields": {
                    "name": recipient.get("name"),
                    "email": recipient.get("email"),
                    "organization": recipient.get("organization")
                }
            },
            "warnings": warnings + ([f"Used fallback: {error}"] if error else [])
        }
        
        result["meta"] = self._create_metadata(recipient, event, day_number, "generated")
        return result

    def _validate_request(self, recipient: Dict, event: Dict) -> Tuple[bool, str, List[str]]:
        """Validate if email should be sent"""
        warnings = []
        
        # Basic field validation
        for field in VALIDATION_RULES["required_recipient_fields"]:
            if field not in recipient:
                warnings.append(f"Missing recipient field: {field}")
                
        # Opt-out check
        if recipient.get("opt_out", False):
            return False, "opted_out", ["Recipient opted out"]
            
        # Deadline check
        deadline = event.get("metadata", {}).get("application_deadline")
        if deadline:
            try:
                dt = dateparse.parse(deadline)
                if dt.tzinfo is None: dt = IST.localize(dt)
                if datetime.now(timezone.utc) > dt.astimezone(timezone.utc):
                    return False, "deadline_passed", ["Deadline passed"]
            except:
                warnings.append("Invalid deadline format")
                
        # Topic Match
        r_topics = {t.lower() for t in recipient.get("topics", [])}
        e_tags = {t.lower() for t in event.get("tags", [])}
        overlap = r_topics.intersection(e_tags)
        
        if len(overlap) < VALIDATION_RULES["topic_match_threshold"]["medium"]:
            return False, "no_topic_match", [f"Insufficient overlap: {overlap}"]
            
        return True, "approved", warnings

    def _create_blocked_response(self, recipient: Dict, event: Dict, day: str, reason: str, warnings: List[str]) -> Dict:
        return {
            "meta": self._create_metadata(recipient, event, day, "blocked", reason),
            "email": None,
            "warnings": warnings
        }

    def _create_metadata(self, recipient: Dict, event: Dict, day: str, status: str, reason: str = None) -> Dict:
        return {
            "recipient_id": recipient.get("recipient_id"),
            "event_id": event.get("event_id"),
            "day": day,
            "status": status,
            "reason": reason,
            "generated_at": datetime.now(IST).isoformat()
        }

    # --- Fallback Content Helpers (Simplified) ---
    def _get_fallback_subject(self, r, e, day):
        title = e.get("title", "")
        topics = r.get("topics", ["funding"])
        topic = topics[0].replace("_", " ").title() if topics else "Funding"
        
        subjects = {
            "0": f"You're in! Here's what to expect - {title}",
            "1": f"The #1 mistake that kills 97% of {topic} applications",
            "3": f"Proof: Real organizations getting real grant money - {title}",
            "5": f"I get it... you're skeptical (but read this about {title})",
            "6": f"⏰ Tomorrow: Your {topic} funding breakthrough",
            "7a": f"🔴 Going LIVE in 6 hours - {title}",
            "7b": f"⏰ Starting in 60 minutes (join now)"
        }
        return subjects.get(str(day), f"{title} - Opportunity")

    def _get_fallback_body(self, r, e, day):
        name = r.get("name", "there")
        return f"Hi {name},\n\nThis is a fallback email for Day {day} regarding {e.get('title')}.\n\nPlease check your API key configuration.\n\nBest,\nPriya"
