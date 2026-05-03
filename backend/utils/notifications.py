import os
import logging

logger = logging.getLogger(__name__)


def send_notification(message: str, title: str = "Mission Control", tags: str = "bell") -> bool:
    try:
        import requests
        topic = os.getenv('NTFY_TOPIC', '')
        if not topic:
            return False
        requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode(),
            headers={"Title": title, "Priority": "high", "Tags": tags},
            timeout=5,
        )
        return True
    except Exception as e:
        logger.error(f"ntfy failed: {e}")
        return False
