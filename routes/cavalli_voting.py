from fastapi import APIRouter, HTTPException
import sqlite3
import json
from pathlib import Path

router = APIRouter()
DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'


@router.get("/cavalli/projects")
def get_projects():
    """Get all Cavalli projects with scores."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM cavalli_projects ORDER BY name')
        projects = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return {"projects": projects}
    except Exception as e:
        return {"error": str(e), "projects": []}


@router.post("/cavalli/vote")
def submit_vote(voter_name: str, weights: str, selections: str):
    """
    Submit a voter's weights and project selections (via query params).

    Args:
        voter_name: Name of the person voting
        weights: JSON string {roi, brand, speed, cost}
        selections: JSON string [project_id, ...]
    """
    try:
        weights_dict = json.loads(weights)
        selections_list = json.loads(selections)

        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        cursor = conn.cursor()

        # Store or update weights
        cursor.execute('''
            INSERT OR REPLACE INTO cavalli_votes
            (voter_name, roi_weight, brand_weight, speed_weight, cost_sensitivity)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            voter_name,
            weights_dict.get('roi', 0.25),
            weights_dict.get('brand', 0.25),
            weights_dict.get('speed', 0.25),
            weights_dict.get('cost', 0.25)
        ))

        # Clear old selections for this voter
        cursor.execute('DELETE FROM cavalli_selections WHERE voter_name = ?', (voter_name,))

        # Store new selections
        for project_id in selections_list:
            cursor.execute('''
                INSERT INTO cavalli_selections (voter_name, project_id, selected)
                VALUES (?, ?, 1)
            ''', (voter_name, project_id))

        conn.commit()
        conn.close()

        return {"status": "success", "voter": voter_name, "projects_selected": len(selections_list)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/cavalli/results")
def get_results():
    """Get aggregated voting results across all voters."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all voters and their weights
        cursor.execute('SELECT voter_name, roi_weight, brand_weight, speed_weight FROM cavalli_votes')
        voters = [dict(row) for row in cursor.fetchall()]

        # Get all projects
        cursor.execute('SELECT * FROM cavalli_projects ORDER BY name')
        projects = [dict(row) for row in cursor.fetchall()]

        # Get selections per voter per project
        cursor.execute('''
            SELECT voter_name, project_id, COUNT(*) as selected
            FROM cavalli_selections
            WHERE selected = 1
            GROUP BY voter_name, project_id
        ''')
        selections_raw = [dict(row) for row in cursor.fetchall()]

        # Build selection matrix
        selection_matrix = {}
        for sel in selections_raw:
            key = f"{sel['voter_name']}_{sel['project_id']}"
            selection_matrix[key] = True

        # Calculate consensus metrics
        project_stats = []
        for project in projects:
            votes = sum(1 for sel in selections_raw if sel['project_id'] == project['id'])
            vote_pct = (votes / max(len(voters), 1)) * 100 if voters else 0

            # Weighted score (using voter's weights)
            weighted_scores = []
            for voter in voters:
                key = f"{voter['voter_name']}_{project['id']}"
                if key in selection_matrix:
                    score = (
                        project['roi_score'] * voter['roi_weight'] +
                        project['brand_score'] * voter['brand_weight'] +
                        project['speed_score'] * voter['speed_weight']
                    )
                    weighted_scores.append(score)

            avg_weighted = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0

            project_stats.append({
                "id": project['id'],
                "name": project['name'],
                "cost": project['cost'],
                "votes": votes,
                "vote_percentage": round(vote_pct, 1),
                "avg_weighted_score": round(avg_weighted, 1),
                "selected_by": [sel['voter_name'] for sel in selections_raw if sel['project_id'] == project['id']]
            })

        # Calculate average weights
        if voters:
            avg_weights = {
                "roi": round(sum(v['roi_weight'] for v in voters) / len(voters), 2),
                "brand": round(sum(v['brand_weight'] for v in voters) / len(voters), 2),
                "speed": round(sum(v['speed_weight'] for v in voters) / len(voters), 2)
            }
        else:
            avg_weights = {"roi": 0.25, "brand": 0.25, "speed": 0.25}

        conn.close()

        return {
            "voters": voters,
            "projects": project_stats,
            "average_weights": avg_weights,
            "consensus_ranking": sorted(project_stats, key=lambda x: x['vote_percentage'], reverse=True)
        }
    except Exception as e:
        return {"error": str(e), "voters": [], "projects": []}


@router.get("/cavalli/voter/{voter_name}")
def get_voter_selections(voter_name: str):
    """Get one voter's selections and weights."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM cavalli_votes WHERE voter_name = ?', (voter_name,))
        vote = dict(cursor.fetchone()) if cursor.fetchone() else None

        cursor.execute('''
            SELECT p.* FROM cavalli_projects p
            INNER JOIN cavalli_selections s ON p.id = s.project_id
            WHERE s.voter_name = ? AND s.selected = 1
        ''', (voter_name,))
        selections = [dict(row) for row in cursor.fetchall()]

        conn.close()

        if not vote:
            return {"status": "not_found"}

        total_cost = sum(p['cost'] for p in selections)

        return {
            "voter": voter_name,
            "weights": {
                "roi": vote['roi_weight'],
                "brand": vote['brand_weight'],
                "speed": vote['speed_weight'],
                "cost_sensitivity": vote['cost_sensitivity']
            },
            "selections": selections,
            "total_cost": total_cost,
            "selection_count": len(selections)
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}
