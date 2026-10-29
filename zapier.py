"""
Zapier Webhook integration module.
"""

import time
import requests
from typing import Dict, Any, Tuple

def send_zapier_webhook(
    webhook_url: str, payload: Dict[str, Any], max_retries: int = 3
) -> Tuple[bool, str]:
    if not webhook_url:
        return False, "Webhook URL not configured in secrets."

    headers = {"Content-Type": "application/json"}
    backoff = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201, 202]:
                return True, f"Triggered successfully (Status {response.status_code})"
            else:
                msg = f"Zapier HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            msg = f"Network error: {str(e)}"

        if attempt < max_retries:
            time.sleep(backoff)
            backoff *= 2.0

    return False, f"Failed after {max_retries} attempts. Last log: {msg}"
