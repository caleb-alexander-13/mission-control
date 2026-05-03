from fastapi import APIRouter
import sqlite3
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()

ALERT_BUDGET = 100.0
ALERT_THRESHOLDS = [10, 25, 50, 75]


def _send_notification(message: str, title: str = "Mission Control") -> bool:
    from utils.notifications import send_notification
    return send_notification(message, title, tags="money")

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

# Pricing per MTok
PRICING = {
    'claude-sonnet-4-6': {
        'input': 3.0,
        'output': 15.0,
        'cache_read': 0.30,
        'cache_creation': 3.75
    },
    'claude-haiku-4-5-20251001': {
        'input': 0.80,
        'output': 4.0,
        'cache_read': 0.08,
        'cache_creation': 1.00
    },
    'default': {
        'input': 1.0,
        'output': 5.0,
        'cache_read': 0.10,
        'cache_creation': 1.25
    }
}

def calculate_cost(tokens, token_type, model):
    """Calculate USD cost from token counts."""
    model_pricing = PRICING.get(model, PRICING['default'])
    price_per_mtok = model_pricing.get(token_type, 1.0)
    return (tokens / 1_000_000) * price_per_mtok

@router.get("/cost/summary")
def cost_summary():
    """Get cost summary: today, this week, all-time, and per-session breakdown."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        now = datetime.now()
        today_start = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        week_start = int((now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)

        def calc_period(start_time):
            """Calculate cost for a time period."""
            cursor.execute('''
                SELECT SUM(input_tokens) as input, SUM(output_tokens) as output,
                       SUM(cache_read_tokens) as cache_read, SUM(cache_creation_tokens) as cache_creation
                FROM token_usage WHERE created_at >= ?
            ''', (start_time,))
            row = cursor.fetchone()
            if not row or not row['input']:
                return {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_creation_tokens": 0, "estimated_usd": 0}

            input_tokens = row['input'] or 0
            output_tokens = row['output'] or 0
            cache_read = row['cache_read'] or 0
            cache_creation = row['cache_creation'] or 0

            # Use default pricing for now (MVP)
            usd = (input_tokens * 3 / 1_000_000) + (output_tokens * 15 / 1_000_000) + \
                  (cache_read * 0.30 / 1_000_000) + (cache_creation * 3.75 / 1_000_000)

            return {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "cache_read_tokens": int(cache_read),
                "cache_creation_tokens": int(cache_creation),
                "estimated_usd": round(usd, 4)
            }

        today = calc_period(today_start)
        week = calc_period(week_start)

        # All-time
        cursor.execute('''
            SELECT SUM(input_tokens) as input, SUM(output_tokens) as output,
                   SUM(cache_read_tokens) as cache_read, SUM(cache_creation_tokens) as cache_creation
            FROM token_usage
        ''')
        row = cursor.fetchone()
        if row and row['input']:
            input_tokens = row['input'] or 0
            output_tokens = row['output'] or 0
            cache_read = row['cache_read'] or 0
            cache_creation = row['cache_creation'] or 0
            usd = (input_tokens * 3 / 1_000_000) + (output_tokens * 15 / 1_000_000) + \
                  (cache_read * 0.30 / 1_000_000) + (cache_creation * 3.75 / 1_000_000)
            all_time = {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "cache_read_tokens": int(cache_read),
                "cache_creation_tokens": int(cache_creation),
                "estimated_usd": round(usd, 4)
            }
        else:
            all_time = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_creation_tokens": 0, "estimated_usd": 0}

        # Per-session
        cursor.execute('''
            SELECT s.session_id, s.project, s.started_at,
                   SUM(t.input_tokens) as input, SUM(t.output_tokens) as output,
                   SUM(t.cache_read_tokens) as cache_read, SUM(t.cache_creation_tokens) as cache_creation
            FROM sessions s
            LEFT JOIN token_usage t ON s.session_id = t.session_id
            GROUP BY s.session_id
            ORDER BY s.started_at DESC
            LIMIT 20
        ''')

        by_session = []
        for row in cursor.fetchall():
            input_tokens = row['input'] or 0
            output_tokens = row['output'] or 0
            cache_read = row['cache_read'] or 0
            cache_creation = row['cache_creation'] or 0
            usd = (input_tokens * 3 / 1_000_000) + (output_tokens * 15 / 1_000_000) + \
                  (cache_read * 0.30 / 1_000_000) + (cache_creation * 3.75 / 1_000_000)

            by_session.append({
                "session_id": row['session_id'],
                "project": row['project'],
                "started_at": row['started_at'],
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "estimated_usd": round(usd, 4)
            })

        conn.close()

        return {
            "today": today,
            "this_week": week,
            "all_time": all_time,
            "by_session": by_session
        }

    except Exception as e:
        return {
            "error": str(e),
            "today": {"estimated_usd": 0},
            "this_week": {"estimated_usd": 0},
            "all_time": {"estimated_usd": 0}
        }


@router.post("/cost/test-sms")
def cost_test_sms():
    """Send a test SMS to verify Twilio credentials."""
    ok = _send_notification("Mission Control: test notification — alerts are working ✓")
    return {"sent": ok}


@router.get("/cost/alert-check")
def cost_alert_check():
    """Check today's cost against thresholds, send SMS for newly crossed ones."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)

    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Ensure table exists (idempotent)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cost_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                threshold_pct INTEGER NOT NULL,
                budget REAL NOT NULL,
                cost_at_trigger REAL NOT NULL,
                alert_date TEXT NOT NULL,
                sent_via TEXT,
                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
            )
        ''')

        # Today's cost
        cursor.execute('''
            SELECT SUM(input_tokens) as input, SUM(output_tokens) as output,
                   SUM(cache_read_tokens) as cache_read, SUM(cache_creation_tokens) as cache_creation
            FROM token_usage WHERE created_at >= ?
        ''', (today_start,))
        row = cursor.fetchone()
        input_tokens = row['input'] or 0 if row else 0
        output_tokens = row['output'] or 0 if row else 0
        cache_read = row['cache_read'] or 0 if row else 0
        cache_creation = row['cache_creation'] or 0 if row else 0
        today_cost = (input_tokens * 3 / 1_000_000) + (output_tokens * 15 / 1_000_000) + \
                     (cache_read * 0.30 / 1_000_000) + (cache_creation * 3.75 / 1_000_000)

        # Which thresholds already alerted today?
        cursor.execute('SELECT threshold_pct FROM cost_alerts WHERE alert_date = ?', (today_str,))
        already_alerted = {row['threshold_pct'] for row in cursor.fetchall()}

        # Check for recent alerts (within last hour) to prevent duplicate edge-case sends
        one_hour_ago = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
        cursor.execute(
            'SELECT threshold_pct FROM cost_alerts WHERE alert_date = ? AND created_at > ?',
            (today_str, one_hour_ago)
        )
        recently_alerted = {row['threshold_pct'] for row in cursor.fetchall()}

        newly_triggered = []
        for pct in ALERT_THRESHOLDS:
            threshold_amount = ALERT_BUDGET * pct / 100
            # Send alert if threshold crossed, not already alerted today, and not sent in the last hour
            if today_cost >= threshold_amount and pct not in already_alerted and pct not in recently_alerted:
                msg = f"Mission Control: {pct}% budget alert — ${today_cost:.2f} spent today (limit ${ALERT_BUDGET:.0f})"
                sms_ok = _send_notification(msg, title=f"Budget {pct}% Reached")
                cursor.execute(
                    'INSERT INTO cost_alerts (threshold_pct, budget, cost_at_trigger, alert_date, sent_via) VALUES (?,?,?,?,?)',
                    (pct, ALERT_BUDGET, round(today_cost, 4), today_str, 'ntfy' if sms_ok else 'visual_only')
                )
                newly_triggered.append(pct)

        conn.commit()

        cursor.execute('SELECT threshold_pct FROM cost_alerts WHERE alert_date = ?', (today_str,))
        alerted_today = sorted([row['threshold_pct'] for row in cursor.fetchall()])

        conn.close()

        return {
            "today_cost": round(today_cost, 4),
            "budget": ALERT_BUDGET,
            "newly_triggered": newly_triggered,
            "alerted_today": alerted_today,
        }

    except Exception as e:
        logger.error(f"alert-check error: {e}")
        return {"today_cost": 0, "budget": ALERT_BUDGET, "newly_triggered": [], "alerted_today": [], "error": str(e)}
