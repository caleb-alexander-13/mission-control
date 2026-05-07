"""Executioner agent for executing autonomous actions and sending alerts."""

import logging
import time
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

from agents.base_agent import BaseAgent
from agent_integrations import call_gm_seat_api
from utils.notifications import send_notification
from project_integrations import route_finding_to_projects, execute_project_integration

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'


class ExecutionerAgent(BaseAgent):
    """Executes autonomous actions and sends alerts for approval-required actions."""

    def __init__(self, user_phone_number: Optional[str] = None):
        super().__init__("executioner")
        self.user_phone_number = user_phone_number

    def run_loop(self, interval_seconds: int = 300) -> None:
        """Run executioner agent loop every 5 minutes."""
        self.running = True
        logger.info(f"Starting executioner agent loop (interval: {interval_seconds}s)")

        while self.running:
            try:
                self._execute_pending_actions()
            except Exception as e:
                logger.error(f"Error in executioner agent: {e}", exc_info=True)

            time.sleep(interval_seconds)

    def _execute_pending_actions(self) -> None:
        """Get pending examinations and execute or alert."""
        # Clean up excess pending actions (keep top 10, max 20 total)
        self._cleanup_pending_actions()

        examinations = self._get_pending_examinations()

        if not examinations:
            logger.debug("No pending examinations")
            return

        logger.info(f"Processing {len(examinations)} pending examinations")

        for exam in examinations:
            if exam["requires_approval"]:
                self._send_alert(exam)
            else:
                self._execute_autonomous_action(exam)

    def _execute_paper_trade(self, exam: Dict[str, Any]) -> bool:
        """Execute a paper trade for finance trade signals."""
        trade_action_raw = exam.get("trade_action")
        if not trade_action_raw:
            return False

        # Parse trade_action from JSON string
        try:
            if isinstance(trade_action_raw, str):
                import json
                trade_action = json.loads(trade_action_raw)
            else:
                trade_action = trade_action_raw
        except (json.JSONDecodeError, TypeError):
            return False

        ticker = trade_action.get("ticker")
        direction = trade_action.get("direction")
        confidence = trade_action.get("confidence", 5)

        if not ticker or not direction:
            return False

        # Fetch current price
        try:
            from agents.research.data_sources import YahooFinanceClient
        except ImportError:
            from .research.data_sources import YahooFinanceClient

        price = YahooFinanceClient.get_stock_price(ticker)
        if not price:
            logger.warning(f"Could not fetch price for {ticker}")
            return False

        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()

            # Get current cash
            cursor.execute('SELECT balance FROM paper_cash WHERE id=1')
            row = cursor.fetchone()
            cash = row[0] if row else 0

            # Calculate position size: aggressive mode 10-15% per trade
            # 10% base + (confidence/10 * 5%) = 10.5% at confidence 1, 15% at confidence 10
            pct = 0.10 + (confidence / 10) * 0.05
            spend = cash * pct
            shares = round(spend / price, 4)

            if direction == "buy":
                if spend > cash:
                    conn.close()
                    return False

                # Deduct cash
                cursor.execute('UPDATE paper_cash SET balance=balance-?, updated_at=? WHERE id=1',
                               (spend, int(time.time() * 1000)))

                # Upsert portfolio
                cursor.execute('''INSERT OR IGNORE INTO paper_portfolio (ticker, shares, avg_cost, updated_at)
                                  VALUES (?,0,0,?)''', (ticker, int(time.time() * 1000)))

                # Update with weighted average cost
                cursor.execute('''UPDATE paper_portfolio
                                  SET shares=shares+?, avg_cost=((avg_cost*shares+?*?)/(shares+?)), updated_at=?
                                  WHERE ticker=?''',
                               (shares, price, shares, shares, int(time.time() * 1000), ticker))

                cash_delta = -spend
            else:  # sell
                cursor.execute('SELECT shares FROM paper_portfolio WHERE ticker=?', (ticker,))
                pos = cursor.fetchone()
                sell_shares = min(shares, pos[0] if pos else 0)

                if sell_shares <= 0:
                    conn.close()
                    return False

                proceeds = sell_shares * price
                cursor.execute('UPDATE paper_cash SET balance=balance+?, updated_at=? WHERE id=1',
                               (proceeds, int(time.time() * 1000)))
                cursor.execute('UPDATE paper_portfolio SET shares=shares-?, updated_at=? WHERE ticker=?',
                               (sell_shares, int(time.time() * 1000), ticker))
                cash_delta = proceeds

            # Log the trade with reason
            # Use trade_reason if available (more specific), otherwise fall back to gameplan
            trade_reason = exam.get("trade_reason") or exam.get("gameplan", "")
            cursor.execute('''INSERT INTO paper_trades (ticker, action, shares, price, cash_impact, reason, finding_id)
                              VALUES (?,?,?,?,?,?,?)''',
                           (ticker, direction, shares if direction == "buy" else sell_shares, price, cash_delta,
                            trade_reason[:200], exam.get("finding_id")))

            conn.commit()
            conn.close()

            # Send notification
            send_notification(
                f"Finance: {direction.upper()} {shares:.2f} {ticker} @ ${price:.2f}",
                title="Paper Trade Executed",
                tags="chart_with_upwards_trend"
            )

            logger.info(f"Executed paper trade: {direction} {shares} {ticker} @ ${price}")
            return True
        except Exception as e:
            logger.error(f"Paper trade execution failed: {e}", exc_info=True)
            return False

    def _execute_autonomous_action(self, exam: Dict[str, Any]) -> None:
        """Execute an autonomous action (paper trade or War Room update)."""
        try:
            finding = self._get_finding(exam["finding_id"])

            # Try paper trade first if trade_action exists
            if self._execute_paper_trade(exam):
                self._log_action(
                    exam["id"],
                    "autonomous",
                    "Paper Trade",
                    "success",
                    "Trade executed"
                )
                self._update_examination_status(exam["id"], "executed")

                # Route finding to relevant projects
                project_actions = route_finding_to_projects(finding, exam)
                for action in project_actions:
                    execute_project_integration(action)

                return

            # Try project integrations (route to Cavalli, Hilda, War Room, etc.)
            project_actions = route_finding_to_projects(finding, exam)
            if project_actions:
                for action in project_actions:
                    success = execute_project_integration(action)
                    self._log_action(
                        exam["id"],
                        "autonomous",
                        f"Project Integration: {action.get('project')}",
                        "success" if success else "failed",
                        action.get("description")
                    )

            # Otherwise try War Room update (legacy)
            if "war room" in exam["gameplan"].lower() or "update war room" in exam["gameplan"].lower():
                result = call_gm_seat_api({
                    "finding_text": finding["finding_text"],
                    "category": finding["category"],
                    "importance_score": finding["importance_score"],
                    "source_name": finding["source_name"],
                    "gameplan": exam["gameplan"]
                })

                self._log_action(
                    exam["id"],
                    "autonomous",
                    "Update War Room",
                    "success" if result.get("status") != "error" else "failed",
                    str(result)
                )

                logger.info(f"Executed autonomous action for examination {exam['id']}")

            # Update examination status
            self._update_examination_status(exam["id"], "executed")

        except Exception as e:
            logger.error(f"Error executing action: {e}", exc_info=True)
            self._log_action(
                exam["id"],
                "autonomous",
                "Autonomous Action",
                "failed",
                str(e)
            )

    def _send_alert(self, exam: Dict[str, Any]) -> None:
        """Send push alert (ntfy) for approval-required action."""
        try:
            import os
            finding = self._get_finding(exam["finding_id"])

            # Build alert message
            gameplan = exam['gameplan']
            finding_text = finding['finding_text'][:100]

            # Create action URLs using configurable base URL (for phone access)
            base_url = os.getenv("MISSION_CONTROL_URL", "http://localhost:8000")
            approve_url = f"{base_url}/api/agent-pipeline/examinations/{exam['id']}/approve"
            deny_url = f"{base_url}/api/agent-pipeline/examinations/{exam['id']}/deny"

            msg = f"{gameplan}\n\n{finding_text}"

            # Send notification via ntfy with approve button
            success = send_notification(
                msg,
                title=f"[{finding['source_name'].upper()}] Action Required ({exam['priority'].upper()})",
                tags="rotating_light",
                action_url=approve_url,
                action_label="APPROVE"
            )

            if success:
                self._log_action(
                    exam["id"],
                    "alert_user",
                    "Send Notification",
                    "pending",
                    f"Alert sent via ntfy"
                )
                logger.info(f"Sent alert for examination {exam['id']}")
            else:
                logger.error(f"Failed to send alert for examination {exam['id']}")
                self._log_action(
                    exam["id"],
                    "alert_user",
                    "Send Notification",
                    "failed",
                    "Notification failed to send"
                )
        except Exception as e:
            logger.error(f"Error sending alert: {e}", exc_info=True)
            self._log_action(
                exam["id"],
                "alert_user",
                "Send Notification",
                "failed",
                str(e)
            )

    def _cleanup_pending_actions(self) -> None:
        """Clean up excess pending actions - keep top 10, never exceed 20 total."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()

            # Get total count of pending actions
            cursor.execute('SELECT COUNT(*) FROM examinations WHERE status = "pending_action"')
            total_pending = cursor.fetchone()[0]

            if total_pending <= 20:
                conn.close()
                return  # Within limit, no cleanup needed

            logger.warning(f"Cleaning up pending actions: {total_pending} > 20 limit")

            # Get the top 10 by priority (these will be kept)
            cursor.execute('''
                SELECT id FROM examinations
                WHERE status = 'pending_action'
                ORDER BY priority DESC, created_at ASC
                LIMIT 10
            ''')
            top_10_ids = [row[0] for row in cursor.fetchall()]

            # Delete all pending actions NOT in top 10
            placeholders = ','.join('?' * len(top_10_ids))
            cursor.execute(f'''
                DELETE FROM examinations
                WHERE status = 'pending_action' AND id NOT IN ({placeholders})
            ''', top_10_ids)

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"Cleaned up {deleted} low-priority pending actions, keeping top 10")

        except Exception as e:
            logger.error(f"Error cleaning up pending actions: {e}", exc_info=True)

    def _get_pending_examinations(self) -> List[Dict[str, Any]]:
        """Get all pending examinations."""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, finding_id, claude_analysis, gameplan, priority,
                   requires_approval, status, trade_action, created_at
            FROM examinations
            WHERE status = 'pending_action'
            ORDER BY priority DESC, created_at ASC
            LIMIT 10
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _get_finding(self, finding_id: int) -> Dict[str, Any]:
        """Get finding details."""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, agent_name, finding_text, source_url, source_name,
                   importance_score, category
            FROM research_findings
            WHERE id = ?
        ''', (finding_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else {}

    def _log_action(
        self,
        examination_id: int,
        action_type: str,
        action_description: str,
        result: str,
        result_detail: str
    ) -> None:
        """Log an action to the database."""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        now = int(time.time() * 1000)
        executed_at = now if result in ["success", "pending"] else None

        cursor.execute('''
            INSERT INTO actions
            (examination_id, action_type, action_description, result, result_detail, created_at, executed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            examination_id,
            action_type,
            action_description,
            result,
            result_detail,
            now,
            executed_at
        ))

        conn.commit()
        conn.close()

    def _update_examination_status(self, exam_id: int, status: str) -> None:
        """Update examination status."""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        now = int(time.time() * 1000)

        cursor.execute(
            'UPDATE examinations SET status = ?, updated_at = ? WHERE id = ?',
            (status, now, exam_id)
        )

        conn.commit()
        conn.close()
