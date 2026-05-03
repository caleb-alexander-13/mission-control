"""Tests for the agents runner module."""

import pytest
import threading
import time
from unittest.mock import patch, MagicMock

from backend.agents_runner import (
    AgentsRunner,
    init_agents_runner,
    start_agents,
    stop_agents,
    get_agents_status,
)


class TestAgentsRunner:
    """Test suite for AgentsRunner class."""

    def test_init_with_phone_number(self):
        """Test AgentsRunner initialization with phone number."""
        runner = AgentsRunner(user_phone_number="+1234567890")
        assert runner.user_phone_number == "+1234567890"
        assert runner.running is False
        assert len(runner.threads) == 0
        assert len(runner.agents) == 6  # All 6 agents initialized

    def test_init_without_phone_number(self):
        """Test AgentsRunner initialization without phone number."""
        runner = AgentsRunner()
        assert runner.user_phone_number == ""
        assert runner.running is False

    def test_init_with_env_phone_number(self):
        """Test AgentsRunner initialization with environment variable."""
        with patch.dict("os.environ", {"USER_PHONE_NUMBER": "+9876543210"}):
            runner = AgentsRunner()
            assert runner.user_phone_number == "+9876543210"

    def test_agents_initialized(self):
        """Test that all agents are properly initialized."""
        runner = AgentsRunner()
        assert "sports" in runner.agents
        assert "finance" in runner.agents
        assert "creative" in runner.agents
        assert "tech" in runner.agents
        assert "examination" in runner.agents
        assert "executioner" in runner.agents

    def test_intervals_configured(self):
        """Test that agent intervals are properly configured."""
        runner = AgentsRunner()
        assert runner.intervals["sports"] == 1800
        assert runner.intervals["finance"] == 1800
        assert runner.intervals["creative"] == 1800
        assert runner.intervals["tech"] == 1800
        assert runner.intervals["examination"] == 900
        assert runner.intervals["executioner"] == 300

    def test_get_status_initial(self):
        """Test getting runner status initially."""
        runner = AgentsRunner()
        status = runner.get_status()

        assert "running" in status
        assert "alive_threads" in status
        assert "total_threads" in status
        assert "user_phone" in status
        assert "agents" in status
        assert status["running"] is False
        assert status["total_threads"] == 0

    def test_get_status_with_phone(self):
        """Test status includes phone number."""
        runner = AgentsRunner(user_phone_number="+1234567890")
        status = runner.get_status()
        assert status["user_phone"] == "+1234567890"

    def test_get_status_without_phone(self):
        """Test status shows not configured when no phone."""
        runner = AgentsRunner()
        status = runner.get_status()
        assert status["user_phone"] == "not configured"

    @patch("backend.agents_runner.SportsAgent")
    @patch("backend.agents_runner.FinanceAgent")
    @patch("backend.agents_runner.CreativeAgent")
    @patch("backend.agents_runner.TechAgent")
    @patch("backend.agents_runner.ExaminationAgent")
    @patch("backend.agents_runner.ExecutionerAgent")
    def test_start_agents(self, mock_exec, mock_exam, mock_tech, mock_creative, mock_finance, mock_sports):
        """Test starting agents creates threads."""
        # Mock agents to prevent actual execution
        for mock_agent_class in [mock_sports, mock_finance, mock_creative, mock_tech, mock_exam, mock_exec]:
            mock_instance = MagicMock()
            mock_instance.run_loop = MagicMock(side_effect=lambda interval_seconds: time.sleep(0.1))
            mock_agent_class.return_value = mock_instance

        runner = AgentsRunner()

        # Mock the run_loop to avoid infinite loops
        for agent_name in runner.agents:
            runner.agents[agent_name].run_loop = MagicMock()

        runner.start()

        assert runner.running is True
        assert len(runner.threads) == 6

        # Clean up
        runner.stop()

    @patch("backend.agents_runner.SportsAgent")
    @patch("backend.agents_runner.FinanceAgent")
    @patch("backend.agents_runner.CreativeAgent")
    @patch("backend.agents_runner.TechAgent")
    @patch("backend.agents_runner.ExaminationAgent")
    @patch("backend.agents_runner.ExecutionerAgent")
    def test_start_when_already_running(self, mock_exec, mock_exam, mock_tech, mock_creative, mock_finance, mock_sports):
        """Test that start is idempotent."""
        # Mock agents
        for mock_agent_class in [mock_sports, mock_finance, mock_creative, mock_tech, mock_exam, mock_exec]:
            mock_instance = MagicMock()
            mock_instance.run_loop = MagicMock()
            mock_agent_class.return_value = mock_instance

        runner = AgentsRunner()

        # Mock the run_loop
        for agent_name in runner.agents:
            runner.agents[agent_name].run_loop = MagicMock()

        runner.start()
        thread_count_1 = len(runner.threads)

        runner.start()
        thread_count_2 = len(runner.threads)

        assert thread_count_1 == thread_count_2  # No additional threads
        runner.stop()

    @patch("backend.agents_runner.SportsAgent")
    @patch("backend.agents_runner.FinanceAgent")
    @patch("backend.agents_runner.CreativeAgent")
    @patch("backend.agents_runner.TechAgent")
    @patch("backend.agents_runner.ExaminationAgent")
    @patch("backend.agents_runner.ExecutionerAgent")
    def test_stop_agents(self, mock_exec, mock_exam, mock_tech, mock_creative, mock_finance, mock_sports):
        """Test stopping agents."""
        # Mock agents
        for mock_agent_class in [mock_sports, mock_finance, mock_creative, mock_tech, mock_exam, mock_exec]:
            mock_instance = MagicMock()
            mock_instance.run_loop = MagicMock()
            mock_agent_class.return_value = mock_instance

        runner = AgentsRunner()

        # Mock the run_loop
        for agent_name in runner.agents:
            runner.agents[agent_name].run_loop = MagicMock()

        runner.start()
        assert runner.running is True

        runner.stop()
        assert runner.running is False


class TestGlobalFunctions:
    """Test suite for global module functions."""

    def test_init_agents_runner(self):
        """Test global agents runner initialization."""
        runner = init_agents_runner(user_phone_number="+1234567890")
        assert runner is not None
        assert isinstance(runner, AgentsRunner)

    def test_init_agents_runner_singleton(self):
        """Test that init_agents_runner returns same instance."""
        runner1 = init_agents_runner()
        runner2 = init_agents_runner()
        assert runner1 is runner2

    def test_get_agents_status_initialized(self):
        """Test getting status when initialized."""
        runner = init_agents_runner(user_phone_number="+1234567890")
        status = get_agents_status()

        assert status["running"] is False
        assert "agents" in status
        assert status["user_phone"] == "+1234567890"
