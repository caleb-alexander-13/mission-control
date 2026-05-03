"""
Agent orchestration and lifecycle management.

Manages parallel execution of all agent loops with configurable intervals,
graceful shutdown, and status monitoring.
"""

import threading
import logging
import os
import time
from typing import Dict, Optional

from agents.research.sports import SportsAgent
from agents.research.finance import FinanceAgent
from agents.research.creative import CreativeAgent
from agents.research.tech import TechAgent
from agents.examination import ExaminationAgent
from agents.executioner import ExecutionerAgent

logger = logging.getLogger(__name__)


class AgentsRunner:
    """Orchestrates all agents running in parallel."""

    def __init__(self, user_phone_number: Optional[str] = None):
        """
        Initialize the agents runner.

        Args:
            user_phone_number: Optional phone number for the executioner agent notifications.
        """
        self.user_phone_number = user_phone_number or os.getenv("USER_PHONE_NUMBER", "")
        self.agents = {}
        self.threads = []
        self.running = False
        self._lock = threading.Lock()

        # Initialize all agents
        self.agents["sports"] = SportsAgent()
        self.agents["finance"] = FinanceAgent()
        self.agents["creative"] = CreativeAgent()
        self.agents["tech"] = TechAgent()
        self.agents["examination"] = ExaminationAgent()
        self.agents["executioner"] = ExecutionerAgent(
            user_phone_number=self.user_phone_number
        )

        # Agent intervals (in seconds)
        self.intervals = {
            "sports": 1800,  # 30 minutes
            "finance": 1800,  # 30 minutes
            "creative": 1800,  # 30 minutes
            "tech": 1800,  # 30 minutes
            "examination": 900,  # 15 minutes
            "executioner": 300,  # 5 minutes
        }

        logger.info("AgentsRunner initialized")

    def _run_agent(self, agent_name: str) -> None:
        """
        Run an agent loop in a thread.

        Args:
            agent_name: Name of the agent to run.
        """
        agent = self.agents[agent_name]
        interval = self.intervals[agent_name]

        logger.info(f"Starting {agent_name} agent loop (interval: {interval}s)")

        try:
            agent.run_loop(interval_seconds=interval)
        except Exception as e:
            logger.error(f"Error in {agent_name} agent: {e}", exc_info=True)
        finally:
            logger.warning(f"{agent_name} agent loop exited")

    def start(self) -> None:
        """Start all agents in background threads."""
        with self._lock:
            if self.running:
                logger.warning("Agents already running")
                return

            self.running = True

        logger.info("Starting all agents...")

        # Start research agents (sports, finance, creative, tech)
        research_agents = ["sports", "finance", "creative", "tech"]
        for agent_name in research_agents:
            thread = threading.Thread(
                target=self._run_agent,
                args=(agent_name,),
                daemon=True,
                name=f"{agent_name}-agent-thread",
            )
            thread.start()
            self.threads.append(thread)
            logger.info(f"Started {agent_name} agent thread")

        # Start examination agent
        exam_thread = threading.Thread(
            target=self._run_agent,
            args=("examination",),
            daemon=True,
            name="examination-agent-thread",
        )
        exam_thread.start()
        self.threads.append(exam_thread)
        logger.info("Started examination agent thread")

        # Start executioner agent
        exec_thread = threading.Thread(
            target=self._run_agent,
            args=("executioner",),
            daemon=True,
            name="executioner-agent-thread",
        )
        exec_thread.start()
        self.threads.append(exec_thread)
        logger.info("Started executioner agent thread")

        logger.info(f"All {len(self.threads)} agents started successfully")

    def stop(self) -> None:
        """Stop all agents (graceful shutdown)."""
        logger.info("Stopping all agents...")

        with self._lock:
            self.running = False

        # Threads are daemonic, so they'll stop when main thread exits.
        # Give them a moment to finish current iterations.
        time.sleep(1)

        alive_threads = [t for t in self.threads if t.is_alive()]
        if alive_threads:
            logger.info(f"{len(alive_threads)} agent threads still alive")
        else:
            logger.info("All agent threads stopped")

    def get_status(self) -> Dict:
        """
        Get status of all agents.

        Returns:
            Dictionary with runner status and thread information.
        """
        with self._lock:
            is_running = self.running

        alive_count = sum(1 for t in self.threads if t.is_alive())

        return {
            "running": is_running,
            "alive_threads": alive_count,
            "total_threads": len(self.threads),
            "user_phone": self.user_phone_number if self.user_phone_number else "not configured",
            "agents": list(self.agents.keys()),
        }


# Global agents runner instance
_agents_runner: Optional[AgentsRunner] = None
_runner_lock = threading.Lock()


def init_agents_runner(user_phone_number: Optional[str] = None) -> AgentsRunner:
    """
    Initialize the global agents runner.

    Args:
        user_phone_number: Optional phone number for notifications.

    Returns:
        The global AgentsRunner instance.
    """
    global _agents_runner

    with _runner_lock:
        if _agents_runner is None:
            _agents_runner = AgentsRunner(user_phone_number=user_phone_number)
        return _agents_runner


def start_agents() -> None:
    """Start the agents runner."""
    global _agents_runner

    with _runner_lock:
        if _agents_runner is None:
            _agents_runner = init_agents_runner()

    _agents_runner.start()


def stop_agents() -> None:
    """Stop the agents runner."""
    global _agents_runner

    with _runner_lock:
        if _agents_runner:
            _agents_runner.stop()


def get_agents_status() -> Dict:
    """
    Get status of the agents runner.

    Returns:
        Status dictionary or error message if not initialized.
    """
    global _agents_runner

    with _runner_lock:
        if _agents_runner:
            return _agents_runner.get_status()

    return {"status": "not initialized"}
