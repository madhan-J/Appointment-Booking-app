"""
Conversational Chat Agent using Anthropic API or a rule-based fallback parser.
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

class BookingChatAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key) if (api_key and HAS_ANTHROPIC) else None

    def parse_user_intent(self, text: str) -> Dict[str, Any]:
        if self.client:
            return self._parse_with_llm(text)
        return self._parse_rule_based(text)

    def _parse_with_llm(self, text: str) -> Dict[str, Any]:
        prompt = f"""
Extract booking intent details from user input as JSON.
User Input: "{text}"
Current Date: {datetime.now().strftime("%Y-%m-%d")}
Return ONLY JSON:
{{
  "intent": "book" | "cancel" | "reschedule" | "unknown",
  "discipline": "Clinic" | "Salon" | "College Counselling" | "Lab & Equipment" | "General Services" | null,
  "service": string or null,
  "date": "YYYY-MM-DD" or null,
  "time": "HH:MM" or null,
  "booking_id": string or null
}}
"""
        try:
            res = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return json.loads(res.content[0].text)
        except Exception:
            return self._parse_rule_based(text)

    def _parse_rule_based(self, text: str) -> Dict[str, Any]:
        txt = text.lower()
        res = {"intent": "unknown", "discipline": None, "service": None, "date": None, "time": None, "booking_id": None}

        if any(w in txt for w in ["book", "appointment", "schedule"]): res["intent"] = "book"
        elif any(w in txt for w in ["cancel", "drop"]): res["intent"] = "cancel"
        elif any(w in txt for w in ["reschedule", "change"]): res["intent"] = "reschedule"

        if "doctor" in txt or "clinic" in txt: res["discipline"] = "Clinic"
        elif "hair" in txt or "salon" in txt: res["discipline"] = "Salon"

        today = datetime.now()
        if "tomorrow" in txt: res["date"] = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "today" in txt: res["date"] = today.strftime("%Y-%m-%d")

        return res
