# agents/research/finance.py
import logging
import os
from typing import List, Dict, Any
from ..base import BaseAgent
from .data_sources import NewsAPIClient, RSSFeedClient, YahooFinanceClient

logger = logging.getLogger(__name__)

class FinanceAgent(BaseAgent):
    """R&D agent for finance/stock market research."""

    def __init__(self):
        super().__init__("finance")
        newsapi_key = os.getenv('NEWSAPI_KEY', '')
        self.news_client = NewsAPIClient(newsapi_key) if newsapi_key else None
        self.yfinance = YahooFinanceClient()

    def get_findings(self) -> List[Dict[str, Any]]:
        """Fetch latest finance findings."""
        findings = []

        # NewsAPI - business category
        if self.news_client:
            articles = self.news_client.search_category('business', hours=24)
            findings.extend(articles)

        # MarketWatch RSS
        try:
            mw_articles = RSSFeedClient.fetch_feed(
                'https://feeds.marketwatch.com/marketwatch/topstories/',
                hours=24
            )
            findings.extend(mw_articles)
        except Exception as e:
            logger.warning(f"MarketWatch RSS error: {e}")

        # Market summary (placeholder)
        try:
            market = self.yfinance.get_market_summary()
            if market:
                findings.append({
                    'title': 'Market Summary',
                    'description': str(market),
                    'url': '',
                    'source': 'Yahoo Finance',
                    'published_at': ''
                })
        except Exception as e:
            logger.warning(f"Yahoo Finance error: {e}")

        return findings

    def score_finding(self, finding: Dict[str, Any]) -> int:
        """Score a finding 1-10 using Claude."""
        from backend.agent_integrations import score_finding_with_claude

        finding_text = f"{finding['title']}: {finding.get('description', '')}"
        score = score_finding_with_claude(
            finding_text=finding_text,
            agent_name='finance'
        )
        return score

    def infer_category(self, finding: Dict[str, Any]) -> str:
        """Infer category from finding."""
        text = (finding.get('title', '') + ' ' + finding.get('description', '')).lower()

        if any(word in text for word in ['rate', 'fed', 'inflation', 'interest']):
            return 'macro'
        elif any(word in text for word in ['earn', 'revenue', 'profit', 'guidance']):
            return 'earnings'
        elif any(word in text for word in ['crash', 'plunge', 'surge', 'down', 'up', '%']):
            return 'market_movement'
        else:
            return 'news'

    def run_once(self) -> None:
        """Run one iteration: fetch findings, score them, store them."""
        logger.info("[finance] Running finance research agent")

        findings = self.get_findings()
        logger.info(f"[finance] Found {len(findings)} items")

        for finding in findings[:5]:
            try:
                score = self.score_finding(finding)
                category = self.infer_category(finding)

                self.insert_research_finding(
                    finding_text=finding.get('title', 'Market Update'),
                    source_url=finding.get('url', ''),
                    source_name=finding.get('source', 'Unknown'),
                    importance_score=score,
                    category=category
                )
            except Exception as e:
                logger.error(f"[finance] Error processing finding: {e}")
