"""Finance R&D agent for market and financial insights."""

import logging
import time
import os
import re
import feedparser
import requests
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from agent_integrations import score_finding_with_claude

logger = logging.getLogger(__name__)

KNOWN_TICKERS = {
    'AAPL','MSFT','GOOGL','AMZN','TSLA','NVDA','META','JPM','BAC','WMT',
    'NFLX','AMD','INTC','DIS','PYPL','UBER','SNAP','SPOT','CRM','GS','MS'
}
TICKER_RE = re.compile(r'\b([A-Z]{2,5})\b')


class FinanceAgent(BaseAgent):
    """Gathers financial news from multiple sources and scores findings."""

    def __init__(self):
        super().__init__("finance")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")

    def run_loop(self, interval_seconds: int = 1800) -> None:
        """Run finance agent loop every 30 minutes."""
        self.running = True
        logger.info(f"Starting finance agent loop (interval: {interval_seconds}s)")

        while self.running:
            try:
                findings = self._fetch_findings()
                for finding in findings:
                    self._process_finding(finding)
            except Exception as e:
                logger.error(f"Error in finance agent: {e}", exc_info=True)

            time.sleep(interval_seconds)

    def _fetch_findings(self) -> List[Dict[str, Any]]:
        """Fetch financial news from available sources."""
        findings = []

        # Try NewsAPI for business news
        if self.newsapi_key:
            try:
                findings.extend(self._fetch_newsapi_business())
            except Exception as e:
                logger.error(f"NewsAPI error: {e}")

        # Try MarketWatch RSS
        try:
            findings.extend(self._fetch_marketwatch_rss())
        except Exception as e:
            logger.error(f"MarketWatch RSS error: {e}")

        return findings

    def _fetch_newsapi_business(self) -> List[Dict[str, Any]]:
        """Fetch business news from NewsAPI."""
        if not self.newsapi_key:
            return []

        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "category": "business",
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

        logger.info(f"Fetched {len(findings)} business articles from NewsAPI")
        return findings

    def _fetch_marketwatch_rss(self) -> List[Dict[str, Any]]:
        """Fetch financial news from MarketWatch RSS."""
        url = "https://feeds.marketwatch.com/marketwatch/topstories/"
        feed = feedparser.parse(url)

        findings = []
        for entry in feed.entries[:5]:
            findings.append({
                "text": entry.get("title", ""),
                "source_url": entry.get("link"),
                "source_name": "MarketWatch"
            })

        logger.info(f"Fetched {len(findings)} articles from MarketWatch RSS")
        return findings

    def _extract_ticker(self, text: str) -> str | None:
        """Extract known ticker symbol from text."""
        for m in TICKER_RE.findall(text):
            if m in KNOWN_TICKERS:
                return m
        return None

    def _process_finding(self, finding: Dict[str, Any]) -> None:
        """Score and store a finding."""
        try:
            score = score_finding_with_claude(finding["text"], "finance")
            category = self._categorize(finding["text"])
            ticker = self._extract_ticker(finding["text"])

            if ticker and score >= 6:
                category = f"trade_signal:{ticker}"

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
        if "fed" in text_lower or "rate" in text_lower:
            return "fed_action"
        elif "earnings" in text_lower:
            return "earnings"
        elif "market" in text_lower or "stock" in text_lower:
            return "market_movement"
        elif "economic" in text_lower or "gdp" in text_lower:
            return "economic_data"
        return "financial_news"
