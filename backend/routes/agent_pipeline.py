from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/agent-pipeline/findings-with-feedback")
async def get_findings_with_feedback(
    agent: str = Query(None, description="Filter by agent name"),
    limit: int = Query(50, description="Number of findings to return")
):
    """Get findings with user feedback status."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        query = """
            SELECT rf.id, rf.agent_name, rf.finding_text, rf.source_name,
                   rf.importance_score, rf.category, rf.created_at,
                   ff.feedback, ff.notes
            FROM research_findings rf
            LEFT JOIN finding_feedback ff ON rf.id = ff.finding_id
            WHERE 1=1
        """
        params = []

        if agent:
            query += " AND rf.agent_name = ?"
            params.append(agent)

        query += " ORDER BY rf.created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        findings = [
            {
                "id": row[0],
                "agent_name": row[1],
                "finding_text": row[2],
                "source_name": row[3],
                "importance_score": row[4],
                "category": row[5],
                "created_at": row[6],
                "feedback": row[7],
                "notes": row[8]
            }
            for row in rows
        ]

        conn.close()
        return findings
    except Exception as e:
        logger.error(f"Error fetching findings with feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent-pipeline/findings/{finding_id}/feedback")
async def submit_finding_feedback(finding_id: int, data: dict):
    """Submit feedback on a finding (important/not important)."""
    try:
        import time

        feedback = data.get("feedback")  # "important" or "not_important"
        notes = data.get("notes", "")

        if feedback not in ["important", "not_important"]:
            raise HTTPException(status_code=400, detail="feedback must be 'important' or 'not_important'")

        conn = get_db()
        cursor = conn.cursor()

        # Check if finding exists
        cursor.execute("SELECT id FROM research_findings WHERE id = ?", (finding_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")

        # Delete existing feedback and add new
        cursor.execute("DELETE FROM finding_feedback WHERE finding_id = ?", (finding_id,))

        now = int(time.time() * 1000)
        cursor.execute("""
            INSERT INTO finding_feedback (finding_id, feedback, notes, created_at)
            VALUES (?, ?, ?, ?)
        """, (finding_id, feedback, notes, now))

        conn.commit()
        conn.close()

        logger.info(f"Recorded feedback for finding {finding_id}: {feedback}")
        return {
            "status": "success",
            "message": f"Feedback recorded: {feedback}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback for finding {finding_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-pipeline/findings")
async def get_findings(
    status: str = Query(None, description="Filter by status: pending_examination or examined"),
    agent: str = Query(None, description="Filter by agent name"),
    importance_min: int = Query(None, description="Minimum importance score")
):
    """Get all research findings with optional filtering."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        query = "SELECT id, agent_name, finding_text, source_name, importance_score, category, status, created_at FROM research_findings WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if agent:
            query += " AND agent_name = ?"
            params.append(agent)
        if importance_min is not None:
            query += " AND importance_score >= ?"
            params.append(importance_min)

        query += " ORDER BY created_at DESC LIMIT 100"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        findings = [
            {
                "id": row[0],
                "agent_name": row[1],
                "finding_text": row[2],
                "source_name": row[3],
                "importance_score": row[4],
                "category": row[5],
                "status": row[6],
                "created_at": row[7]
            }
            for row in rows
        ]

        conn.close()
        return findings
    except Exception as e:
        logger.error(f"Error fetching findings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-pipeline/examinations")
async def get_examinations():
    """Get pending examinations."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.id, e.finding_id, rf.finding_text, e.claude_analysis,
                   e.gameplan, e.priority, e.requires_approval, e.status, e.created_at
            FROM examinations e
            JOIN research_findings rf ON e.finding_id = rf.id
            WHERE e.status = 'pending_action'
            ORDER BY e.created_at ASC
        """)

        rows = cursor.fetchall()
        examinations = [
            {
                "id": row[0],
                "finding_id": row[1],
                "finding_text": row[2],
                "claude_analysis": row[3],
                "gameplan": row[4],
                "priority": row[5],
                "requires_approval": bool(row[6]),
                "status": row[7],
                "created_at": row[8]
            }
            for row in rows
        ]

        conn.close()
        return examinations
    except Exception as e:
        logger.error(f"Error fetching examinations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-pipeline/approvals")
