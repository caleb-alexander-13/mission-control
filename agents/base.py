# agents/base.py
import sqlite3
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
import time

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.db_path = DB_PATH

    def get_db_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def insert_research_finding(self,
                              finding_text: str,
                              source_url: str,
                              source_name: str,
                              importance_score: int,
                              category: str) -> int:
        """Insert a research finding into the database. Returns finding ID."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            now = int(time.time() * 1000)
            cursor.execute('''
                INSERT INTO research_findings
                (agent_name, finding_text, source_url, source_name, importance_score, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.agent_name, finding_text, source_url, source_name, importance_score, category, now, now))

            conn.commit()
            finding_id = cursor.lastrowid
            logger.info(f"[{self.agent_name}] Inserted finding {finding_id}: {finding_text[:50]}")
            return finding_id
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error inserting finding: {e}")
            raise
        finally:
            conn.close()

    def mark_examined(self, finding_id: int) -> None:
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

    @abstractmethod
    def run_once(self) -> None:
        """Run one iteration of the agent loop. Must be implemented by subclasses."""
        pass

    def run_loop(self, interval_seconds: int = 1800) -> None:
        """Run the agent in a continuous loop with given interval."""
        logger.info(f"[{self.agent_name}] Starting agent loop (interval: {interval_seconds}s)")

        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"[{self.agent_name}] Error in agent loop: {e}")

            time.sleep(interval_seconds)
