import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_get_findings():
    """Test GET /api/agent-pipeline/findings"""
    response = client.get("/api/agent-pipeline/findings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_findings_with_filters():
    """Test GET /api/agent-pipeline/findings with query parameters"""
    response = client.get("/api/agent-pipeline/findings?status=pending_examination&agent=sports&importance_min=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # If results exist, verify filters were applied
    results = response.json()
    if results:
        for finding in results:
            assert finding["status"] == "pending_examination"
            assert finding["agent_name"] == "sports"
            assert finding["importance_score"] >= 5

def test_get_examinations():
    """Test GET /api/agent-pipeline/examinations"""
    response = client.get("/api/agent-pipeline/examinations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # If results exist, verify structure
    results = response.json()
    if results:
        for exam in results:
            assert "id" in exam
            assert "finding_id" in exam
            assert "finding_text" in exam
            assert "claude_analysis" in exam
            assert "gameplan" in exam
            assert "priority" in exam
            assert "requires_approval" in exam
            assert "status" in exam
            assert "created_at" in exam

def test_get_actions():
    """Test GET /api/agent-pipeline/actions"""
    response = client.get("/api/agent-pipeline/actions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # Verify structure of actions
    results = response.json()
    if results:
        for action in results:
            assert "id" in action
            assert "examination_id" in action
            assert "action_type" in action
            assert "result" in action
            assert "created_at" in action

def test_get_status():
    """Test GET /api/agent-pipeline/status"""
    response = client.get("/api/agent-pipeline/status")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "timestamp" in data

    agents = data["agents"]
    # Verify research agents
    for agent_name in ["sports", "finance", "creative", "tech"]:
        assert agent_name in agents
        agent = agents[agent_name]
        assert "status" in agent
        assert agent["status"] in ["idle", "working"]
        assert "findings_total" in agent
        assert "findings_pending" in agent
        assert "last_activity" in agent

    # Verify examination agent
    assert "examination" in agents
    exam_agent = agents["examination"]
    assert "status" in exam_agent
    assert exam_agent["status"] in ["idle", "analyzing"]
    assert "pending_examinations" in exam_agent

    # Verify executioner agent
    assert "executioner" in agents
    exec_agent = agents["executioner"]
    assert "status" in exec_agent
    assert exec_agent["status"] in ["idle", "executing"]
    assert "pending_actions" in exec_agent

def test_get_cost_summary():
    """Test GET /api/agent-pipeline/cost-summary"""
    response = client.get("/api/agent-pipeline/cost-summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_cost" in data
    assert "tokens_used" in data
    assert "cost_breakdown" in data
    assert "sms_sent" in data
    assert "api_calls" in data

    # Verify token structure
    tokens = data["tokens_used"]
    assert "input" in tokens
    assert "output" in tokens
    assert "cache_read" in tokens
    assert "cache_creation" in tokens

    # Verify cost breakdown
    breakdown = data["cost_breakdown"]
    assert "input_cost" in breakdown
    assert "output_cost" in breakdown
    assert "cache_read_cost" in breakdown
    assert "cache_creation_cost" in breakdown

def test_approve_action_success():
    """Test POST /api/agent-pipeline/approve-action - approve"""
    payload = {
        "examination_id": 999,  # Non-existent ID for test
        "approved": True
    }
    response = client.post("/api/agent-pipeline/approve-action", json=payload)
    # Should succeed even with non-existent ID (no FK constraint enforced)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "approved" in data["message"]

def test_approve_action_reject():
    """Test POST /api/agent-pipeline/approve-action - reject"""
    payload = {
        "examination_id": 999,  # Non-existent ID for test
        "approved": False
    }
    response = client.post("/api/agent-pipeline/approve-action", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "rejected" in data["message"]

def test_approve_action_missing_id():
    """Test POST /api/agent-pipeline/approve-action - missing examination_id"""
    payload = {
        "approved": True
    }
    response = client.post("/api/agent-pipeline/approve-action", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "examination_id" in data["detail"]

def test_health_check():
    """Verify app is running"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
