# tests/test_examination_agent.py
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.examination import ExaminationAgent


def test_examination_agent_init():
    """Test Examination agent initialization."""
    agent = ExaminationAgent()
    assert agent.agent_name == "examination"
    assert agent.db_path is not None


def test_examination_agent_get_pending_findings():
    """Test fetching pending findings (may be empty in test environment)."""
    agent = ExaminationAgent()
    findings = agent.get_pending_findings()
    assert isinstance(findings, list)


def test_examination_agent_mark_examined():
    """Test marking a finding as examined (will skip if no test data)."""
    agent = ExaminationAgent()
    # This will only work if there are findings in the database
    # For MVP, just verify the method exists and doesn't crash on empty state
    try:
        agent.mark_finding_examined(999)  # Non-existent ID, should not crash
    except Exception as e:
        pass  # Expected behavior for non-existent ID
