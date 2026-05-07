from fastapi import APIRouter, Query
import sqlite3
from pathlib import Path

router = APIRouter()

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

@router.get("/activity/feed")
def activity_feed(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    """Get recent activity feed: tool calls and file events combined."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get tool events
        cursor.execute('''
            SELECT 'tool' as type, id, session_id, tool_name, created_at
            FROM tool_events
            WHERE event_type = 'PreToolUse'
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        items = [dict(row) for row in cursor.fetchall()]

        # Get file events
        cursor.execute('''
            SELECT 'file' as type, id, session_id, file_path as path, event_type, created_at
            FROM file_events
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        items.extend([dict(row) for row in cursor.fetchall()])

        # Sort by created_at descending
        items.sort(key=lambda x: x['created_at'], reverse=True)
        items = items[:limit]

        # Get total count
        cursor.execute('SELECT COUNT(*) as count FROM tool_events WHERE event_type = "PreToolUse"')
        total = cursor.fetchone()['count']

        conn.close()

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        return {"error": str(e), "items": [], "total": 0}
