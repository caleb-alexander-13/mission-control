# backend/project_integrations.py
"""Route findings to relevant projects (Cavalli, Hilda, War Room, Mission Control)."""

import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def route_finding_to_projects(finding: Dict[str, Any], examination: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Route a finding to relevant projects based on content and category.

    Returns list of project integration actions.
    """
    actions = []

    # Analyze finding to determine which projects it affects
    finding_text = finding.get("finding_text", "").lower()
    agent = finding.get("agent_name", "").lower()
    category = finding.get("category", "").lower()
    priority = examination.get("priority", "").lower()
    gameplan = examination.get("gameplan", "")

    # FINANCE FINDINGS → CAVALLI (revenue/marketing opportunities)
    if agent == "finance":
        cavalli_keywords = ["event", "sponsorship", "marketing", "partnership", "revenue", "advertising", "brand"]
        if any(kw in finding_text for kw in cavalli_keywords) and priority in ["high", "critical"]:
            actions.append({
                "project": "cavalli",
                "action": "revenue_opportunity",
                "finding_id": finding.get("id"),
                "description": f"Potential revenue/marketing angle: {gameplan}",
                "url": f"https://cavalli.local/opportunities"  # Replace with actual URL
            })

    # SPORTS FINDINGS → GM SEAT WAR ROOM (scouting updates)
    if agent == "sports":
        war_room_keywords = ["injury", "trade", "transfer", "draft", "coaching", "prospect", "player"]
        if any(kw in finding_text or kw in category for kw in war_room_keywords):
            actions.append({
                "project": "war_room",
                "action": "scouting_update",
                "finding_id": finding.get("id"),
                "description": gameplan,
                "category": category,
                "priority": priority,
                "url": f"http://localhost:8000/api/war-room/update"
            })

    # CREATIVE FINDINGS → HILDA PORTFOLIO (design/portfolio improvements)
    if agent == "creative":
        portfolio_keywords = ["design", "trend", "inspiration", "tool", "ai creative", "award", "portfolio"]
        if any(kw in finding_text or kw in category for kw in portfolio_keywords):
            actions.append({
                "project": "hilda_portfolio",
                "action": "design_inspiration",
                "finding_id": finding.get("id"),
                "description": f"Design/portfolio idea: {gameplan}",
                "source": finding.get("source_name"),
                "url": finding.get("source_url")
            })

    # TECH FINDINGS → MISSION CONTROL + CAVALLI (tech stack, competitive advantage)
    if agent == "tech":
        if priority in ["high", "critical"]:
            # Track for Mission Control improvements
            actions.append({
                "project": "mission_control",
                "action": "tech_opportunity",
                "finding_id": finding.get("id"),
                "description": f"Tech advancement: {gameplan}",
                "category": category,
                "url": f"http://localhost:8000/api/agent-pipeline/findings/{finding.get('id')}"
            })

        # Also check if relevant to Cavalli (AI tools, automation, competitive advantage)
        cavalli_keywords = ["ai", "automation", "tool", "workflow", "efficiency"]
        if any(kw in finding_text for kw in cavalli_keywords) and priority in ["high", "critical"]:
            actions.append({
                "project": "cavalli",
                "action": "tech_competitive_advantage",
                "finding_id": finding.get("id"),
                "description": f"Tech advantage for venue: {gameplan}",
                "category": category
            })

    logger.info(f"Routed finding {finding.get('id')} to {len(actions)} projects")
    return actions


def execute_project_integration(action: Dict[str, Any]) -> bool:
    """
    Execute a project integration action.

    Returns True if successful.
    """
    try:
        project = action.get("project")
        action_type = action.get("action")

        if project == "war_room" and action_type == "scouting_update":
            # Send to War Room API
            import requests
            payload = {
                "finding_text": action.get("description"),
                "category": action.get("category"),
                "importance_score": 7,  # Medium-high
                "source_name": "Mission Control Scouting",
                "gameplan": action.get("description")
            }
            response = requests.post(
                action.get("url"),
                json=payload,
                timeout=10
            )
            return response.status_code == 200

        elif project == "cavalli" and action_type == "revenue_opportunity":
            # Log opportunity for manual review
            logger.info(f"CAVALLI OPPORTUNITY: {action.get('description')}")
            return True

        elif project == "cavalli" and action_type == "tech_competitive_advantage":
            # Log tech advantage for manual review
            logger.info(f"CAVALLI TECH ADVANTAGE: {action.get('description')}")
            return True

        elif project == "hilda_portfolio" and action_type == "design_inspiration":
            # Log design inspiration
            logger.info(f"HILDA INSPIRATION: {action.get('description')} (source: {action.get('source')})")
            return True

        elif project == "mission_control" and action_type == "tech_opportunity":
            # Log tech opportunity for self-improvement
            logger.info(f"MISSION CONTROL TECH: {action.get('description')}")
            return True

        return False

    except Exception as e:
        logger.error(f"Project integration failed: {e}")
        return False


def get_project_integrations_summary() -> Dict[str, Any]:
    """Get summary of project integration opportunities."""
    return {
        "cavalli": {
            "description": "Hudson Valley wedding venue - revenue, marketing, tech opportunities",
            "integration_types": ["revenue_opportunity", "tech_competitive_advantage"]
        },
        "hilda_portfolio": {
            "description": "Interior designer portfolio - design trends, creative inspiration",
            "integration_types": ["design_inspiration"]
        },
        "war_room": {
            "description": "NFL War Room scouting system - player/team intelligence",
            "integration_types": ["scouting_update"]
        },
        "mission_control": {
            "description": "This system - tech advancements and self-improvement",
            "integration_types": ["tech_opportunity"]
        }
    }
