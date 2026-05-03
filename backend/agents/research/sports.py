"""Sports R&D agent for NFL news and insights."""

import logging
import time
import os
import feedparser
import requests
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from agent_integrations import score_finding_with_claude

logger = logging.getLogger(__name__)


class SportsAgent(BaseAgent):
    """Gathers sports news from multiple sources and scores findings."""

    def __init__(self):
        super().__init__("sports")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")

    def run_loop(self, interval_seconds: int = 1800) -> None:
        """Run sports agent loop every 30 minutes."""
        self.running = True
        logger.info(f"Starting sports agent loop (interval: {interval_seconds}s)")

        while self.running:
            try:
                findings = self._fetch_findings()
                for finding in findings:
                    self._process_finding(finding)
            except Exception as e:
                logger.error(f"Error in sports agent: {e}", exc_info=True)

            time.sleep(interval_seconds)

    def _fetch_findings(self) -> List[Dict[str, Any]]:
        """Fetch sports news from available sources."""
        findings = []

        # Try NewsAPI for sports news
        if self.newsapi_key:
            try:
                findings.extend(self._fetch_newsapi_sports())
            except Exception as e:
                logger.error(f"NewsAPI error: {e}")

        # Try ESPN RSS
        try:
            findings.extend(self._fetch_espn_rss())
        except Exception as e:
            logger.error(f"ESPN RSS error: {e}")

        return findings

    def _fetch_newsapi_sports(self) -> List[Dict[str, Any]]:
        """Fetch sports news from NewsAPI."""
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "NFL sports",
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": self.newsapi_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        findings = []
        for article in data.get("articles", [])[:5]:
            findings.append({
                "text": article.get("title", "") + " " + article.get("description", ""),
                "source_url": article.get("url"),
                "source_name": "NewsAPI"
            })

        logger.info(f"Fetched {len(findings)} sports articles from NewsAPI")
        return findings

    def _fetch_espn_rss(self) -> List[Dict[str, Any]]:
        """Fetch sports news from ESPN RSS feed."""
        url = "https://www.espn.com/espn/rss/nfl/news"
        feed = feedparser.parse(url)

        findings = []
        for entry in feed.entries[:5]:
            findings.append({
                "text": entry.get("title", ""),
                "source_url": entry.get("link"),
                "source_name": "ESPN"
            })

        logger.info(f"Fetched {len(findings)} articles from ESPN RSS")
        return findings

    def _process_finding(self, finding: Dict[str, Any]) -> None:
        """Score and store a finding."""
        try:
            score = score_finding_with_claude(finding["text"], "sports")

            # Categorize based on content
            category = self._categorize(finding["text"])

            self._insert_research_finding(
                finding_text=finding["text"][:500],
                source_url=finding.get("source_url"),
                source_name=finding.get("source_name"),
                importance_score=score,
                category=category
            )
        except Exception as e:
            logger.error(f"Error processing finding: {e}")

    def _categorize(self, text: str) -> str:
        """Categorize finding based on content."""
        text_lower = text.lower()
        if "injury" in text_lower or "injured" in text_lower:
            return "injury"
        elif "trade" in text_lower:
            return "trade"
        elif "draft" in text_lower:
            return "draft"
        elif "rule" in text_lower:
            return "rule_change"
        return "news"
