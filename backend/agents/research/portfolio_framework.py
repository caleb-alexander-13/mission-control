"""Portfolio approach framework for impact investing.

Based on JPMorgan's "A Portfolio Approach to Impact Investment" guide.
Evaluates investments across three dimensions: Impact, Return, and Risk.
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'


class PortfolioFramework:
    """Manages portfolio target profile and investment evaluation."""

    # Portfolio target profile (can be customized)
    TARGET_PROFILE = {
        "impact": {
            "min": 4,  # 1-10 scale: responsible/ethical considerations
            "max": 8,
            "weight": 0.2,  # How much does impact matter?
            "description": "ESG alignment, company ethics, responsible business practices"
        },
        "return": {
            "min": 0.08,  # 8% annual return expectation
            "max": 0.25,  # 25% max (risk-adjusted)
            "weight": 0.5,  # Primary focus: financial return
            "description": "Risk-adjusted expected annual return"
        },
        "risk": {
            "min": 2,  # 1-10 scale: low volatility preferred
            "max": 6,  # But willing to take some risk
            "weight": 0.3,
            "description": "Volatility, concentration, downside protection"
        }
    }

    # Stock evaluation rules
    STOCK_IMPACT_SCORES = {
        # High impact (ESG leaders)
        'MSFT': 8,   # Carbon neutral, diversity, renewable energy
        'GOOGL': 8,  # Carbon neutral, privacy focus, diverse workforce
        'JPM': 6,    # Banking for social good programs

        # Medium impact
        'AAPL': 6,   # Supply chain ethics, but high profit concentration
        'WMT': 6,    # Affordable goods, but labor concerns
        'DIS': 5,    # Entertainment, family content
        'CRM': 7,    # Salesforce Eq., 1-1-1 model

        # Lower impact (financial/trading focused)
        'NVDA': 5,   # Tech enablement but no direct social mission
        'AMZN': 4,   # Convenience vs. labor/monopoly concerns
        'TSLA': 7,   # Electric vehicles, sustainability
        'META': 3,   # Privacy concerns, social media risks
        'NFLX': 5,   # Entertainment access
        'AMD': 5,    # Semiconductors, tech enablement
        'INTC': 5,   # Computing infrastructure
        'PYPL': 6,   # Financial inclusion, merchant support
        'UBER': 4,   # Gig economy mixed impact
        'SNAP': 3,   # Social media, youth platform
        'SPOT': 6,   # Artist support, music accessibility
        'GS': 5,     # Investment banking
        'MS': 5,     # Investment banking
    }

    @staticmethod
    def score_stock(ticker: str, expected_return: float, volatility: float) -> Dict[str, Any]:
        """
        Evaluate a stock across Impact, Return, Risk dimensions.

        Args:
            ticker: Stock symbol
            expected_return: Expected annual return (e.g., 0.15 for 15%)
            volatility: Expected volatility/risk (1-10 scale)

        Returns:
            Dictionary with impact, return, risk scores and portfolio fit
        """
        impact = PortfolioFramework.STOCK_IMPACT_SCORES.get(ticker, 5)

        # Normalize return to 1-10 scale (0-50% -> 1-10)
        return_score = min(10, max(1, int(expected_return * 20)))

        # Risk is already 1-10
        risk_score = int(volatility)

        profile = {
            "ticker": ticker,
            "impact": impact,
            "return": return_score,
            "risk": risk_score,
            "fit_assessment": PortfolioFramework._assess_portfolio_fit(impact, return_score, risk_score)
        }

        return profile

    @staticmethod
    def _assess_portfolio_fit(impact: int, return_score: int, risk_score: int) -> Dict[str, Any]:
        """Check if investment aligns with target portfolio profile."""
        target = PortfolioFramework.TARGET_PROFILE

        fit = {
            "impact_fit": target["impact"]["min"] <= impact <= target["impact"]["max"],
            "return_fit": target["return"]["min"] * 10 <= return_score <= target["return"]["max"] * 10,
            "risk_fit": target["risk"]["min"] <= risk_score <= target["risk"]["max"],
            "recommendation": "STRONG" if all([
                target["impact"]["min"] <= impact <= target["impact"]["max"],
                target["return"]["min"] * 10 <= return_score <= target["return"]["max"] * 10,
                target["risk"]["min"] <= risk_score <= target["risk"]["max"]
            ]) else "REVIEW"
        }

        return fit

    @staticmethod
    def get_portfolio_composition() -> Dict[str, Any]:
        """Get current portfolio holdings and composition."""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ticker, shares, avg_cost FROM paper_portfolio WHERE shares > 0
        ''')

        holdings = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Calculate composition
        total_value = sum(h['shares'] * h['avg_cost'] for h in holdings)
        composition = {}

        for holding in holdings:
            pct = (holding['shares'] * holding['avg_cost']) / total_value if total_value > 0 else 0
            composition[holding['ticker']] = {
                "shares": holding['shares'],
                "avg_cost": holding['avg_cost'],
                "pct_of_portfolio": pct * 100,
                "impact_score": PortfolioFramework.STOCK_IMPACT_SCORES.get(holding['ticker'], 5)
            }

        return {
            "holdings": composition,
            "total_value": total_value,
            "num_positions": len(holdings),
            "avg_impact_score": sum(c["impact_score"] for c in composition.values()) / len(holdings) if holdings else 0
        }

    @staticmethod
    def should_diversify(ticker: str, concentration_threshold: float = 0.35) -> bool:
        """Check if adding this position would over-concentrate portfolio."""
        composition = PortfolioFramework.get_portfolio_composition()

        # If ticker already exists and would become > 35% of portfolio, flag for diversification
        if ticker in composition["holdings"]:
            if composition["holdings"][ticker]["pct_of_portfolio"] > concentration_threshold * 100:
                return True

        return False