async def get_pending_approvals():
    """Get examinations pending user approval."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.id, e.finding_id, rf.finding_text, rf.agent_name, e.claude_analysis,
                   e.gameplan, e.priority, e.created_at
            FROM examinations e
            JOIN research_findings rf ON e.finding_id = rf.id
            WHERE e.status = 'pending_action' AND e.requires_approval = 1
            ORDER BY e.priority DESC, e.created_at ASC
        """)

        rows = cursor.fetchall()
        approvals = [
            {
                "id": row[0],
                "finding_id": row[1],
                "finding_text": row[2],
                "agent": row[3],
                "analysis": row[4],
                "gameplan": row[5],
                "priority": row[6],
                "created_at": row[7],
                "approve_url": f"/api/agent-pipeline/examinations/{row[0]}/approve",
                "deny_url": f"/api/agent-pipeline/examinations/{row[0]}/deny"
            }
            for row in rows
        ]

        conn.close()
        return {
            "total": len(approvals),
            "pending_approvals": approvals
        }
    except Exception as e:
        logger.error(f"Error fetching pending approvals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-pipeline/actions")
async def get_actions():
    """Get recent actions (last 24 hours)."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        now = int(datetime.now().timestamp() * 1000)
        yesterday = now - (24 * 60 * 60 * 1000)

        cursor.execute("""
            SELECT id, examination_id, action_type, action_description, result, created_at, executed_at
            FROM actions
            WHERE created_at >= ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (yesterday,))

        rows = cursor.fetchall()
        actions = [
            {
                "id": row[0],
                "examination_id": row[1],
                "action_type": row[2],
                "action_description": row[3],
                "result": row[4],
                "created_at": row[5],
                "executed_at": row[6]
            }
            for row in rows
        ]

        conn.close()
        return actions
    except Exception as e:
        logger.error(f"Error fetching actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-pipeline/status")
