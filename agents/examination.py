# agents/examination.py
import sqlite3
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

class ExaminationAgent(BaseAgent):
    """Agent that examines research findings and generates gameplans."""

    def __init__(self):
        super().__init__("examination")
        self.db_path = DB_PATH

    def get_pending_findings(self) -> List[Dict[str, Any]]:
        """Get all findings pending examination."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, agent_name, finding_text, source_name, importance_score, category
                FROM research_findings
                WHERE status = 'pending_examination'
                ORDER BY created_at ASC
            ''')

            findings = [dict(row) for row in cursor.fetchall()]
            return findings
        finally:
            conn.close()

    def insert_examination(self,
                         finding_id: int,
                         claude_analysis: str,
                         gameplan: str,
                         priority: str,
                         requires_approval: bool) -> int:
        """Insert an examination result into the database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            now = int(time.time() * 1000)
            requires_approval_int = 1 if requires_approval else 0

            cursor.execute('''
                INSERT INTO examinations
                (finding_id, claude_analysis, gameplan, priority, requires_approval, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (finding_id, claude_analysis, gameplan, priority, requires_approval_int, now, now))

            conn.commit()
            examination_id = cursor.lastrowid
            logger.info(f"[examination] Inserted examination {examination_id} for finding {finding_id}")
            return examination_id
        except Exception as e:
            logger.error(f"[examination] Error inserting examination: {e}")
            raise
        finally:
            conn.close()

    def mark_finding_examined(self, finding_id: int) -> None:
        """Mark a finding as examined."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            now = int(time.time() * 1000)
            cursor.execute('''
                UPDATE research_findings
                SET status = 'examined', updated_at = ?
                WHERE id = ?
            ''', (now, finding_id))
            conn.commit()
        finally:
            conn.close()

    def run_once(self) -> None:
        """Run one iteration: fetch pending findings, examine with Claude, store results."""
        logger.info("[examination] Running examination agent")

        findings = self.get_pending_findings()
        logger.info(f"[examination] Found {len(findings)} pending findings")

        if not findings:
            return

        # Call Claude to examine findings
        from backend.agent_integrations import examine_findings_with_claude

        try:
            examination_results = examine_findings_with_claude(findings)

            for finding_id, result in examination_results.items():
                try:
                    finding_id = int(finding_id)

                    # Extract fields from Claude response
                    analysis = result.get('analysis', '')
                    gameplan = result.get('gameplan', '')
                    priority = result.get('priority', 'medium')
                    needs_approval = result.get('needs_approval', False)

                    # Insert examination
                    self.insert_examination(
                        finding_id=finding_id,
                        claude_analysis=analysis,
                        gameplan=gameplan,
                        priority=priority,
                        requires_approval=needs_approval
                    )

                    # Mark finding as examined
                    self.mark_finding_examined(finding_id)

                except Exception as e:
                    logger.error(f"[examination] Error processing examination result: {e}")
        except Exception as e:
            logger.error(f"[examination] Error examining findings: {e}")
