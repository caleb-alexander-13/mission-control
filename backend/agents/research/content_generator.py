"""Content generation for sports articles based on successful ESPN articles."""

import logging
import sqlite3
import json
import feedparser
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from agent_integrations import score_finding_with_claude

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'


class ContentGenerator:
    """Generates original sports articles based on style analysis of top performing articles."""

    @staticmethod
    def fetch_espn_articles(limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent NFL articles from ESPN."""
        try:
            url = "https://www.espn.com/espn/rss/nfl/news"
            feed = feedparser.parse(url)

            articles = []
            for entry in feed.entries[:limit]:
                articles.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": "ESPN"
                })

            logger.info(f"Fetched {len(articles)} articles from ESPN RSS")
            return articles
        except Exception as e:
            logger.error(f"Error fetching ESPN articles: {e}")
            return []

    @staticmethod
    def analyze_article_style(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze style patterns from top articles."""
        if not articles:
            return {}

        # Extract style characteristics
        style = {
            "avg_title_length": sum(len(a["title"].split()) for a in articles) / len(articles),
            "avg_summary_length": sum(len(a["summary"].split()) for a in articles) / len(articles),
            "common_openings": [],
            "tone_indicators": [],
            "article_topics": [a["title"] for a in articles]
        }

        # Analyze opening patterns
        for article in articles:
            summary = article.get("summary", "")
            if summary:
                first_sentence = summary.split(".")[0] if "." in summary else summary[:100]
                style["common_openings"].append(first_sentence)

            # Detect tone indicators
            summary_lower = summary.lower()
            if any(word in summary_lower for word in ["stunning", "incredible", "dominant", "explosive"]):
                style["tone_indicators"].append("emphatic")
            if any(word in summary_lower for word in ["could", "might", "potentially", "may"]):
                style["tone_indicators"].append("speculative")
            if any(word in summary_lower for word in ["analysis", "expert", "report"]):
                style["tone_indicators"].append("analytical")

        return style

    @staticmethod
    def generate_article(
        finding_topic: str,
        style_analysis: Dict[str, Any],
        inspiration_articles: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Generate an original article based on finding and style analysis."""
        try:
            # Build context for Claude
            article_summaries = "\n".join([
                f"- {a['title']}: {a['summary'][:200]}"
                for a in inspiration_articles[:3]
            ])

            prompt = f"""Generate an original NFL article for GMSeat based on this research finding:

FINDING TOPIC:
{finding_topic}

INSPIRATION (top recent ESPN articles):
{article_summaries}

STYLE GUIDANCE:
- Average title length: {style_analysis.get('avg_title_length', 8):.0f} words
- Average body length: {style_analysis.get('avg_summary_length', 150):.0f} words
- Tone: Mix of {', '.join(set(style_analysis.get('tone_indicators', ['analytical'])))} styles
- Structure: Start with hook, develop insight, end with implication for fans

REQUIREMENTS:
- Write as original GMSeat voice (not ESPN copy)
- 400-600 word article
- Include specific player/team names
- End with key takeaway for fantasy/real-world implications
- Professional, engaging, sports-focused

Output JSON with:
{{"title": "...", "content": "...", "style_notes": "..."}}"""

            # Use Claude to generate
            from anthropic import Anthropic
            client = Anthropic()

            response = client.messages.create(
                model="claude-opus-4-7",
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            import json
            response_text = response.content[0].text

            # Try to extract JSON
            try:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse generated article JSON: {response_text[:200]}")
                return None

        except Exception as e:
            logger.error(f"Error generating article: {e}")
            return None

    @staticmethod
    def save_draft(
        title: str,
        content: str,
        topic: str,
        inspiration_sources: List[str],
        style_analysis: Dict[str, Any]
    ) -> Optional[int]:
        """Save draft article to database."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()

            now = int(datetime.now().timestamp() * 1000)

            cursor.execute('''
                INSERT INTO sports_article_drafts
                (title, content, topic, inspiration_sources, style_analysis, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                content,
                topic,
                json.dumps(inspiration_sources),
                json.dumps(style_analysis),
                'draft',
                now
            ))

            conn.commit()
            draft_id = cursor.lastrowid
            conn.close()

            logger.info(f"Saved draft article {draft_id}: {title}")
            return draft_id

        except Exception as e:
            logger.error(f"Error saving draft: {e}")
            return None

    @staticmethod
    def get_pending_drafts(limit: int = 5) -> List[Dict[str, Any]]:
        """Get draft articles awaiting review."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, title, content, topic, style_analysis, created_at
                FROM sports_article_drafts
                WHERE status = 'draft'
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

            drafts = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return drafts
        except Exception as e:
            logger.error(f"Error fetching drafts: {e}")
            return []

    @staticmethod
    def approve_draft(draft_id: int, feedback: Optional[str] = None) -> bool:
        """Mark draft as approved."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()

            now = int(datetime.now().timestamp() * 1000)

            cursor.execute('''
                UPDATE sports_article_drafts
                SET status = 'approved', reviewed_at = ?, feedback = ?
                WHERE id = ?
            ''', (now, feedback, draft_id))

            conn.commit()
            conn.close()

            logger.info(f"Approved draft {draft_id}")
            return True
        except Exception as e:
            logger.error(f"Error approving draft: {e}")
            return False

    @staticmethod
    def reject_draft(draft_id: int, feedback: str) -> bool:
        """Mark draft as rejected."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()

            now = int(datetime.now().timestamp() * 1000)

            cursor.execute('''
                UPDATE sports_article_drafts
                SET status = 'rejected', reviewed_at = ?, feedback = ?
                WHERE id = ?
            ''', (now, feedback, draft_id))

            conn.commit()
            conn.close()

            logger.info(f"Rejected draft {draft_id}")
            return True
        except Exception as e:
            logger.error(f"Error rejecting draft: {e}")
            return False
