from fastapi import APIRouter
import sqlite3
import time
import json
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

        # Get recent trades with linked findings (last 20)
        cur.execute('''
            SELECT pt.id, pt.ticker, pt.action, pt.shares, pt.price, pt.cash_impact,
                   pt.reason, pt.created_at, pt.finding_id,
                   rf.finding_text, rf.source_name, rf.importance_score
            FROM paper_trades pt
            LEFT JOIN research_findings rf ON pt.finding_id = rf.id
            ORDER BY pt.created_at DESC LIMIT 20
        ''')
        trades = [dict(r) for r in cur.fetchall()]

        # Resolve confidence for each trade from linked examination
        for trade in trades:
            confidence = None
            if trade.get('finding_id'):
                cur.execute('''
                    SELECT trade_action FROM examinations
                    WHERE finding_id = ? AND trade_action IS NOT NULL LIMIT 1
                ''', (trade['finding_id'],))
                exam_row = cur.fetchone()
                if exam_row and exam_row[0]:
                    try:
                        ta = json.loads(exam_row[0])
                        confidence = ta.get('confidence')
                    except Exception:
                        pass
            trade['confidence'] = confidence

        # Performance stats
        cur.execute('''
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN cash_impact > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN cash_impact < 0 THEN 1 ELSE 0 END) as losses,
                MAX(cash_impact) as best_trade,
                MIN(cash_impact) as worst_trade,
                AVG(ABS(cash_impact)) as avg_size
            FROM paper_trades
        ''')
        stats = cur.fetchone()
        total_trades = stats['total_trades'] or 0
        wins = stats['wins'] or 0
        win_rate = round((wins / max(total_trades, 1)) * 100, 1) if total_trades > 0 else 0
        performance = {
            "total_trades": total_trades,
            "wins": wins,
            "losses": stats['losses'] or 0,
            "win_rate": win_rate,
            "best_trade": round(stats['best_trade'] or 0, 2),
            "worst_trade": round(stats['worst_trade'] or 0, 2),
            "avg_size": round(stats['avg_size'] or 0, 2),
        }

        conn.close()

        return {
            "cash": round(cash, 2),
            "total_value": round(total_market_value, 2),
            "pnl": round(total_market_value - 5000.0, 2),
            "pnl_pct": round(((total_market_value - 5000.0) / 5000.0) * 100, 2),
            "holdings": holdings,
            "recent_trades": trades,
            "performance": performance,
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
