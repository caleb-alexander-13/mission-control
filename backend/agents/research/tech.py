"""Tech R&D agent for security vulnerabilities and tech breakthroughs."""

import logging
import time
import os
import feedparser
import requests
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from agent_integrations import score_finding_with_claude

logger = logging.getLogger(__name__)


class TechAgent(BaseAgent):
    """Gathers tech news from multiple sources and scores findings."""

    def __init__(self):
        super().__init__("tech")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")

    def run_loop(self, interval_seconds: int = 1800) -> None:
        """Run tech agent loop every 30 minutes."""
        self.running = True
        logger.info(f"Starting tech agent loop (interval: {interval_seconds}s)")

        while self.running:
            try:
                findings = self._fetch_findings()
                for finding in findings:
                    self._process_finding(finding)
            except Exception as e:
                logger.error(f"Error in tech agent: {e}", exc_info=True)

            time.sleep(interval_seconds)

    def _fetch_findings(self) -> List[Dict[str, Any]]:
        """Fetch tech news from available sources."""
        findings = []

        # Try NewsAPI for tech news
        if self.newsapi_key:
            try:
                findings.extend(self._fetch_newsapi_tech())
            except Exception as e:
                logger.error(f"NewsAPI error: {e}")

        # Try Hacker News
        try:
            findings.extend(self._fetch_hacker_news())
        except Exception as e:
            logger.error(f"Hacker News error: {e}")

        # Try tech RSS feeds
        try:
            findings.extend(self._fetch_tech_rss())
        except Exception as e:
            logger.error(f"Tech RSS error: {e}")

        return findings

    def _fetch_newsapi_tech(self) -> List[Dict[str, Any]]:
        """Fetch tech news from NewsAPI."""
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "category": "technology",
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

        logger.info(f"Fetched {len(findings)} tech articles from NewsAPI")
        return findings

    def _fetch_hacker_news(self) -> List[Dict[str, Any]]:
        """Fetch top stories from Hacker News."""
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        story_ids = response.json()[:5]

        findings = []
        for story_id in story_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            story_response = requests.get(story_url, timeout=10)
            story_response.raise_for_status()
            story = story_response.json()

            findings.append({
                "text": story.get("title", ""),
                "source_url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                "source_name": "Hacker News"
            })

        logger.info(f"Fetched {len(findings)} stories from Hacker News")
        return findings

    def _fetch_tech_rss(self) -> List[Dict[str, Any]]:
        """Fetch tech news from RSS feeds."""
        urls = [
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://techcrunch.com/feed/",
        ]

        findings = []
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:3]:
                    findings.append({
                        "text": entry.get("title", ""),
                        "source_url": entry.get("link"),
                        "source_name": feed.feed.get("title", "Tech RSS")
                    })
            except Exception as e:
                logger.error(f"RSS feed error for {url}: {e}")

        logger.info(f"Fetched {len(findings)} articles from tech RSS feeds")
        return findings

    def _process_finding(self, finding: Dict[str, Any]) -> None:
        """Score and store a finding."""
        try:
            score = score_finding_with_claude(finding["text"], "tech")
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
        if "vulnerability" in text_lower or "exploit" in text_lower or "cve" in text_lower:
            return "security_vulnerability"
        elif "zero-day" in text_lower or "critical" in text_lower:
            return "critical_security"
        elif "framework" in text_lower or "library" in text_lower:
            return "new_tool"
        elif "breakthrough" in text_lower or "ai" in text_lower:
            return "breakthrough"
        return "tech_news"
