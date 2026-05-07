"""Data sources for research agents - stock prices, news, economic data, etc."""

import logging

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Fetch real stock prices via yfinance."""

    @staticmethod
    def get_stock_price(ticker: str) -> float | None:
        """Get current stock price for a ticker."""
        try:
            import yfinance as yf
            hist = yf.Ticker(ticker).history(period="1d")
            if hist.empty:
                return None
            return float(hist["Close"].iloc[-1])
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e}")
            return None
