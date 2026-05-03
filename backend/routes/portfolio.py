from fastapi import APIRouter
import sqlite3
import time
from pathlib import Path

router = APIRouter()
DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'


@router.get("/portfolio")
def get_portfolio():
    """Get paper trading portfolio with current valuations."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Get current cash balance
        cur.execute('SELECT balance FROM paper_cash WHERE id=1')
        row = cur.fetchone()
        cash = row['balance'] if row else 5000.0

        # Get all holdings with positive shares
        cur.execute('SELECT * FROM paper_portfolio WHERE shares > 0 ORDER BY ticker')
        holdings = [dict(r) for r in cur.fetchall()]

        # Refresh prices and compute market value
        total_market_value = cash
        for h in holdings:
            try:
                from agents.research.data_sources import YahooFinanceClient
                price = YahooFinanceClient.get_stock_price(h['ticker']) or h['avg_cost']
                h['current_price'] = round(float(price), 2)
                h['market_value'] = round(float(price) * h['shares'], 2)
                h['unrealized_pnl'] = round((float(price) - h['avg_cost']) * h['shares'], 2)
                total_market_value += h['market_value']
            except Exception:
                h['current_price'] = h['avg_cost']
                h['market_value'] = h['avg_cost'] * h['shares']
                h['unrealized_pnl'] = 0

        # Get recent trades (last 20)
        cur.execute('SELECT * FROM paper_trades ORDER BY created_at DESC LIMIT 20')
        trades = [dict(r) for r in cur.fetchall()]

        conn.close()

        return {
            "cash": round(cash, 2),
            "total_value": round(total_market_value, 2),
            "pnl": round(total_market_value - 5000.0, 2),
            "pnl_pct": round(((total_market_value - 5000.0) / 5000.0) * 100, 2),
            "holdings": holdings,
            "recent_trades": trades,
        }
    except Exception as e:
        return {
            "error": str(e),
            "cash": 5000.0,
            "total_value": 5000.0,
            "pnl": 0.0,
            "pnl_pct": 0.0,
            "holdings": [],
            "recent_trades": [],
        }
