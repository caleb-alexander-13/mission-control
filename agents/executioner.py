# agents/executioner.py
import sqlite3
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

class ExecutionerAgent(BaseAgent):
    """Agent that executes pending examinations (autonomous actions or SMS alerts)."""

    def __init__(self, user_phone_number: str = None):
        super().__init__("executioner")
        self.db_path = DB_PATH
        self.user_phone_number = user_phone_number or ""

    def get_pending_examinations(self) -> List[Dict[str, Any]]:
        """Get all examinations pending action."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT e.id, e.finding_id, e.claude_analysis, e.gameplan, e.priority,
                       e.requires_approval, rf.finding_text, rf.category, rf.importance_score,
                       rf.source_name, rf.source_url
                FROM examinations e
                JOIN research_findings rf ON e.finding_id = rf.id
                WHERE e.status = 'pending_action'
                ORDER BY e.created_at ASC
            ''')

            examinations = [dict(row) for row in cursor.fetchall()]
            return examinations
        finally:
            conn.close()

    def log_action(self,
                  examination_id: int,
                  action_type: str,
                  action_description: str,
                  result: str,
                  result_detail: str = "") -> int:
        """Log an action to the database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            now = int(time.time() * 1000)
            cursor.execute('''
                INSERT INTO actions
                (examination_id, action_type, action_description, result, result_detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (examination_id, action_type, action_description, result, result_detail, now))

            conn.commit()
            action_id = cursor.lastrowid
            logger.info(f"[executioner] Logged action {action_id}: {action_type} - {result}")
            return action_id
        except Exception as e:
            logger.error(f"[executioner] Error logging action: {e}")
            raise
        finally:
            conn.close()

    def update_examination_status(self, examination_id: int, status: str) -> None:
        """Update examination status."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            now = int(time.time() * 1000)
            cursor.execute('''
                UPDATE examinations
                SET status = ?, updated_at = ?
                WHERE id = ?
            ''', (status, now, examination_id))
            conn.commit()
        finally:
            conn.close()

    def execute_autonomous_action(self, examination: Dict[str, Any]) -> None:
        """Execute autonomous action (update War Room)."""
        try:
            from backend.agent_integrations import call_gm_seat_api

            # Build finding dict for GM Seat API
            finding = {
                'finding_text': examination['finding_text'],
                'category': examination['category'],
                'importance_score': examination['importance_score'],
                'source_name': examination['source_name'],
                'gameplan': examination['gameplan']
            }

            # Call GM Seat API
            response = call_gm_seat_api(finding)

            # Log action
            result = "success" if response.get('status') == 'success' else "failed"
            self.log_action(
                examination_id=examination['id'],
                action_type='autonomous',
                action_description=f"Update War Room: {examination['finding_text'][:100]}",
                result=result,
                result_detail=str(response)
            )

            # Mark examination as executed
            self.update_examination_status(examination['id'], 'executed')

            logger.info(f"[executioner] Autonomous action executed for exam {examination['id']}: {result}")
        except Exception as e:
            logger.error(f"[executioner] Error executing autonomous action: {e}")
            self.log_action(
                examination_id=examination['id'],
                action_type='autonomous',
                action_description=f"Update War Room: {examination['finding_text'][:100]}",
                result='failed',
                result_detail=str(e)
            )
            self.update_examination_status(examination['id'], 'executed')

    def send_approval_alert(self, examination: Dict[str, Any]) -> None:
        """Send SMS alert for approval-required action."""
        try:
            from backend.agent_integrations import send_sms_alert

            # Send SMS
            if not self.user_phone_number:
                logger.warning(f"[executioner] No phone number configured for SMS alerts")
                self.log_action(
                    examination_id=examination['id'],
                    action_type='alert_user',
                    action_description=f"SMS Alert: {examination['finding_text'][:100]}",
                    result='pending',
                    result_detail="Phone number not configured"
                )
                return

            success = send_sms_alert(
                phone_number=self.user_phone_number,
                finding_text=examination['finding_text'],
                gameplan=examination['gameplan'],
                priority=examination['priority']
            )

            result = "sent" if success else "failed"
            self.log_action(
                examination_id=examination['id'],
                action_type='alert_user',
                action_description=f"SMS Alert: {examination['finding_text'][:100]}",
                result=result,
                result_detail=f"SMS to {self.user_phone_number}"
            )

            # Mark as pending (waiting for user reply)
            self.update_examination_status(examination['id'], 'pending_action')

            logger.info(f"[executioner] SMS alert sent for exam {examination['id']}: {result}")
        except Exception as e:
            logger.error(f"[executioner] Error sending approval alert: {e}")
            self.log_action(
                examination_id=examination['id'],
                action_type='alert_user',
                action_description=f"SMS Alert: {examination['finding_text'][:100]}",
                result='failed',
                result_detail=str(e)
            )

    def run_once(self) -> None:
        """Run one iteration: fetch pending examinations and execute actions."""
        logger.info("[executioner] Running executioner agent")

        examinations = self.get_pending_examinations()
        logger.info(f"[executioner] Found {len(examinations)} pending examinations")

        for exam in examinations:
            try:
                if exam['requires_approval']:
                    # Send SMS alert for approval
                    self.send_approval_alert(exam)
                else:
                    # Check if gameplan mentions updating war room
                    if 'update war room' in exam['gameplan'].lower():
                        self.execute_autonomous_action(exam)
                    else:
                        # Other autonomous actions not yet implemented
                        logger.debug(f"[executioner] Skipping exam {exam['id']}: gameplan not recognized")
            except Exception as e:
                logger.error(f"[executioner] Error processing examination {exam['id']}: {e}")

    def run_loop(self, interval_seconds: int = 300) -> None:
        """Run the executioner agent in a continuous loop (default 5 minutes)."""
        logger.info(f"[executioner] Starting executioner loop (interval: {interval_seconds}s)")

        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"[executioner] Error in executioner loop: {e}")

            time.sleep(interval_seconds)
