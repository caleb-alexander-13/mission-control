"""GMSeat integration for publishing approved sports articles to NFL War Room."""

import logging
import os
import requests
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'


class GMSeatPublisher:
    """Publish articles to NFL War Room (GMSeat)."""

    @staticmethod
    def get_gmseat_url() -> str:
        """Get GMSeat War Room URL from environment."""
        return os.getenv("GMSEAT_URL", "http://localhost:8000")

    @staticmethod
    def publish_article(
        title: str,
        content: str,
        topic: str,
        draft_id: int,
        inspiration_sources: Optional[list] = None
    ) -> Optional[Dict[str, Any]]:
        """Publish an article to GMSeat War Room."""
        try:
            base_url = GMSeatPublisher.get_gmseat_url()
            url = f"{base_url}/api/war-room/articles"

            payload = {
                "title": title,
                "content": content,
                "topic": topic,
                "inspiration_sources": inspiration_sources or [],
                "gmseat_url": ""
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                article_id = result.get('article_id')
                logger.info(f"Published article to GMSeat War Room: {article_id}")
                return result
            else:
                logger.error(f"GMSeat publish failed ({response.status_code}): {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error publishing to GMSeat: {e}")
            return None

    @staticmethod
    def update_draft_published(draft_id: int, gmseat_url: str) -> bool:
        """Update draft status to published with GMSeat URL."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()

            import time
            now = int(time.time() * 1000)

            cursor.execute('''
                UPDATE sports_article_drafts
                SET status = 'published', gmseat_url = ?, published_at = ?
                WHERE id = ?
            ''', (gmseat_url, now, draft_id))

            conn.commit()
            conn.close()

            logger.info(f"Updated draft {draft_id} status to published")
            return True

        except Exception as e:
            logger.error(f"Error updating draft publish status: {e}")
            return False

    @staticmethod
    def send_notification(title: str, content: str):
        """Send notification that article was published."""
        try:
            from utils.notifications import send_notification
            send_notification(
                f"Published to GMSeat: {title[:60]}...",
                title="📰 Article Published",
                tags="newspaper"
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
