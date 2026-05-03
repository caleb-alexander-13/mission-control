# agents/research/tech.py
import logging
import os
from typing import List, Dict, Any
from ..base import BaseAgent
from .data_sources import NewsAPIClient, GitHubClient, HackerNewsClient

logger = logging.getLogger(__name__)

class TechAgent(BaseAgent):
    """R&D agent for technology research (security, tools, trends)."""

    def __init__(self):
        super().__init__("tech")
        newsapi_key = os.getenv('NEWSAPI_KEY', '')
        self.news_client = NewsAPIClient(newsapi_key) if newsapi_key else None
        self.github = GitHubClient()
        self.hackernews = HackerNewsClient()

    def get_findings(self) -> List[Dict[str, Any]]:
        """Fetch latest tech findings."""
        findings = []

        # NewsAPI - tech category
        if self.news_client:
            articles = self.news_client.search_category('technology', hours=24)
            findings.extend(articles)

        # Hacker News
        try:
            hn_stories = self.hackernews.get_top_stories(limit=20)
            findings.extend(hn_stories)
        except Exception as e:
            logger.warning(f"Hacker News error: {e}")

        # GitHub trending
        try:
            trending = self.github.get_trending(language='python')
            findings.extend(trending)
        except Exception as e:
            logger.warning(f"GitHub trending error: {e}")

        return findings

    def score_finding(self, finding: Dict[str, Any]) -> int:
        """Score a finding 1-10 using Claude."""
        from backend.agent_integrations import score_finding_with_claude

        finding_text = f"{finding['title']}: {finding.get('description', '')}"
        score = score_finding_with_claude(
            finding_text=finding_text,
            agent_name='tech'
        )
        return score

    def infer_category(self, finding: Dict[str, Any]) -> str:
        """Infer category from finding."""
        text = (finding.get('title', '') + ' ' + finding.get('description', '')).lower()

        if any(word in text for word in ['security', 'vuln', 'patch', 'breach', 'attack']):
            return 'security_vuln'
        elif any(word in text for word in ['tool', 'framework', 'library', 'release']):
            return 'new_tool'
        elif any(word in text for word in ['ai', 'llm', 'model', 'neural']):
            return 'ai_ml'
        else:
            return 'news'

    def run_once(self) -> None:
        """Run one iteration: fetch findings, score them, store them."""
        logger.info("[tech] Running tech research agent")

        findings = self.get_findings()
        logger.info(f"[tech] Found {len(findings)} items")

        for finding in findings[:5]:
            try:
                score = self.score_finding(finding)
                category = self.infer_category(finding)

                self.insert_research_finding(
                    finding_text=finding.get('title', 'Tech Update'),
                    source_url=finding.get('url', ''),
                    source_name=finding.get('source', 'Unknown'),
                    importance_score=score,
                    category=category
                )
            except Exception as e:
                logger.error(f"[tech] Error processing finding: {e}")
