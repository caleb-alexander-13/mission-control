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
        Insert a research finding into the database.

        Returns:
            ID of the inserted finding
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

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
