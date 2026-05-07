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
                # Deduplicate findings within batch
                seen_texts = set()
                for finding in findings:
                    text_lower = finding["text"].lower().strip()
                    if text_lower not in seen_texts:
                        seen_texts.add(text_lower)
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

        # Try AI model release tracking
        try:
            findings.extend(self._fetch_ai_releases())
        except Exception as e:
            logger.error(f"AI releases error: {e}")

        # Try GitHub trending repositories
        try:
            findings.extend(self._fetch_github_trending())
        except Exception as e:
            logger.error(f"GitHub trending error: {e}")

        # Try Product Hunt newest products
        try:
            findings.extend(self._fetch_product_hunt())
        except Exception as e:
            logger.error(f"Product Hunt error: {e}")

        # Try security advisories and CVEs
        try:
            findings.extend(self._fetch_security_advisories())
        except Exception as e:
            logger.error(f"Security advisories error: {e}")

        return findings

    def _fetch_newsapi_tech(self) -> List[Dict[str, Any]]:
        """Fetch tech news from NewsAPI (past 3 days only)."""
        from datetime import datetime, timedelta
        three_days_ago = (datetime.utcnow() - timedelta(days=3)).isoformat()

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "technology AI startup software cloud",
            "language": "en",
            "from": three_days_ago,
            "sortBy": "publishedAt",
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

    def _fetch_ai_releases(self) -> List[Dict[str, Any]]:
        """Monitor AI model releases from major labs."""
        findings = []
        try:
            # Monitor Anthropic's website for Claude releases
            url = "https://www.anthropic.com"
            response = requests.get(url, timeout=5)
            if "claude" in response.text.lower():
                finding_text = "Anthropic Claude updates or new model releases - check official announcements"
                findings.append({
                    "text": finding_text,
                    "source_url": "https://www.anthropic.com",
                    "source_name": "Anthropic"
                })

            # Monitor OpenAI announcements via their blog RSS
            openai_rss = "https://openai.com/blog/rss.xml"
            try:
                feed = feedparser.parse(openai_rss)
                for entry in feed.entries[:3]:
                    if any(word in entry.get("title", "").lower() for word in ["gpt", "model", "release"]):
                        findings.append({
                            "text": entry.get("title", "OpenAI announcement"),
                            "source_url": entry.get("link", "https://openai.com/blog"),
                            "source_name": "OpenAI Blog"
                        })
            except Exception as e:
                logger.debug(f"OpenAI RSS error: {e}")

            logger.info(f"Fetched {len(findings)} AI release updates")
        except Exception as e:
            logger.warning(f"AI releases fetch failed: {e}")

        return findings

    def _fetch_github_trending(self) -> List[Dict[str, Any]]:
        """Fetch trending GitHub repositories."""
        findings = []
        try:
            # GitHub trending endpoint (unofficial but reliable)
            url = "https://api.github.com/search/repositories"
            today = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400))  # Last 24 hours

            params = {
                "q": f"created:>{today} stars:>100",
                "sort": "stars",
                "order": "desc",
                "per_page": 5
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for repo in data.get("items", []):
                if repo.get("language"):  # Only repos with detected language
                    finding_text = f"GitHub trending: {repo['name']} ({repo['language']}) - {repo['description'][:100] if repo.get('description') else 'Rising project'}"
                    findings.append({
                        "text": finding_text,
                        "source_url": repo.get("html_url"),
                        "source_name": "GitHub Trending"
                    })

            logger.info(f"Fetched {len(findings)} trending GitHub repos")
        except Exception as e:
            logger.warning(f"GitHub trending fetch failed: {e}")

        return findings

    def _fetch_product_hunt(self) -> List[Dict[str, Any]]:
        """Fetch newest products from Product Hunt."""
        findings = []
        try:
            # Product Hunt API endpoint (free tier)
            url = "https://api.producthunt.com/v2/posts"

            # Note: Requires Product Hunt API token for authentication
            # For now, use RSS feed alternative
            ph_rss = "https://www.producthunt.com/feed.xml"
            feed = feedparser.parse(ph_rss)

            for entry in feed.entries[:5]:
                finding_text = f"Product Hunt launch: {entry.get('title', 'New product')} - {entry.get('summary', '')[:100]}"
                findings.append({
                    "text": finding_text,
                    "source_url": entry.get("link", "https://www.producthunt.com"),
                    "source_name": "Product Hunt"
                })

            logger.info(f"Fetched {len(findings)} new products from Product Hunt")
        except Exception as e:
            logger.warning(f"Product Hunt fetch failed: {e}")

        return findings

    def _fetch_security_advisories(self) -> List[Dict[str, Any]]:
        """Fetch security advisories and critical CVEs."""
        findings = []
        try:
            # National Vulnerability Database RSS feed
            url = "https://services.nvd.nist.gov/rest/xml/cves/1.0"

            # Alternative: Use CVE RSS feed
            cve_rss = "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-modified.json"

            # For now, use a simpler approach - monitor security.txt and advisories
            # Check CISA alerts
            cisa_url = "https://www.cisa.gov/news-events/news"

            response = requests.get(cisa_url, timeout=10)
            if response.status_code == 200 and ("alert" in response.text.lower() or "critical" in response.text.lower()):
                finding_text = "CISA security alert or advisory - check for critical vulnerabilities affecting your infrastructure"
                findings.append({
                    "text": finding_text,
                    "source_url": "https://www.cisa.gov/news-events/news",
                    "source_name": "CISA Alerts"
                })

            # Python/Node.js security releases
            npm_security = "https://registry.npmjs.org/-/npm/v1/security/advisories"
            try:
                resp = requests.get(npm_security, timeout=5)
                if resp.status_code == 200:
                    advisories = resp.json()
                    if advisories:
                        finding_text = f"npm security advisory - {len(advisories)} recent vulnerabilities detected in JavaScript ecosystem"
                        findings.append({
                            "text": finding_text,
                            "source_url": "https://www.npmjs.com/advisories",
                            "source_name": "npm Security"
                        })
            except Exception as e:
                logger.debug(f"npm security check failed: {e}")

            logger.info(f"Fetched {len(findings)} security advisories")
        except Exception as e:
            logger.warning(f"Security advisories fetch failed: {e}")

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
