# agents/research/creative.py
import logging
import os
from typing import List, Dict, Any
from ..base import BaseAgent
from .data_sources import NewsAPIClient, RSSFeedClient

logger = logging.getLogger(__name__)

class CreativeAgent(BaseAgent):
    """R&D agent for creative industry research (design, art, trends)."""

    def __init__(self):
        super().__init__("creative")
        newsapi_key = os.getenv('NEWSAPI_KEY', '')
        self.news_client = NewsAPIClient(newsapi_key) if newsapi_key else None

    def get_findings(self) -> List[Dict[str, Any]]:
        """Fetch latest creative findings."""
        findings = []

        # NewsAPI - entertainment category
        if self.news_client:
            articles = self.news_client.search_category('entertainment', hours=24)
            findings.extend(articles)

        # Design blogs/RSS (simplified)
        try:
            design_articles = RSSFeedClient.fetch_feed(
                'https://www.designernews.co/feed',
                hours=24
            )
            findings.extend(design_articles)
        except Exception as e:
            logger.warning(f"Design news RSS error: {e}")

        return findings

    def score_finding(self, finding: Dict[str, Any]) -> int:
        """Score a finding 1-10 using Claude."""
        from backend.agent_integrations import score_finding_with_claude

        finding_text = f"{finding['title']}: {finding.get('description', '')}"
        score = score_finding_with_claude(
            finding_text=finding_text,
            agent_name='creative'
        )
        return score

    def infer_category(self, finding: Dict[str, Any]) -> str:
        """Infer category from finding."""
        text = (finding.get('title', '') + ' ' + finding.get('description', '')).lower()

        if any(word in text for word in ['design', 'tool', 'software']):
            return 'design_tool'
        elif any(word in text for word in ['trend', 'style', 'aesthetic']):
            return 'trend'
        elif any(word in text for word in ['award', 'winning']):
            return 'recognition'
        else:
            return 'news'

    def run_once(self) -> None:
        """Run one iteration: fetch findings, score them, store them."""
        logger.info("[creative] Running creative research agent")

        findings = self.get_findings()
        logger.info(f"[creative] Found {len(findings)} items")

        for finding in findings[:5]:
            try:
                score = self.score_finding(finding)
                category = self.infer_category(finding)

                self.insert_research_finding(
                    finding_text=finding.get('title', 'Creative Update'),
                    source_url=finding.get('url', ''),
                    source_name=finding.get('source', 'Unknown'),
                    importance_score=score,
                    category=category
                )
            except Exception as e:
                logger.error(f"[creative] Error processing finding: {e}")
