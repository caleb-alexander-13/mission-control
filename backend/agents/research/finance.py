"""Finance R&D agent for market and financial insights."""

import logging
import time
import os
import re
import feedparser
import requests
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from agent_integrations import score_finding_with_claude, batch_score_findings_with_claude

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
                if findings:
                    self._process_findings_batch(findings)
            except Exception as e:
                logger.error(f"Error in finance agent: {e}", exc_info=True)

            time.sleep(interval_seconds)

    def _fetch_findings(self) -> List[Dict[str, Any]]:
        """Fetch financial news and data from available sources."""
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

        # Try SEC EDGAR insider trades
        try:
            findings.extend(self._fetch_sec_insider_trades())
        except Exception as e:
            logger.error(f"SEC EDGAR error: {e}")

        # Try stock market data (price moves, technicals)
        try:
            findings.extend(self._fetch_stock_technicals())
        except Exception as e:
            logger.error(f"Stock technicals error: {e}")

        # Try earnings calendar
        try:
            findings.extend(self._fetch_earnings_calendar())
        except Exception as e:
            logger.error(f"Earnings calendar error: {e}")

        # Try economic calendar (FRED)
        try:
            findings.extend(self._fetch_economic_calendar())
        except Exception as e:
            logger.error(f"Economic calendar error: {e}")

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

    def _fetch_sec_insider_trades(self) -> List[Dict[str, Any]]:
        """Fetch recent SEC insider trades (Form 4 filings)."""
        findings = []
        try:
            # Use SEC EDGAR API to get recent insider trades
            # Query for recent Form 4 filings across all tickers
            url = "https://data.sec.gov/submissions/cgi-bin/browse-edgar"
            params = {
                "action": "getcompany",
                "type": "4",
                "dateb": "",
                "owner": "exclude",
                "count": 40,
                "output": "json"
            }

            # Note: SEC API has rate limits, use with care
            response = requests.get(url, params=params, timeout=10, headers={"User-Agent": "FinanceAgent/1.0"})
            response.raise_for_status()
            data = response.json()

            for filing in data.get("filings", {}).get("recent", [])[:5]:
                ticker = filing.get("ticker", "").upper()
                if ticker in KNOWN_TICKERS:
                    finding_text = f"SEC Form 4: {ticker} insider activity - {filing.get('accessionNumber', '')}"
                    findings.append({
                        "text": finding_text,
                        "source_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={filing.get('cik')}&type=4",
                        "source_name": "SEC EDGAR"
                    })

            logger.info(f"Fetched {len(findings)} insider trades from SEC EDGAR")
        except Exception as e:
            logger.warning(f"SEC EDGAR fetch failed: {e}")

        return findings

    def _fetch_stock_technicals(self) -> List[Dict[str, Any]]:
        """Fetch stock price movements and technical signals."""
        findings = []
        try:
            import yfinance as yf

            # Check key technical stocks for significant moves
            for ticker in list(KNOWN_TICKERS)[:5]:  # Sample first 5
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="5d")

                    if len(hist) < 2:
                        continue

                    current_price = hist["Close"].iloc[-1]
                    prev_price = hist["Close"].iloc[-2]
                    pct_change = ((current_price - prev_price) / prev_price) * 100

                    # Flag significant moves (>5%)
                    if abs(pct_change) > 5:
                        direction = "↑" if pct_change > 0 else "↓"
                        finding_text = f"{ticker} technical breakout: {direction} {abs(pct_change):.1f}% move detected"
                        findings.append({
                            "text": finding_text,
                            "source_url": f"https://finance.yahoo.com/quote/{ticker}",
                            "source_name": "YahooFinance"
                        })
                except Exception as e:
                    logger.debug(f"Error fetching {ticker}: {e}")

            logger.info(f"Fetched {len(findings)} technical signals")
        except ImportError:
            logger.warning("yfinance not available for technicals")

        return findings

    def _fetch_earnings_calendar(self) -> List[Dict[str, Any]]:
        """Fetch upcoming earnings announcements for tracked stocks."""
        findings = []
        try:
            # Earnings calendar is typically available via Yahoo Finance
            # For MVP, we'll track key upcoming events manually
            # In production, use: https://api.example.com/earnings or earnings RSS feeds

            upcoming_earnings = {
                "AAPL": "2026-05-10",
                "MSFT": "2026-05-12",
                "NVDA": "2026-05-15",
                "AMZN": "2026-05-16",
                "GOOGL": "2026-05-18"
            }

            from datetime import datetime, timedelta
            today = datetime.now()
            next_week = today + timedelta(days=7)

            for ticker, date_str in upcoming_earnings.items():
                try:
                    earnings_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if today <= earnings_date <= next_week:
                        finding_text = f"{ticker} earnings announcement scheduled for {date_str} - prepare trading thesis"
                        findings.append({
                            "text": finding_text,
                            "source_url": f"https://www.marketwatch.com/tools/earnings-calendar",
                            "source_name": "Earnings Calendar"
                        })
                except Exception as e:
                    logger.debug(f"Error processing earnings for {ticker}: {e}")

            logger.info(f"Fetched {len(findings)} earnings alerts")
        except Exception as e:
            logger.warning(f"Earnings calendar error: {e}")

        return findings

    def _fetch_economic_calendar(self) -> List[Dict[str, Any]]:
        """Fetch economic data and macro indicators from FRED API."""
        findings = []
        try:
            # FRED API endpoints for key economic indicators
            # Free tier available at https://fred.stlouisfed.org/
            fred_api_key = os.getenv("FRED_API_KEY")

            if not fred_api_key:
                logger.debug("FRED_API_KEY not configured, skipping economic calendar")
                return findings

            # Key economic indicators to track
            indicators = {
                "UNRATE": "Unemployment Rate",
                "CPIAUCSL": "Consumer Price Index",
                "FEDFUNDS": "Federal Funds Rate",
                "DEXUSEU": "USD/EUR Exchange Rate",
                "VIXCLS": "Market Volatility Index"
            }

            for series_id, description in indicators.items():
                try:
                    url = f"https://api.stlouisfed.org/fred/series/observations"
                    params = {
                        "series_id": series_id,
                        "api_key": fred_api_key,
                        "limit": 1,
                        "sort_order": "desc"
                    }

                    response = requests.get(url, params=params, timeout=5)
                    response.raise_for_status()
                    data = response.json()

                    if data.get("observations"):
                        obs = data["observations"][0]
                        value = obs.get("value")
                        date = obs.get("date")

                        if value and value != ".":
                            finding_text = f"Economic: {description} at {value} as of {date} - assess impact on markets"
                            findings.append({
                                "text": finding_text,
                                "source_url": f"https://fred.stlouisfed.org/{series_id}",
                                "source_name": "FRED"
                            })
                except Exception as e:
                    logger.debug(f"Error fetching {series_id}: {e}")

            logger.info(f"Fetched {len(findings)} economic indicators")
        except Exception as e:
            logger.warning(f"Economic calendar error: {e}")

        return findings

    def _process_findings_batch(self, findings: List[Dict[str, Any]]) -> None:
        """Score and store multiple findings in batch."""
        if not findings:
            return

        try:
            # Score all findings in a single batch call
            batch_to_score = [{"text": f["text"]} for f in findings]
            scores = batch_score_findings_with_claude(batch_to_score, "finance")

            # Process each finding with its score
            for finding in findings:
                score = scores.get(finding["text"], 5)
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
            logger.error(f"Error processing findings batch: {e}")

    def _process_finding(self, finding: Dict[str, Any]) -> None:
        """Score and store a single finding (fallback for single-finding processing)."""
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
