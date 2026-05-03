"""Executioner agent for executing autonomous actions and sending alerts."""

import logging
import time
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

from agents.base_agent import BaseAgent
from agent_integrations import send_sms_alert, call_gm_seat_api

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

    def _execute_autonomous_action(self, exam: Dict[str, Any]) -> None:
        """Execute an autonomous action (update War Room)."""
        try:
            # For MVP, only autonomous action is updating War Room
            finding = self._get_finding(exam["finding_id"])

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
            else:
                logger.debug(f"Gameplan doesn't trigger autonomous action: {exam['gameplan']}")
        except Exception as e:
            logger.error(f"Error executing action: {e}", exc_info=True)
            self._log_action(
                exam["id"],
                "autonomous",
                "Update War Room",
                "failed",
                str(e)
            )

    def _send_alert(self, exam: Dict[str, Any]) -> None:
        """Send SMS alert for approval-required action."""
        try:
            if not self.user_phone_number:
                logger.warning("User phone number not configured, cannot send alert")
                self._log_action(
                    exam["id"],
                    "alert_user",
                    "Send SMS",
                    "failed",
                    "No user phone configured"
                )
                return

            finding = self._get_finding(exam["finding_id"])

            success = send_sms_alert(
                self.user_phone_number,
                finding["finding_text"],
                exam["gameplan"],
                exam["priority"]
            )

            if success:
                self._log_action(
                    exam["id"],
                    "alert_user",
                    "Send SMS",
                    "pending",
                    f"SMS sent to {self.user_phone_number}"
                )
                logger.info(f"Sent alert for examination {exam['id']}")
            else:
                logger.error(f"Failed to send alert for examination {exam['id']}")
                self._log_action(
                    exam["id"],
                    "alert_user",
                    "Send SMS",
                    "failed",
                    "SMS failed to send"
                )
        except Exception as e:
            logger.error(f"Error sending alert: {e}", exc_info=True)
            self._log_action(
                exam["id"],
                "alert_user",
                "Send SMS",
                "failed",
                str(e)
            )

    def _get_pending_examinations(self) -> List[Dict[str, Any]]:
        """Get all pending examinations."""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, finding_id, claude_analysis, gameplan, priority,
                   requires_approval, status, created_at
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
