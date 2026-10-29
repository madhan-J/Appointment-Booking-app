"""
Slot calculation and conflict detection logic.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

def generate_time_slots(start_str: str, end_str: str, duration_min: int) -> List[str]:
    fmt = "%H:%M"
    try:
        current = datetime.strptime(start_str, fmt)
        end_time = datetime.strptime(end_str, fmt)
    except ValueError:
        return []

    slots = []
    delta = timedelta(minutes=duration_min)
    while current + delta <= end_time:
        slots.append(current.strftime(fmt))
        current += delta
    return slots

def is_time_overlapping(s1: str, e1: str, s2: str, e2: str) -> bool:
    fmt = "%H:%M"
    start1, end1 = datetime.strptime(s1, fmt), datetime.strptime(e1, fmt)
    start2, end2 = datetime.strptime(s2, fmt), datetime.strptime(e2, fmt)
    return max(start1, start2) < min(end1, end2)

def calculate_end_time(start_time_str: str, duration_min: int) -> str:
    fmt = "%H:%M"
    dt = datetime.strptime(start_time_str, fmt) + timedelta(minutes=duration_min)
    return dt.strftime(fmt)

def get_available_slots(
    provider: Dict[str, Any],
    service_duration: int,
    target_date: str,
    existing_bookings: List[Dict[str, Any]],
    holidays: List[Dict[str, Any]] = None
) -> List[str]:
    target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
    today = datetime.now().date()

    if target_dt < today:
        return []

    day_name = target_dt.strftime("%A")
    working_days = [d.strip() for d in str(provider.get("working_days", "")).split(",")]
    if day_name not in working_days:
        return []

    start_time = str(provider["start_time"])
    end_time = str(provider["end_time"])
    all_slots = generate_time_slots(start_time, end_time, service_duration)

    break_start = str(provider.get("break_start", ""))
    break_end = str(provider.get("break_end", ""))

    available_slots = []
    now = datetime.now()

    for slot in all_slots:
        slot_end = calculate_end_time(slot, service_duration)

        if target_dt == today:
            slot_dt = datetime.combine(today, datetime.strptime(slot, "%H:%M").time())
            if slot_dt <= now:
                continue

        if break_start and break_end:
            if is_time_overlapping(slot, slot_end, break_start, break_end):
                continue

        has_conflict = False
        for b in existing_bookings:
            if b.get("provider_id") == provider["provider_id"] and b.get("date") == target_date:
                if b.get("status") in ["Confirmed", "Rescheduled"]:
                    if is_time_overlapping(slot, slot_end, b["start_time"], b["end_time"]):
                        has_conflict = True
                        break

        if not has_conflict:
            available_slots.append(slot)

    return available_slots
