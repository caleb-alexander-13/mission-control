"""Base agent class for all agents in the pipeline."""

import logging
import sqlite3
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'


class BaseAgent(ABC):
    """Base class for all agents in the pipeline."""

    def __init__(self, agent_name: str):
        """
        Initialize base agent.

        Args:
            agent_name: Name of the agent (e.g., 'sports', 'examination')
        """
        self.agent_name = agent_name
        self.running = False

    @abstractmethod
    def run_loop(self, interval_seconds: int) -> None:
        """
        Run the agent loop indefinitely with specified interval.

        Args:
            interval_seconds: Time to sleep between iterations
        """
        pass

    def stop(self) -> None:
        """Stop the agent loop."""
        self.running = False
        logger.info(f"{self.agent_name} agent stopping")

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def _insert_research_finding(
        self,
        finding_text: str,
        source_url: Optional[str] = None,
        source_name: Optional[str] = None,
        importance_score: Optional[int] = None,
        category: Optional[str] = None
    ) -> int:
        """
        Insert a research finding into the database (skip if duplicate).

        Returns:
            ID of the inserted finding (or existing ID if duplicate)
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Check if exact finding already exists (same agent, same or very similar text)
        cursor.execute('''
            SELECT id FROM research_findings
            WHERE agent_name = ? AND LOWER(finding_text) = LOWER(?)
            LIMIT 1
        ''', (self.agent_name, finding_text[:500]))

        existing = cursor.fetchone()
        if existing:
            conn.close()
            logger.debug(f"Skipping duplicate finding from {self.agent_name}: {finding_text[:50]}...")
            return existing[0]

        # Check if we've covered this topic recently (past 7 days) to avoid repetitive content
        # Extract first 50 chars as topic signature
        topic_sig = finding_text[:50].lower()
        seven_days_ago = int(time.time() * 1000) - (7 * 24 * 60 * 60 * 1000)

        cursor.execute('''
            SELECT id FROM research_findings
            WHERE agent_name = ? AND LOWER(finding_text) LIKE ? AND created_at > ?
            ORDER BY created_at DESC LIMIT 1
        ''', (self.agent_name, f"{topic_sig}%", seven_days_ago))

        recent_topic = cursor.fetchone()
        if recent_topic:
            conn.close()
            logger.debug(f"Skipping recent duplicate topic from {self.agent_name}: {finding_text[:50]}...")
            return recent_topic[0]

        now = int(time.time() * 1000)

        cursor.execute('''
            INSERT INTO research_findings
            (agent_name, finding_text, source_url, source_name, importance_score, category, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.agent_name,
            finding_text,
            source_url,
            source_name,
            importance_score,
            category,
            'pending_examination',
            now,
            now
        ))

        conn.commit()
        finding_id = cursor.lastrowid
        conn.close()

        logger.info(f"Inserted finding {finding_id} from {self.agent_name}")
        return finding_id

    def _get_pending_findings(self) -> List[Dict[str, Any]]:
        """Get all pending findings from database."""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, agent_name, finding_text, source_url, source_name,
                   importance_score, category, status, created_at
            FROM research_findings
            WHERE status = 'pending_examination'
            ORDER BY created_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
