from fastapi import APIRouter
import sqlite3
from pathlib import Path
from datetime import datetime

router = APIRouter()

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

@router.get("/agent/status")
def agent_status():
    """Get current agent status: idle/working, last heartbeat, active sessions."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get active sessions
        cursor.execute('''
            SELECT * FROM sessions WHERE status = 'active'
            ORDER BY started_at DESC LIMIT 1
        ''')
        active = cursor.fetchone()

        if not active:
            return {
                "status": "idle",
                "current_session_id": None,
                "current_project": None,
                "last_heartbeat": None,
                "last_tool": None,
                "last_tool_at": None,
                "active_sessions_count": 0,
                "tools_last_5min": 0
            }

        session_id = active['session_id']

        # Get last tool call
        cursor.execute('''
            SELECT * FROM tool_events
            WHERE session_id = ? AND event_type = 'PreToolUse'
            ORDER BY created_at DESC LIMIT 1
        ''', (session_id,))
        last_tool = cursor.fetchone()

        # Determine status: working if last tool < 30 seconds ago
        now_ms = int(datetime.now().timestamp() * 1000)
        last_tool_age_ms = now_ms - (last_tool['created_at'] if last_tool else 0)
        is_working = last_tool_age_ms < 30000

        # Count tools in last 5 min
        cursor.execute('''
            SELECT COUNT(*) as count FROM tool_events
            WHERE session_id = ? AND event_type = 'PreToolUse'
            AND created_at > ?
        ''', (session_id, now_ms - 300000))
        tools_5min = cursor.fetchone()['count']

        conn.close()

        return {
            "status": "working" if is_working else "idle",
            "current_session_id": session_id,
            "current_project": active['project'],
            "last_heartbeat": last_tool['created_at'] if last_tool else None,
            "last_tool": last_tool['tool_name'] if last_tool else None,
            "last_tool_at": last_tool['created_at'] if last_tool else None,
            "active_sessions_count": 1,
            "tools_last_5min": tools_5min
        }

    except Exception as e:
        return {"error": str(e), "status": "idle"}
