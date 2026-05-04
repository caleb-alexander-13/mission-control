import os
import logging

logger = logging.getLogger(__name__)


def send_notification(message: str, title: str = "Mission Control", tags: str = "bell",
                     action_url: str = None, action_label: str = None) -> bool:
    try:
        import requests
        topic = os.getenv('NTFY_TOPIC', '')
        if not topic:
            return False

        headers = {"Title": title, "Priority": "high", "Tags": tags}

        # Add action button if provided (for approve/deny)
        if action_url and action_label:
            headers["Action"] = f"{action_url}; label={action_label}; method=POST"

        requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode(),
            headers=headers,
            timeout=5,
        )
        return True
    except Exception as e:
        logger.error(f"ntfy failed: {e}")
        return False
