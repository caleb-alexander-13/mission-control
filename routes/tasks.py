from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
from pathlib import Path

router = APIRouter()

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

class TaskCreate(BaseModel):
    title: str
    project: str = None
    status: str = "queued"

class TaskUpdate(BaseModel):
    status: str

@router.get("/tasks")
def get_tasks(status: str = "all"):
    """Get tasks grouped by status."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status == "all":
            cursor.execute('SELECT * FROM tasks ORDER BY status, updated_at DESC')
        else:
            cursor.execute('SELECT * FROM tasks WHERE status = ? ORDER BY updated_at DESC', (status,))

        tasks = [dict(row) for row in cursor.fetchall()]

        # Group by status
        grouped = {
            "queued": [t for t in tasks if t['status'] == 'queued'],
            "in_progress": [t for t in tasks if t['status'] == 'in_progress'],
            "done": [t for t in tasks if t['status'] == 'done']
        }

        conn.close()

        if status == "all":
            return grouped
        else:
            return {status: grouped.get(status, [])}

    except Exception as e:
        return {"error": str(e)}

@router.post("/tasks")
def create_task(task: TaskCreate):
    """Create a new task."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        cursor = conn.cursor()

        now = int(__import__('time').time() * 1000)
        cursor.execute('''
            INSERT INTO tasks(title, status, project, created_at, updated_at)
            VALUES(?, ?, ?, ?, ?)
        ''', (task.title, task.status, task.project, now, now))

        conn.commit()
        task_id = cursor.lastrowid
        conn.close()

        return {"id": task_id, "title": task.title, "status": task.status}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate):
    """Update task status."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        cursor = conn.cursor()

        now = int(__import__('time').time() * 1000)
        cursor.execute('UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?',
                      (update.status, now, task_id))
        conn.commit()
        conn.close()

        return {"id": task_id, "status": update.status}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
