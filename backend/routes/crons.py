from fastapi import APIRouter
import sqlite3
from pathlib import Path

router = APIRouter()

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

@router.get("/crons")
def get_crons():
    """Get all registered cron jobs."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, schedule, last_run_at, last_run_status, project
            FROM cron_jobs
            ORDER BY last_run_at DESC
        ''')

        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {"jobs": jobs}

    except Exception as e:
        return {"error": str(e), "jobs": []}
