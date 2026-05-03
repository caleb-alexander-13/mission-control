# agents/research/sports.py
import os
import logging
from typing import List, Dict, Any
from ..base import BaseAgent
from .data_sources import NewsAPIClient, RSSFeedClient

logger = logging.getLogger(__name__)

class SportsAgent(BaseAgent):
    """R&D agent for sports research (NFL focus)."""

    def __init__(self):
        super().__init__("sports")
        self.news_api_key = os.getenv('NEWSAPI_KEY', '')
        self.news_client = NewsAPIClient(self.news_api_key) if self.news_api_key else None

    def get_findings(self) -> List[Dict[str, Any]]:
        """Fetch latest sports findings from data sources."""
        findings = []

        # NewsAPI - sports category
        if self.news_client:
            articles = self.news_client.search_category('sports', hours=24)
            findings.extend([
                {
                    'title': a['title'],
                    'description': a['description'],
                    'url': a['url'],
                    'source': a['source'],
                    'published': a['published_at']
                }
                for a in articles
            ])

        # ESPN RSS feed
        try:
            espn_articles = RSSFeedClient.fetch_feed(
                'http://feeds.espn.go.com/espn/rss/nfl/news',
                hours=24
            )
            findings.extend(espn_articles)
        except Exception as e:
            logger.warning(f"ESPN RSS error: {e}")

        # Reddit r/nfl (simplified - would need PRAW in production)
        # For MVP, skip Reddit scraping

        return findings

    def score_finding(self, finding: Dict[str, Any]) -> int:
        """Score a finding 1-10 using Claude."""
        from backend.agent_integrations import score_finding_with_claude

        finding_text = f"{finding['title']}: {finding.get('description', '')}"
        score = score_finding_with_claude(
            finding_text=finding_text,
            agent_name='sports'
        )
        return score

    def infer_category(self, finding: Dict[str, Any]) -> str:
        """Infer category from finding."""
        text = (finding.get('title', '') + ' ' + finding.get('description', '')).lower()

        if any(word in text for word in ['injur', 'hurt', 'out', 'week-to-week']):
            return 'injury'
        elif any(word in text for word in ['trade', 'sign', 'draft']):
            return 'roster'
        elif any(word in text for word in ['rule', 'change', 'playoff']):
            return 'rules'
        else:
            return 'news'

    def run_once(self) -> None:
        """Run one iteration: fetch findings, score them, store them."""
        logger.info("[sports] Running sports research agent")

        findings = self.get_findings()
        logger.info(f"[sports] Found {len(findings)} articles")

        for finding in findings[:5]:  # Limit to 5 per run for cost
            try:
                score = self.score_finding(finding)
                category = self.infer_category(finding)

                self.insert_research_finding(
                    finding_text=finding['title'],
                    source_url=finding.get('url', ''),
                    source_name=finding.get('source', 'Unknown'),
                    importance_score=score,
                    category=category
                )
            except Exception as e:
                logger.error(f"[sports] Error processing finding: {e}")
