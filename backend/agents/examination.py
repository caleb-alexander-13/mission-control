"""Examination agent for analyzing findings and creating gameplans."""

import logging
import time
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from agent_integrations import examine_findings_with_claude
from utils.notifications import send_notification

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'


class ExaminationAgent(BaseAgent):
    """Analyzes research findings and creates actionable gameplans."""

    def __init__(self):
        super().__init__("examination")

    def run_loop(self, interval_seconds: int = 900) -> None:
        """Run examination agent loop every 15 minutes."""
        self.running = True
        logger.info(f"Starting examination agent loop (interval: {interval_seconds}s)")

        while self.running:
            try:
                self._examine_pending_findings()
            except Exception as e:
                logger.error(f"Error in examination agent: {e}", exc_info=True)

            time.sleep(interval_seconds)

    def _examine_pending_findings(self) -> None:
        """Get pending findings, analyze with Claude, and create examinations."""
        findings = self._get_pending_findings()

        if not findings:
            logger.debug("No pending findings to examine")
            return

        logger.info(f"Examining {len(findings)} pending findings")

        # Prepare findings for Claude
        findings_for_claude = [
            {
                "id": f["id"],
                "finding_text": f["finding_text"],
                "importance_score": f["importance_score"],
                "category": f["category"]
            }
            for f in findings
        ]

        # Get Claude analysis
        analysis_result = examine_findings_with_claude(findings_for_claude)

        if not analysis_result:
            logger.warning("Claude analysis returned empty result")
            return

        # Store examinations in database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        now = int(time.time() * 1000)

        for finding in findings:
            finding_id = finding["id"]
            if finding_id in analysis_result:
                result = analysis_result[finding_id]

                import json
                trade_action_json = None
                if result.get("trade_action"):
                    trade_action_json = json.dumps(result.get("trade_action"))

                cursor.execute('''
                    INSERT INTO examinations
                    (finding_id, claude_analysis, gameplan, priority, requires_approval, status, trade_action, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    finding_id,
                    result.get("analysis", ""),
                    result.get("gameplan", ""),
                    result.get("priority", "medium"),
                    1 if result.get("needs_approval", False) else 0,
                    'pending_action',
                    trade_action_json,
                    now,
                    now
                ))

                # Update finding status
                cursor.execute(
                    'UPDATE research_findings SET status = ?, updated_at = ? WHERE id = ?',
                    ('examined', now, finding_id)
                )

                # Send notification for approval-required items
                if result.get("needs_approval"):
                    agent = finding.get("agent_name", "unknown")
                    priority = result.get("priority", "medium").upper()
                    gameplan = result.get("gameplan", "")[:180]
                    send_notification(
                        f"[{agent.upper()} / {priority}] {gameplan}",
                        title="Action Required — Mission Control",
                        tags="rotating_light"
                    )

                logger.info(f"Created examination for finding {finding_id}")
            else:
                logger.warning(f"No analysis for finding {finding_id}")

        conn.commit()
        conn.close()

        logger.info(f"Created {len([f for f in findings if f['id'] in analysis_result])} examinations")

    def _get_pending_findings(self) -> List[Dict[str, Any]]:
        """Get all pending findings from database."""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, agent_name, finding_text, source_url, source_name,
                   importance_score, category, status, created_at
            FROM research_findings
            WHERE status = 'pending_examination'
            ORDER BY importance_score DESC, created_at DESC
            LIMIT 20
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
