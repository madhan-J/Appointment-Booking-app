"""
App configuration, discipline registry, extra fields, and timezone rules.
Adding a new discipline only requires adding an entry to DISCIPLINES below.
"""

from typing import Dict, Any

DEFAULT_TIMEZONE = "Asia/Kolkata"
ADMIN_PASSWORD_DEFAULT = "admin123"

NOTIFICATION_CHANNELS = ["Email", "SMS", "WhatsApp"]

STATUS_CONFIRMED = "Confirmed"
STATUS_RESCHEDULED = "Rescheduled"
STATUS_COMPLETED = "Completed"
STATUS_NO_SHOW = "No-show"
STATUS_CANCELLED = "Cancelled"

BOOKING_STATUSES = [
    STATUS_CONFIRMED,
    STATUS_RESCHEDULED,
    STATUS_COMPLETED,
    STATUS_NO_SHOW,
    STATUS_CANCELLED,
]

DISCIPLINES: Dict[str, Dict[str, Any]] = {
    "Clinic": {
        "label": "Medical & Healthcare",
        "icon": "🩺",
        "description": "Book doctor consultations, health checkups, and diagnostic visits.",
        "extra_fields": [
            {"name": "symptoms", "label": "Primary Symptoms / Reason for Visit", "type": "textarea", "required": True},
            {"name": "age", "label": "Patient Age", "type": "number", "required": True},
            {"name": "is_first_visit", "label": "First time visiting this clinic?", "type": "checkbox", "required": False},
        ],
    },
    "Salon": {
        "label": "Hair & Beauty Salon",
        "icon": "✂️",
        "description": "Haircuts, styling, spa, manicure, and grooming services.",
        "extra_fields": [
            {"name": "hair_type", "label": "Hair Type / Style Preference", "type": "text", "required": False},
            {"name": "stylist_notes", "label": "Special Requests / Allergies", "type": "textarea", "required": False},
        ],
    },
    "College Counselling": {
        "label": "Academic & Career Counselling",
        "icon": "🎓",
        "description": "Schedule sessions with academic advisors, mentors, and career counsellors.",
        "extra_fields": [
            {"name": "roll_number", "label": "Student Roll Number / ID", "type": "text", "required": True},
            {"name": "department", "label": "Department / Major", "type": "text", "required": True},
            {"name": "topic", "label": "Discussion Topic (e.g. Thesis, Electives)", "type": "text", "required": True},
        ],
    },
    "Lab & Equipment": {
        "label": "Lab & Equipment Booking",
        "icon": "🔬",
        "description": "Reserve specialized research instruments and lab stations.",
        "extra_fields": [
            {"name": "project_code", "label": "Research Project Code", "type": "text", "required": True},
            {"name": "equipment_name", "label": "Equipment / Station ID", "type": "text", "required": True},
            {"name": "safety_certified", "label": "I have completed mandatory lab safety training", "type": "checkbox", "required": True},
        ],
    },
    "General Services": {
        "label": "General Professional Services",
        "icon": "💼",
        "description": "Consulting, legal support, financial planning, and general maintenance.",
        "extra_fields": [
            {"name": "service_purpose", "label": "Brief Description of Request", "type": "textarea", "required": True}
        ],
    },
}
