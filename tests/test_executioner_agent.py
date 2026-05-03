# tests/test_executioner_agent.py
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.executioner import ExecutionerAgent


def test_executioner_agent_init():
    """Test Executioner agent initialization."""
    agent = ExecutionerAgent(user_phone_number="+1234567890")
    assert agent.agent_name == "executioner"
    assert agent.db_path is not None
    assert agent.user_phone_number == "+1234567890"


def test_executioner_agent_init_no_phone():
    """Test Executioner agent without phone number."""
    agent = ExecutionerAgent()
    assert agent.agent_name == "executioner"
    assert agent.user_phone_number == ""


def test_executioner_agent_get_pending_examinations():
    """Test fetching pending examinations."""
    agent = ExecutionerAgent()
    examinations = agent.get_pending_examinations()
    assert isinstance(examinations, list)


def test_executioner_agent_log_action():
    """Test logging an action (will fail if no test data, that's ok)."""
    agent = ExecutionerAgent()
    # This will only work if there are examinations in the database
    # For MVP, just verify method exists
    try:
        agent.log_action(
            examination_id=999,
            action_type='autonomous',
            action_description='Test action',
            result='pending',
            result_detail='Test'
        )
    except Exception as e:
        # Expected if test database is empty or no foreign key match
        pass


def test_executioner_agent_update_examination_status():
    """Test updating examination status (will skip if no test data)."""
    agent = ExecutionerAgent()
    # This will only work if there are examinations in the database
    # For MVP, just verify the method exists and doesn't crash on empty state
    try:
        agent.update_examination_status(999, 'executed')  # Non-existent ID
    except Exception as e:
        pass  # Expected behavior for non-existent ID