async def get_status():
    """Get agent status and last activity."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        agents = ["sports", "finance", "creative", "tech"]
        agent_status = {}

        for agent in agents:
            # Get status and last finding
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status='pending_examination' THEN 1 ELSE 0 END) as pending,
                       MAX(created_at) as last_finding
                FROM research_findings
                WHERE agent_name = ?
            """, (agent,))

            row = cursor.fetchone()
            agent_status[agent] = {
                "status": "idle" if not row[2] else "working",
                "findings_total": row[0] or 0,
                "findings_pending": row[1] or 0,
                "last_activity": row[2] or None
            }

        # Examination agent status
        cursor.execute("SELECT COUNT(*) FROM examinations WHERE status='pending_action'")
        pending_exams = cursor.fetchone()[0]
        agent_status["examination"] = {
            "status": "idle" if pending_exams == 0 else "analyzing",
            "pending_examinations": pending_exams
        }

        # Executioner agent status (count pending examinations awaiting execution)
        cursor.execute("SELECT COUNT(*) FROM examinations WHERE status='pending_action'")
        pending_actions = cursor.fetchone()[0]
        agent_status["executioner"] = {
            "status": "idle" if pending_actions == 0 else "executing",
            "pending_actions": pending_actions
        }

        conn.close()
        return {
            "agents": agent_status,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-pipeline/cost-summary")
async def get_cost_summary():
    """Get cost summary (tokens, SMS, API calls)."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get token usage totals
        cursor.execute("""
            SELECT
                SUM(input_tokens) as total_input,
                SUM(output_tokens) as total_output,
                SUM(cache_read_tokens) as total_cache_read,
                SUM(cache_creation_tokens) as total_cache_creation
            FROM token_usage
        """)

        tokens = cursor.fetchone()

        # Calculate cost (using Claude 3.5 Sonnet pricing as example)
        # Input: $3 per MTok, Output: $15 per MTok, Cache read: $0.30 per MTok, Cache creation: $3.75 per MTok
        input_tokens = tokens[0] or 0
        output_tokens = tokens[1] or 0
        cache_read = tokens[2] or 0
        cache_creation = tokens[3] or 0

        input_cost = (input_tokens / 1_000_000) * 3.00
        output_cost = (output_tokens / 1_000_000) * 15.00
        cache_read_cost = (cache_read / 1_000_000) * 0.30
        cache_creation_cost = (cache_creation / 1_000_000) * 3.75

        total_cost = input_cost + output_cost + cache_read_cost + cache_creation_cost

        conn.close()

        return {
            "total_cost": round(total_cost, 4),
            "tokens_used": {
                "input": input_tokens,
                "output": output_tokens,
                "cache_read": cache_read,
                "cache_creation": cache_creation
            },
            "cost_breakdown": {
                "input_cost": round(input_cost, 4),
                "output_cost": round(output_cost, 4),
                "cache_read_cost": round(cache_read_cost, 4),
                "cache_creation_cost": round(cache_creation_cost, 4)
            },
            "sms_sent": 0,
            "api_calls": {
                "newsapi": 0,
                "github": 0,
                "hackernews": 0,
                "yahoo_finance": 0,
                "gm_seat": 0
            }
        }
    except Exception as e:
        logger.error(f"Error fetching cost summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent-pipeline/examinations/{exam_id}/approve")
async def approve_examination(exam_id: int):
    """Approve a pending examination for automatic execution."""
    try:
        import time

        conn = get_db()
        cursor = conn.cursor()

        # Check if examination exists and requires approval
        cursor.execute("SELECT id, status FROM examinations WHERE id = ?", (exam_id,))
        exam = cursor.fetchone()

        if not exam:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Examination {exam_id} not found")

        # Mark as pending_action so executioner picks it up immediately
        now = int(datetime.now().timestamp() * 1000)
        cursor.execute("""
            UPDATE examinations
            SET status = ?, requires_approval = 0, updated_at = ?
            WHERE id = ?
        """, ("pending_action", now, exam_id))

        # Log the approval decision
        cursor.execute("""
            INSERT INTO actions
            (examination_id, action_type, action_description, result, created_at, executed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (exam_id, "approval", "User approved examination", "success", now, now))

        conn.commit()
        conn.close()

        logger.info(f"User approved examination {exam_id}")
        return {
            "status": "success",
            "message": f"Examination {exam_id} approved and queued for execution"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving examination {exam_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent-pipeline/examinations/{exam_id}/deny")
async def deny_examination(exam_id: int):
    """Deny a pending examination (skip it)."""
    try:
        import time

        conn = get_db()
        cursor = conn.cursor()

        # Check if examination exists
        cursor.execute("SELECT id, status FROM examinations WHERE id = ?", (exam_id,))
        exam = cursor.fetchone()

        if not exam:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Examination {exam_id} not found")

        # Mark as denied
        now = int(datetime.now().timestamp() * 1000)
        cursor.execute("""
            UPDATE examinations
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, ("denied", now, exam_id))

        # Log the denial decision
        cursor.execute("""
            INSERT INTO actions
            (examination_id, action_type, action_description, result, created_at, executed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (exam_id, "approval", "User denied examination", "skipped", now, now))

        conn.commit()
        conn.close()

        logger.info(f"User denied examination {exam_id}")
        return {
            "status": "success",
            "message": f"Examination {exam_id} denied and archived"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error denying examination {exam_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-pipeline/examinations/{exam_id}/conversation")
async def get_conversation(exam_id: int):
    """Get conversation history for an examination."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get examination details
        cursor.execute("""
            SELECT e.id, e.finding_id, rf.finding_text, e.claude_analysis, e.gameplan, e.priority
            FROM examinations e
            JOIN research_findings rf ON e.finding_id = rf.id
            WHERE e.id = ?
        """, (exam_id,))

        exam = cursor.fetchone()
        if not exam:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Examination {exam_id} not found")

        # Get conversation history
        cursor.execute("""
            SELECT role, message, created_at FROM examination_conversations
            WHERE examination_id = ?
            ORDER BY created_at ASC
        """, (exam_id,))

        messages = cursor.fetchall()
        conversation = [
            {
                "role": msg[0],
                "message": msg[1],
                "timestamp": msg[2]
            }
            for msg in messages
        ]

        conn.close()

        return {
            "examination_id": exam[0],
            "finding_id": exam[1],
            "finding_text": exam[2],
            "analysis": exam[3],
            "gameplan": exam[4],
            "priority": exam[5],
            "conversation": conversation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation for exam {exam_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-pipeline/trading-log")
async def get_trading_log(limit: int = Query(50, description="Number of trades to return")):
    """Get trading history with P&L details."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get all trades with current prices
        cursor.execute("""
            SELECT id, ticker, action, shares, price, cash_impact, reason, created_at
            FROM paper_trades
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        trades = cursor.fetchall()

        # Get current cash
        cursor.execute("SELECT balance FROM paper_cash WHERE id=1")
        cash_row = cursor.fetchone()
        current_cash = cash_row[0] if cash_row else 0

        # Get current portfolio
        cursor.execute("SELECT ticker, shares, avg_cost FROM paper_portfolio WHERE shares > 0")
        holdings = cursor.fetchall()

        trade_list = []
        total_pnl = 0
        total_value = current_cash

        for trade in trades:
            trade_dict = {
                "id": trade[0],
                "ticker": trade[1],
                "action": trade[2],
                "shares": trade[3],
                "price": trade[4],
                "cash_impact": trade[5],
                "reason": trade[6],
                "timestamp": trade[7]
            }
            trade_list.append(trade_dict)

        # Calculate current portfolio value
        for holding in holdings:
            ticker, shares, avg_cost = holding
            # For now, use avg_cost as current price (would need live data)
            position_value = shares * avg_cost
            total_value += position_value
            pnl = (avg_cost - avg_cost) * shares  # Placeholder
            total_pnl += pnl

        conn.close()

        return {
            "trades": trade_list,
            "summary": {
                "cash": round(current_cash, 2),
                "total_value": round(total_value, 2),
                "total_pnl": round(total_pnl, 2),
                "trade_count": len(trade_list)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching trading log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent-pipeline/examinations/{exam_id}/ask")
async def ask_agent(exam_id: int, data: dict):
    """Ask the agent a follow-up question about the examination."""
    try:
        import time
        from anthropic import Anthropic

        question = data.get("question")
        if not question:
            raise HTTPException(status_code=400, detail="question required")

        conn = get_db()
        cursor = conn.cursor()

        # Get examination details
        cursor.execute("""
            SELECT e.id, e.finding_id, rf.finding_text, rf.agent_name, e.claude_analysis, e.gameplan, e.priority
            FROM examinations e
            JOIN research_findings rf ON e.finding_id = rf.id
            WHERE e.id = ?
        """, (exam_id,))

        exam = cursor.fetchone()
        if not exam:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Examination {exam_id} not found")

        # Get conversation history
        cursor.execute("""
            SELECT role, message FROM examination_conversations
            WHERE examination_id = ?
            ORDER BY created_at ASC
        """, (exam_id,))

        history = cursor.fetchall()

        # Store user question
        now = int(time.time() * 1000)
        cursor.execute("""
            INSERT INTO examination_conversations (examination_id, role, message, created_at)
            VALUES (?, ?, ?, ?)
        """, (exam_id, "user", question, now))
        conn.commit()

        # Build conversation context
        conv_text = "\n".join([f"{msg[0].upper()}: {msg[1]}" for msg in history])
        if conv_text:
            conv_text += f"\nUSER: {question}"
        else:
            conv_text = f"USER: {question}"

        # Call Claude for follow-up analysis
        client = Anthropic()
        prompt = f"""You are a research agent ({exam[3]}) who made an initial finding and analysis.

ORIGINAL FINDING:
{exam[2]}

YOUR INITIAL ANALYSIS:
{exam[4]}

YOUR GAMEPLAN:
{exam[5]}

CONVERSATION SO FAR:
{conv_text}

Provide a detailed response to the user's follow-up question. Be specific and substantiate your reasoning with facts and logic. Consider trade-offs and alternatives if relevant."""

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        agent_response = response.content[0].text

        # Store agent response
        now = int(time.time() * 1000)
        cursor.execute("""
            INSERT INTO examination_conversations (examination_id, role, message, created_at)
            VALUES (?, ?, ?, ?)
        """, (exam_id, "agent", agent_response, now))
        conn.commit()
        conn.close()

        logger.info(f"Agent responded to question on examination {exam_id}")

        return {
            "examination_id": exam_id,
            "question": question,
            "response": agent_response,
            "timestamp": now
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error asking agent about exam {exam_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# SPORTS ARTICLE DRAFT ENDPOINTS
# =====================================================================

@router.get("/agent-pipeline/article-drafts")
async def get_article_drafts(status: str = "draft", limit: int = 10):
    """Get article drafts for review."""
    try:
        from agents.research.content_generator import ContentGenerator

        drafts = ContentGenerator.get_pending_drafts(limit)
        return {
            "drafts": drafts,
            "count": len(drafts)
        }
    except Exception as e:
        logger.error(f"Error fetching drafts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent-pipeline/article-drafts/{draft_id}/approve")
async def approve_article_draft(draft_id: int, feedback: str = ""):
    """Approve an article draft for publication to GMSeat."""
    try:
        import sqlite3
        from pathlib import Path
        from agents.research.content_generator import ContentGenerator
        from agents.research.gmseat_publisher import GMSeatPublisher

        # Get draft details
        db_path = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT title, content, topic, inspiration_sources FROM sports_article_drafts WHERE id = ?', (draft_id,))
        draft = cursor.fetchone()
        conn.close()

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        # Approve the draft
        success = ContentGenerator.approve_draft(draft_id, feedback)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to approve draft")

        # Parse inspiration sources
        import json
        inspiration_sources = []
        try:
            if draft['inspiration_sources']:
                inspiration_sources = json.loads(draft['inspiration_sources'])
        except:
            inspiration_sources = []

        # Publish to GMSeat
        gmseat_result = GMSeatPublisher.publish_article(
            draft['title'],
            draft['content'],
            draft['topic'],
            draft_id,
            inspiration_sources
        )

        if gmseat_result:
            # Update draft with GMSeat URL
            gmseat_url = gmseat_result.get('url', f"https://gmseat.com/articles/{gmseat_result.get('article_id')}")
            GMSeatPublisher.update_draft_published(draft_id, gmseat_url)
            GMSeatPublisher.send_notification(draft['title'], draft['content'])

            return {
                "status": "approved_and_published",
                "draft_id": draft_id,
                "gmseat_url": gmseat_url
            }
        else:
            # Approved but GMSeat publish failed
            return {
                "status": "approved",
                "draft_id": draft_id,
                "warning": "Draft approved but GMSeat publishing failed"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving draft {draft_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent-pipeline/article-drafts/{draft_id}/reject")
async def reject_article_draft(draft_id: int, feedback: str = ""):
    """Reject an article draft with feedback."""
    try:
        from agents.research.content_generator import ContentGenerator

        success = ContentGenerator.reject_draft(draft_id, feedback)
        if success:
            return {"status": "rejected", "draft_id": draft_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to reject draft")
    except Exception as e:
        logger.error(f"Error rejecting draft {draft_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-pipeline/war-room-articles")
async def get_war_room_articles(limit: int = Query(10, description="Number of articles to return")):
    """Fetch published articles from NFL War Room for review."""
    try:
        war_room_db = Path.home() / 'Desktop' / 'NFL War Room' / 'backend' / 'draft.db'

        if not war_room_db.exists():
            return {"status": "success", "articles": [], "count": 0}

        conn = sqlite3.connect(str(war_room_db), timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, content, topic, created_at, published_at, status
            FROM war_room_articles
            WHERE status = 'published'
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "status": "success",
            "articles": articles,
            "count": len(articles)
        }

    except Exception as e:
        logger.error(f"Error fetching War Room articles: {e}")
        # Return empty list on error - War Room might not be accessible
        return {
            "status": "success",
            "articles": [],
            "count": 0
        }


@router.get("/agent-pipeline/trades-with-findings")
async def get_trades_with_findings(limit: int = Query(20, description="Number of trades to return")):
    """Fetch trades with their associated findings for detailed context."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                pt.id,
                pt.ticker,
                pt.action,
                pt.shares,
                pt.price,
                pt.cash_impact,
                pt.reason,
                pt.created_at,
                rf.finding_text,
                rf.source_name,
                rf.importance_score
            FROM paper_trades pt
            LEFT JOIN research_findings rf ON pt.finding_id = rf.id
            ORDER BY pt.created_at DESC
            LIMIT ?
        """, (limit,))

        trades = []
        for row in cursor.fetchall():
            trades.append({
                "id": row[0],
                "ticker": row[1],
                "action": row[2],
                "shares": row[3],
                "price": row[4],
                "cash_impact": row[5],
                "reason": row[6],
                "created_at": row[7],
                "finding_text": row[8],
                "source_name": row[9],
                "importance_score": row[10]
            })

        conn.close()

        return {
            "status": "success",
            "trades": trades,
            "count": len(trades)
        }

    except Exception as e:
        logger.error(f"Error fetching trades with findings: {e}")
        return {
            "status": "success",
            "trades": [],
            "count": 0
        }
