"""Creative R&D agent for design trends and cultural shifts."""

import logging
import time
import os
import feedparser
import requests
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from agent_integrations import score_finding_with_claude

logger = logging.getLogger(__name__)


class CreativeAgent(BaseAgent):
    """Gathers creative industry news from multiple sources and scores findings."""

    def __init__(self):
        super().__init__("creative")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")

    def run_loop(self, interval_seconds: int = 1800) -> None:
        """Run creative agent loop every 30 minutes."""
        self.running = True
        logger.info(f"Starting creative agent loop (interval: {interval_seconds}s)")

        while self.running:
            try:
                findings = self._fetch_findings()
                for finding in findings:
                    self._process_finding(finding)
            except Exception as e:
                logger.error(f"Error in creative agent: {e}", exc_info=True)

            time.sleep(interval_seconds)

    def _fetch_findings(self) -> List[Dict[str, Any]]:
        """Fetch creative industry news from available sources."""
        findings = []

        # Try NewsAPI for entertainment
        if self.newsapi_key:
            try:
                findings.extend(self._fetch_newsapi_entertainment())
            except Exception as e:
                logger.error(f"NewsAPI error: {e}")

        # Try Design RSS (placeholder for design-focused feed)
        try:
            findings.extend(self._fetch_design_feeds())
        except Exception as e:
            logger.error(f"Design feeds error: {e}")

        return findings

    def _fetch_newsapi_entertainment(self) -> List[Dict[str, Any]]:
        """Fetch entertainment news from NewsAPI."""
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "category": "entertainment",
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

        logger.info(f"Fetched {len(findings)} entertainment articles from NewsAPI")
        return findings

    def _fetch_design_feeds(self) -> List[Dict[str, Any]]:
        """Fetch design trends from available RSS feeds."""
        # Placeholder for design-focused RSS feeds
        findings = []
        try:
            # Try fetching from design blogs or trends
            urls = [
                "https://feeds.arstechnica.com/arstechnica/index",
            ]
            for url in urls:
                feed = feedparser.parse(url)
                for entry in feed.entries[:3]:
                    findings.append({
                        "text": entry.get("title", ""),
                        "source_url": entry.get("link"),
                        "source_name": "Design Resources"
                    })
        except Exception as e:
            logger.error(f"Design feeds error: {e}")

        return findings

    def _process_finding(self, finding: Dict[str, Any]) -> None:
        """Score and store a finding."""
        try:
            score = score_finding_with_claude(finding["text"], "creative")
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
        if "design" in text_lower or "ui" in text_lower:
            return "design_trend"
        elif "trend" in text_lower:
            return "trend"
        elif "award" in text_lower or "winner" in text_lower:
            return "award"
        elif "tool" in text_lower or "software" in text_lower:
            return "creative_tool"
        return "creative_news"
