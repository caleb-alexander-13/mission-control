# agents/research/data_sources.py
import feedparser
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsAPIClient:
    """Wrapper for NewsAPI (requires API key)."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"

    def search_category(self, category: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Search news by category. Returns last N hours of articles."""
        try:
            url = f"{self.base_url}/top-headlines?category={category}&apiKey={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            articles = response.json().get('articles', [])
            return [
                {
                    'title': a['title'],
                    'description': a['description'],
                    'url': a['url'],
                    'source': a['source']['name'],
                    'published_at': a['publishedAt']
                }
                for a in articles
            ]
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []

class RSSFeedClient:
    """Wrapper for RSS feeds."""

    @staticmethod
    def fetch_feed(feed_url: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Fetch RSS feed articles from last N hours."""
        try:
            feed = feedparser.parse(feed_url)
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            entries = []
            for entry in feed.entries[:20]:  # Limit to 20 most recent
                try:
                    published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.utcnow()
                    if published > cutoff_time:
                        entries.append({
                            'title': entry.get('title', ''),
                            'summary': entry.get('summary', ''),
                            'url': entry.get('link', ''),
                            'source': feed.feed.get('title', 'RSS'),
                            'published_at': published.isoformat()
                        })
                except Exception as e:
                    logger.debug(f"Error parsing RSS entry: {e}")

            return entries
        except Exception as e:
            logger.error(f"RSS feed error: {e}")
            return []

class GitHubClient:
    """Wrapper for GitHub API (trending repos)."""

    @staticmethod
    def get_trending(language: str = '', since: str = 'daily') -> List[Dict[str, Any]]:
        """Get trending GitHub repos. since='daily'|'weekly'|'monthly'."""
        try:
            # GitHub doesn't have a dedicated trending API, use search
            # This is a simplified version
            url = f"https://api.github.com/search/repositories?q=stars:>{100}&sort=stars&order=desc"

            if language:
                url += f"&language={language}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            repos = response.json().get('items', [])
            return [
                {
                    'name': r['full_name'],
                    'description': r['description'],
                    'url': r['html_url'],
                    'stars': r['stargazers_count'],
                    'language': r['language']
                }
                for r in repos[:10]
            ]
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return []

class HackerNewsClient:
    """Wrapper for Hacker News API."""

    @staticmethod
    def get_top_stories(limit: int = 30) -> List[Dict[str, Any]]:
        """Get top stories from Hacker News."""
        try:
            # Get top story IDs
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            story_ids = response.json()[:limit]
            stories = []

            for story_id in story_ids:
                try:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    story_response = requests.get(story_url, timeout=5)
                    story_response.raise_for_status()

                    story = story_response.json()
                    stories.append({
                        'title': story.get('title', ''),
                        'url': story.get('url', ''),
                        'score': story.get('score', 0),
                        'comments': story.get('descendants', 0),
                        'source': 'Hacker News'
                    })
                except Exception as e:
                    logger.debug(f"Error fetching HN story: {e}")

            return stories
        except Exception as e:
            logger.error(f"Hacker News API error: {e}")
            return []

class YahooFinanceClient:
    """Wrapper for Yahoo Finance (simplified, no API key needed)."""

    @staticmethod
    def get_market_summary() -> Dict[str, Any]:
        """Get market summary (indices)."""
        try:
            # Simplified version - in production use yfinance library
            # For now, return placeholder
            return {
                'indices': {
                    'S&P 500': {'change': 0, 'change_pct': 0},
                    'Nasdaq': {'change': 0, 'change_pct': 0},
                    'Dow': {'change': 0, 'change_pct': 0}
                }
            }
        except Exception as e:
            logger.error(f"Yahoo Finance error: {e}")
            return {}

    @staticmethod
    def get_stock_price(ticker: str) -> float | None:
        """Fetch current stock price for a ticker."""
        try:
            import yfinance as yf
            hist = yf.Ticker(ticker).history(period="1d")
            if hist.empty:
                return None
            return float(hist["Close"].iloc[-1])
        except Exception as e:
            logger.error(f"Stock price fetch for {ticker} failed: {e}")
            return None
