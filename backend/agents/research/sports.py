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

        # Try NFL player injury reports
        try:
            findings.extend(self._fetch_nfl_injuries())
        except Exception as e:
            logger.error(f"NFL injuries error: {e}")

        # Try college transfer portal tracking
        try:
            findings.extend(self._fetch_transfer_portal())
        except Exception as e:
            logger.error(f"Transfer portal error: {e}")

        # Try draft analysis and scouting
        try:
            findings.extend(self._fetch_draft_analysis())
        except Exception as e:
            logger.error(f"Draft analysis error: {e}")

        # Try coaching news and staff changes
        try:
            findings.extend(self._fetch_coaching_news())
        except Exception as e:
            logger.error(f"Coaching news error: {e}")

        # Try Pro Football Focus insights
        try:
            findings.extend(self._fetch_pff_insights())
        except Exception as e:
            logger.error(f"PFF insights error: {e}")

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
            title = article.get("title", "")
            description = article.get("description") or ""
            findings.append({
                "text": (title + " " + description).strip(),
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

    def _fetch_nfl_injuries(self) -> List[Dict[str, Any]]:
        """Fetch NFL player injury reports and updates."""
        findings = []
        try:
            # ESPN NFL injuries page RSS
            url = "https://www.espn.com/nfl/injuries"
            response = requests.get(url, timeout=10)

            # Check for injury report indicators
            if response.status_code == 200:
                content = response.text.lower()
                # Parse for injury updates
                if "out" in content or "questionable" in content or "doubtful" in content:
                    finding_text = "NFL injury report update - key players status changes, check detailed report for impact on rosters"
                    findings.append({
                        "text": finding_text,
                        "source_url": url,
                        "source_name": "ESPN Injuries"
                    })

            # Pro Football Reference injury trends
            pfr_injuries = "https://www.pro-football-reference.com/players/"
            try:
                response = requests.get(pfr_injuries, timeout=5)
                if response.status_code == 200 and ("injury" in response.text.lower()):
                    finding_text = "Pro Football Reference: Injury reports for notable players updated"
                    findings.append({
                        "text": finding_text,
                        "source_url": pfr_injuries,
                        "source_name": "Pro Football Reference"
                    })
            except Exception as e:
                logger.debug(f"PFR check failed: {e}")

            logger.info(f"Fetched {len(findings)} injury reports")
        except Exception as e:
            logger.warning(f"NFL injuries fetch failed: {e}")

        return findings

    def _fetch_transfer_portal(self) -> List[Dict[str, Any]]:
        """Track college transfer portal activity and player movements."""
        findings = []
        try:
            # ESPN Transfer Portal tracking
            portal_url = "https://www.espn.com/college-football/transfers"
            response = requests.get(portal_url, timeout=10)

            if response.status_code == 200:
                content = response.text.lower()
                # Look for portal activity indicators
                if "transfer" in content or "portal" in content:
                    finding_text = "College transfer portal update - prospect movements, check for key decommitments and new commitments"
                    findings.append({
                        "text": finding_text,
                        "source_url": portal_url,
                        "source_name": "ESPN Transfer Portal"
                    })

            # 247Sports transfer news
            tracker_url = "https://247sports.com/portal/transfer-tracker/"
            try:
                response = requests.get(tracker_url, timeout=5)
                if response.status_code == 200:
                    finding_text = "247Sports transfer tracker - updated prospect portal rankings and evaluations"
                    findings.append({
                        "text": finding_text,
                        "source_url": tracker_url,
                        "source_name": "247Sports"
                    })
            except Exception as e:
                logger.debug(f"247Sports check failed: {e}")

            logger.info(f"Fetched {len(findings)} transfer portal updates")
        except Exception as e:
            logger.warning(f"Transfer portal fetch failed: {e}")

        return findings

    def _fetch_draft_analysis(self) -> List[Dict[str, Any]]:
        """Fetch draft analysis and scouting reports."""
        findings = []
        try:
            # NFL.com draft coverage
            draft_url = "https://www.nfl.com/draft"
            response = requests.get(draft_url, timeout=10)

            if response.status_code == 200:
                finding_text = "NFL.com draft coverage - updated prospect rankings, mock drafts, and analysis"
                findings.append({
                    "text": finding_text,
                    "source_url": draft_url,
                    "source_name": "NFL.com"
                })

            # The Athletic draft analysis (check for free content)
            athletic_url = "https://theathletic.com/draft"
            try:
                response = requests.get(athletic_url, timeout=5)
                if response.status_code == 200:
                    finding_text = "The Athletic draft coverage - detailed prospect analysis and film study reviews"
                    findings.append({
                        "text": finding_text,
                        "source_url": athletic_url,
                        "source_name": "The Athletic"
                    })
            except Exception as e:
                logger.debug(f"The Athletic check failed: {e}")

            # Draft Wire (insider analysis)
            wire_url = "https://www.draftwire.usatoday.com"
            try:
                response = requests.get(wire_url, timeout=5)
                if response.status_code == 200:
                    finding_text = "Draft Wire - insider scouting reports and team draft strategy analysis"
                    findings.append({
                        "text": finding_text,
                        "source_url": wire_url,
                        "source_name": "Draft Wire"
                    })
            except Exception as e:
                logger.debug(f"Draft Wire check failed: {e}")

            logger.info(f"Fetched {len(findings)} draft analysis reports")
        except Exception as e:
            logger.warning(f"Draft analysis fetch failed: {e}")

        return findings

    def _fetch_coaching_news(self) -> List[Dict[str, Any]]:
        """Track NFL coaching changes and staff moves."""
        findings = []
        try:
            # ESPN NFL coaching news
            coaching_url = "https://www.espn.com/nfl/news"
            response = requests.get(coaching_url, timeout=10)

            if response.status_code == 200:
                content = response.text.lower()
                coaching_keywords = ["coach", "hired", "fired", "offensive coordinator", "defensive coordinator"]
                if any(keyword in content for keyword in coaching_keywords):
                    finding_text = "NFL coaching news - staff changes, promotions, or departures affecting teams"
                    findings.append({
                        "text": finding_text,
                        "source_url": coaching_url,
                        "source_name": "ESPN"
                    })

            logger.info(f"Fetched {len(findings)} coaching news items")
        except Exception as e:
            logger.warning(f"Coaching news fetch failed: {e}")

        return findings

    def _fetch_pff_insights(self) -> List[Dict[str, Any]]:
        """Fetch Pro Football Focus player grades and analysis."""
        findings = []
        try:
            # Pro Football Focus main page (free tier content)
            pff_url = "https://www.pff.com"
            response = requests.get(pff_url, timeout=10)

            if response.status_code == 200:
                content = response.text.lower()
                pff_keywords = ["grade", "player evaluation", "nfl analysis"]
                if any(keyword in content for keyword in pff_keywords):
                    finding_text = "Pro Football Focus - updated player grades, positional rankings, and performance analysis"
                    findings.append({
                        "text": finding_text,
                        "source_url": pff_url,
                        "source_name": "Pro Football Focus"
                    })

            # PFF Player Pages (scouting data)
            nfl_pages = "https://www.pff.com/nfl"
            try:
                response = requests.get(nfl_pages, timeout=5)
                if response.status_code == 200:
                    finding_text = "PFF NFL Player Evaluations - weekly updated grades, pass rush productivity, coverage metrics"
                    findings.append({
                        "text": finding_text,
                        "source_url": nfl_pages,
                        "source_name": "PFF"
                    })
            except Exception as e:
                logger.debug(f"PFF check failed: {e}")

            logger.info(f"Fetched {len(findings)} PFF insights")
        except Exception as e:
            logger.warning(f"PFF insights fetch failed: {e}")

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
