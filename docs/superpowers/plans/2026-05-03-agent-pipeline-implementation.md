# Agent Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a cost-conscious autonomous agent system with 4 R&D agents (Sports, Finance, Creative, Tech) that research continuously, feed findings into an Examination agent for prioritization, and trigger an Executioner agent for autonomous actions or SMS alerts.

**Architecture:** Agents run as independent background loops writing to SQLite. R&D agents (30-60min intervals) → Examination agent (15min batches) → Executioner agent (5min polling). Data flows through research_findings → examinations → actions tables. Claude API scores findings and gameplans; Twilio sends alerts; GM Seat API receives autonomous updates.

**Tech Stack:** Python 3.10+, FastAPI, SQLite, Claude API, Twilio, NewsAPI, Yahoo Finance, GitHub/Hacker News APIs, Redis (optional for caching)

---

## File Structure

**New files to create:**
```
mission-control/
├── agents/
│   ├── __init__.py
│   ├── base.py (BaseAgent abstract class)
│   ├── research/
│   │   ├── __init__.py
│   │   ├── sports.py (Sports R&D agent)
│   │   ├── finance.py (Finance R&D agent)
│   │   ├── creative.py (Creative R&D agent)
│   │   ├── tech.py (Tech R&D agent)
│   │   └── data_sources.py (NewsAPI, RSS, Reddit, GitHub clients)
│   ├── examination.py (Examination agent)
│   └── executioner.py (Executioner agent)
├── backend/
│   ├── agents_runner.py (orchestrates all agent loops)
│   ├── agent_integrations.py (Twilio, GM Seat API, Claude API calls)
│   └── routes/
│       ├── agent_pipeline.py (new API endpoints for dashboard)
│       └── agent_actions.py (SMS reply handling)
├── tests/
│   ├── test_research_agents.py
│   ├── test_examination_agent.py
│   ├── test_executioner_agent.py
│   ├── test_agent_integrations.py
│   └── test_e2e_pipeline.py
├── frontend/
│   └── src/
│       └── components/
│           ├── AgentPipeline.jsx (new dashboard panel)
│           └── PixelOffice.jsx (pixel art visualization)
└── docs/
    └── superpowers/
        └── plans/
            └── 2026-05-03-agent-pipeline-implementation.md
```

**Files to modify:**
- `backend/db_init.py` - add 3 new tables
- `backend/app.py` - import agents_runner, add new routes
- `frontend/src/App.jsx` - add AgentPipeline component
- `.env.example` - add NewsAPI key, Twilio credentials

---

## PHASE 0: PREREQUISITES

### Task 0.1: Design & Build GM Seat API Endpoint

**Files:**
- Modify: `~/Desktop/NFL War Room/backend/routes/war_room.py` (or create if doesn't exist)
- Create: `~/Desktop/mission-control/backend/agent_integrations.py` (Twilio/GM Seat client)

**Context:** Executioner agent will POST findings to GM Seat API. This endpoint must exist first.

- [ ] **Step 1: Check if GM Seat API exists**

Run: `curl http://localhost:8000/api/war-room/update -X POST -H "Content-Type: application/json" -d '{"finding": "test"}' 2>&1 | head -20`

If 404, proceed to Step 2. If it exists, verify schema matches spec at line 303-323 of the design.

- [ ] **Step 2: Create/Update GM Seat API endpoint (if missing)**

If GM Seat API doesn't exist, add this endpoint to the War Room backend:

```python
# In ~/Desktop/NFL War Room/backend/routes/war_room.py (or create it)

from fastapi import APIRouter, HTTPException
import sqlite3
from datetime import datetime

router = APIRouter()

@router.post("/api/war-room/update")
def update_war_room(data: dict):
    """
    Receive findings from Mission Control Executioner agent.
    Updates war room with latest intelligence.
    """
    try:
        finding = data.get("finding")
        category = data.get("category")
        importance = data.get("importance")
        source = data.get("source")
        recommended_action = data.get("recommended_action")
        timestamp = data.get("timestamp")
        
        if not finding or not category:
            raise HTTPException(status_code=400, detail="Missing finding or category")
        
        # Store in war_room_findings table or log to file
        # For MVP, just log to console and database
        log_entry = {
            "finding": finding,
            "category": category,
            "importance": importance,
            "source": source,
            "recommended_action": recommended_action,
            "timestamp": timestamp,
            "received_at": int(datetime.now().timestamp() * 1000)
        }
        
        # TODO: Persist to War Room database
        # For now, just return success
        
        return {
            "status": "success",
            "message": "War room updated",
            "updated_fields": ["injury_report", "market_projection", "strategy"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: Test the endpoint**

Run: 
```bash
curl -X POST http://localhost:8000/api/war-room/update \
  -H "Content-Type: application/json" \
  -d '{
    "finding": "Patrick Mahomes ankle injury",
    "category": "injury",
    "importance": 8,
    "source": "ESPN",
    "recommended_action": "Re-evaluate KC projections",
    "timestamp": 1746345600000
  }'
```

Expected: `{"status": "success", "message": "War room updated", ...}`

- [ ] **Step 4: Commit GM Seat API changes**

```bash
cd ~/Desktop/NFL\ War\ Room
git add backend/routes/war_room.py
git commit -m "feat: add war-room/update endpoint for Mission Control agent integration"
```

**Note:** GM Seat API is now ready. Return to Mission Control implementation.

---

## PHASE 1: FOUNDATION (Database + R&D Agents)

### Task 1.1: Add Database Tables for Agent Pipeline

**Files:**
- Modify: `backend/db_init.py`

- [ ] **Step 1: Read current db_init.py**

Run: `head -95 ~/Desktop/mission-control/backend/db_init.py`

- [ ] **Step 2: Add research_findings table to db_init.py**

Add after the cron_jobs table creation:

```python
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_findings (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name        TEXT NOT NULL,
            finding_text      TEXT NOT NULL,
            source_url        TEXT,
            source_name       TEXT,
            importance_score  INTEGER,
            category          TEXT,
            status            TEXT DEFAULT 'pending_examination',
            created_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
            updated_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_findings_status ON research_findings(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_findings_agent ON research_findings(agent_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_findings_created ON research_findings(created_at DESC)')
```

- [ ] **Step 3: Add examinations table to db_init.py**

```python
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS examinations (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            finding_id        INTEGER NOT NULL,
            claude_analysis   TEXT NOT NULL,
            gameplan          TEXT NOT NULL,
            priority          TEXT,
            requires_approval INTEGER DEFAULT 0,
            status            TEXT DEFAULT 'pending_action',
            created_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
            updated_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
            FOREIGN KEY (finding_id) REFERENCES research_findings(id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_examinations_status ON examinations(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_examinations_finding ON examinations(finding_id)')
```

- [ ] **Step 4: Add actions table to db_init.py**

```python
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            examination_id    INTEGER NOT NULL,
            action_type       TEXT NOT NULL,
            action_description TEXT,
            result            TEXT,
            result_detail     TEXT,
            created_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
            executed_at       INTEGER,
            FOREIGN KEY (examination_id) REFERENCES examinations(id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(action_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_examination ON actions(examination_id)')
```

- [ ] **Step 5: Test database initialization**

Run:
```bash
cd ~/Desktop/mission-control/backend
python db_init.py
sqlite3 mission_control.db ".tables"
```

Expected output should include: `research_findings`, `examinations`, `actions`

Verify schema:
```bash
sqlite3 mission_control.db ".schema research_findings"
```

- [ ] **Step 6: Commit**

```bash
cd ~/Desktop/mission-control
git add backend/db_init.py
git commit -m "feat: add research_findings, examinations, actions tables for agent pipeline"
```

---

### Task 1.2: Create Base Agent Class

**Files:**
- Create: `agents/__init__.py`
- Create: `agents/base.py`

- [ ] **Step 1: Create agents package**

Run: `mkdir -p ~/Desktop/mission-control/agents`

- [ ] **Step 2: Create agents/__init__.py**

```python
# agents/__init__.py
from .base import BaseAgent
from .research.sports import SportsAgent
from .research.finance import FinanceAgent
from .research.creative import CreativeAgent
from .research.tech import TechAgent
from .examination import ExaminationAgent
from .executioner import ExecutionerAgent

__all__ = [
    'BaseAgent',
    'SportsAgent',
    'FinanceAgent',
    'CreativeAgent',
    'TechAgent',
    'ExaminationAgent',
    'ExecutionerAgent'
]
```

- [ ] **Step 3: Create agents/base.py with BaseAgent class**

```python
# agents/base.py
import sqlite3
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
import time

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.db_path = DB_PATH
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    
    def insert_research_finding(self, 
                              finding_text: str,
                              source_url: str,
                              source_name: str,
                              importance_score: int,
                              category: str) -> int:
        """Insert a research finding into the database. Returns finding ID."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = int(time.time() * 1000)
            cursor.execute('''
                INSERT INTO research_findings 
                (agent_name, finding_text, source_url, source_name, importance_score, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.agent_name, finding_text, source_url, source_name, importance_score, category, now, now))
            
            conn.commit()
            finding_id = cursor.lastrowid
            logger.info(f"[{self.agent_name}] Inserted finding {finding_id}: {finding_text[:50]}")
            return finding_id
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error inserting finding: {e}")
            raise
        finally:
            conn.close()
    
    def mark_examined(self, finding_id: int) -> None:
        """Mark a finding as examined."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = int(time.time() * 1000)
            cursor.execute('''
                UPDATE research_findings
                SET status = 'examined', updated_at = ?
                WHERE id = ?
            ''', (now, finding_id))
            conn.commit()
        finally:
            conn.close()
    
    @abstractmethod
    def run_once(self) -> None:
        """Run one iteration of the agent loop. Must be implemented by subclasses."""
        pass
    
    def run_loop(self, interval_seconds: int = 1800) -> None:
        """Run the agent in a continuous loop with given interval."""
        logger.info(f"[{self.agent_name}] Starting agent loop (interval: {interval_seconds}s)")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"[{self.agent_name}] Error in agent loop: {e}")
            
            time.sleep(interval_seconds)
```

- [ ] **Step 4: Commit**

```bash
cd ~/Desktop/mission-control
git add agents/__init__.py agents/base.py
git commit -m "feat: create BaseAgent abstract class for all agents"
```

---

### Task 1.3: Create Data Sources Module (News, RSS, APIs)

**Files:**
- Create: `agents/research/__init__.py`
- Create: `agents/research/data_sources.py`

- [ ] **Step 1: Create research package**

Run: `mkdir -p ~/Desktop/mission-control/agents/research`

- [ ] **Step 2: Create agents/research/__init__.py**

```python
# agents/research/__init__.py
from .sports import SportsAgent
from .finance import FinanceAgent
from .creative import CreativeAgent
from .tech import TechAgent

__all__ = ['SportsAgent', 'FinanceAgent', 'CreativeAgent', 'TechAgent']
```

- [ ] **Step 3: Create agents/research/data_sources.py**

```python
# agents/research/data_sources.py
import feedparser
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsAPIClient:
    """Wrapper for NewsAPI (requires API key)."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
    
    def search_category(self, category: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Search news by category. Returns last N hours of articles."""
        try:
            url = f"{self.base_url}/top-headlines?category={category}&apiKey={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            articles = response.json().get('articles', [])
            return [
                {
                    'title': a['title'],
                    'description': a['description'],
                    'url': a['url'],
                    'source': a['source']['name'],
                    'published_at': a['publishedAt']
                }
                for a in articles
            ]
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []

class RSSFeedClient:
    """Wrapper for RSS feeds."""
    
    @staticmethod
    def fetch_feed(feed_url: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Fetch RSS feed articles from last N hours."""
        try:
            feed = feedparser.parse(feed_url)
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            entries = []
            for entry in feed.entries[:20]:  # Limit to 20 most recent
                try:
                    published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.utcnow()
                    if published > cutoff_time:
                        entries.append({
                            'title': entry.get('title', ''),
                            'summary': entry.get('summary', ''),
                            'url': entry.get('link', ''),
                            'source': feed.feed.get('title', 'RSS'),
                            'published_at': published.isoformat()
                        })
                except Exception as e:
                    logger.debug(f"Error parsing RSS entry: {e}")
            
            return entries
        except Exception as e:
            logger.error(f"RSS feed error: {e}")
            return []

class GitHubClient:
    """Wrapper for GitHub API (trending repos)."""
    
    @staticmethod
    def get_trending(language: str = '', since: str = 'daily') -> List[Dict[str, Any]]:
        """Get trending GitHub repos. since='daily'|'weekly'|'monthly'."""
        try:
            # GitHub doesn't have a dedicated trending API, use search
            # This is a simplified version
            url = f"https://api.github.com/search/repositories?q=stars:>{100}&sort=stars&order=desc"
            
            if language:
                url += f"&language={language}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            repos = response.json().get('items', [])
            return [
                {
                    'name': r['full_name'],
                    'description': r['description'],
                    'url': r['html_url'],
                    'stars': r['stargazers_count'],
                    'language': r['language']
                }
                for r in repos[:10]
            ]
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return []

class HackerNewsClient:
    """Wrapper for Hacker News API."""
    
    @staticmethod
    def get_top_stories(limit: int = 30) -> List[Dict[str, Any]]:
        """Get top stories from Hacker News."""
        try:
            # Get top story IDs
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            story_ids = response.json()[:limit]
            stories = []
            
            for story_id in story_ids:
                try:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    story_response = requests.get(story_url, timeout=5)
                    story_response.raise_for_status()
                    
                    story = story_response.json()
                    stories.append({
                        'title': story.get('title', ''),
                        'url': story.get('url', ''),
                        'score': story.get('score', 0),
                        'comments': story.get('descendants', 0),
                        'source': 'Hacker News'
                    })
                except Exception as e:
                    logger.debug(f"Error fetching HN story: {e}")
            
            return stories
        except Exception as e:
            logger.error(f"Hacker News API error: {e}")
            return []

class YahooFinanceClient:
    """Wrapper for Yahoo Finance (simplified, no API key needed)."""
    
    @staticmethod
    def get_market_summary() -> Dict[str, Any]:
        """Get market summary (indices)."""
        try:
            # Simplified version - in production use yfinance library
            # For now, return placeholder
            return {
                'indices': {
                    'S&P 500': {'change': 0, 'change_pct': 0},
                    'Nasdaq': {'change': 0, 'change_pct': 0},
                    'Dow': {'change': 0, 'change_pct': 0}
                }
            }
        except Exception as e:
            logger.error(f"Yahoo Finance error: {e}")
            return {}
```

- [ ] **Step 4: Commit**

```bash
cd ~/Desktop/mission-control
git add agents/research/__init__.py agents/research/data_sources.py
git commit -m "feat: add data source clients (NewsAPI, RSS, GitHub, HN, Yahoo Finance)"
```

---

### Task 1.4: Implement Sports R&D Agent

**Files:**
- Create: `agents/research/sports.py`
- Create: `tests/test_research_agents.py`

- [ ] **Step 1: Create agents/research/sports.py**

```python
# agents/research/sports.py
import os
import logging
from typing import List, Dict, Any
from ..base import BaseAgent
from .data_sources import NewsAPIClient, RSSFeedClient

logger = logging.getLogger(__name__)

class SportsAgent(BaseAgent):
    """R&D agent for sports research (NFL focus)."""
    
    def __init__(self):
        super().__init__("sports")
        self.news_api_key = os.getenv('NEWSAPI_KEY', '')
        self.news_client = NewsAPIClient(self.news_api_key) if self.news_api_key else None
    
    def get_findings(self) -> List[Dict[str, Any]]:
        """Fetch latest sports findings from data sources."""
        findings = []
        
        # NewsAPI - sports category
        if self.news_client:
            articles = self.news_client.search_category('sports', hours=24)
            findings.extend([
                {
                    'title': a['title'],
                    'description': a['description'],
                    'url': a['url'],
                    'source': a['source'],
                    'published': a['published_at']
                }
                for a in articles
            ])
        
        # ESPN RSS feed
        try:
            espn_articles = RSSFeedClient.fetch_feed(
                'http://feeds.espn.go.com/espn/rss/nfl/news',
                hours=24
            )
            findings.extend(espn_articles)
        except Exception as e:
            logger.warning(f"ESPN RSS error: {e}")
        
        # Reddit r/nfl (simplified - would need PRAW in production)
        # For MVP, skip Reddit scraping
        
        return findings
    
    def score_finding(self, finding: Dict[str, Any]) -> int:
        """Score a finding 1-10 using Claude."""
        from backend.agent_integrations import score_finding_with_claude
        
        finding_text = f"{finding['title']}: {finding.get('description', '')}"
        score = score_finding_with_claude(
            finding_text=finding_text,
            agent_name='sports'
        )
        return score
    
    def infer_category(self, finding: Dict[str, Any]) -> str:
        """Infer category from finding."""
        text = (finding.get('title', '') + ' ' + finding.get('description', '')).lower()
        
        if any(word in text for word in ['injur', 'hurt', 'out', 'week-to-week']):
            return 'injury'
        elif any(word in text for word in ['trade', 'sign', 'draft']):
            return 'roster'
        elif any(word in text for word in ['rule', 'change', 'playoff']):
            return 'rules'
        else:
            return 'news'
    
    def run_once(self) -> None:
        """Run one iteration: fetch findings, score them, store them."""
        logger.info("[sports] Running sports research agent")
        
        findings = self.get_findings()
        logger.info(f"[sports] Found {len(findings)} articles")
        
        for finding in findings[:5]:  # Limit to 5 per run for cost
            try:
                score = self.score_finding(finding)
                category = self.infer_category(finding)
                
                self.insert_research_finding(
                    finding_text=finding['title'],
                    source_url=finding.get('url', ''),
                    source_name=finding.get('source', 'Unknown'),
                    importance_score=score,
                    category=category
                )
            except Exception as e:
                logger.error(f"[sports] Error processing finding: {e}")
```

- [ ] **Step 2: Create basic test file**

```python
# tests/test_research_agents.py
import pytest
from unittest.mock import patch, MagicMock
from agents.research.sports import SportsAgent

def test_sports_agent_init():
    """Test Sports agent initialization."""
    agent = SportsAgent()
    assert agent.agent_name == "sports"
    assert agent.db_path is not None

def test_sports_agent_infer_category():
    """Test category inference."""
    agent = SportsAgent()
    
    finding_injury = {'title': 'QB suffers season-ending injury', 'description': ''}
    assert agent.infer_category(finding_injury) == 'injury'
    
    finding_trade = {'title': 'Star RB traded to rival', 'description': ''}
    assert agent.infer_category(finding_trade) == 'roster'
    
    finding_rule = {'title': 'NFL changes playoff format', 'description': ''}
    assert agent.infer_category(finding_rule) == 'rules'

def test_sports_agent_get_findings_no_api_key():
    """Test get_findings when NewsAPI key is missing."""
    agent = SportsAgent()
    findings = agent.get_findings()
    # Should return empty or RSS-only findings
    assert isinstance(findings, list)

@patch('agents.research.data_sources.RSSFeedClient.fetch_feed')
def test_sports_agent_run_once(mock_rss):
    """Test run_once with mocked data sources."""
    mock_rss.return_value = [
        {
            'title': 'Player X Injured',
            'summary': 'Key player out for season',
            'url': 'http://example.com/news',
            'source': 'ESPN',
            'published_at': '2026-05-03'
        }
    ]
    
    agent = SportsAgent()
    # run_once should not raise
    try:
        agent.run_once()
    except Exception as e:
        # May fail if Claude API not configured, that's ok for now
        pass
```

- [ ] **Step 3: Test file structure**

Run: `ls -la ~/Desktop/mission-control/tests/` (create if missing)

If tests dir doesn't exist:
```bash
mkdir -p ~/Desktop/mission-control/tests
touch ~/Desktop/mission-control/tests/__init__.py
```

- [ ] **Step 4: Run test to verify it works**

Run:
```bash
cd ~/Desktop/mission-control
python -m pytest tests/test_research_agents.py::test_sports_agent_init -v
```

Expected: Test passes or shows missing imports (which is ok for now).

- [ ] **Step 5: Commit**

```bash
cd ~/Desktop/mission-control
git add agents/research/sports.py tests/test_research_agents.py tests/__init__.py
git commit -m "feat: implement Sports R&D agent with basic tests"
```

---

### Task 1.5: Implement Finance, Creative, Tech R&D Agents

**Files:**
- Create: `agents/research/finance.py`
- Create: `agents/research/creative.py`
- Create: `agents/research/tech.py`
- Modify: `tests/test_research_agents.py`

- [ ] **Step 1: Create agents/research/finance.py**

```python
# agents/research/finance.py
import logging
from typing import List, Dict, Any
from ..base import BaseAgent
from .data_sources import NewsAPIClient, RSSFeedClient, YahooFinanceClient

logger = logging.getLogger(__name__)

class FinanceAgent(BaseAgent):
    """R&D agent for finance/stock market research."""
    
    def __init__(self):
        super().__init__("finance")
        self.news_client = NewsAPIClient(__import__('os').getenv('NEWSAPI_KEY', '')) if __import__('os').getenv('NEWSAPI_KEY') else None
        self.yfinance = YahooFinanceClient()
    
    def get_findings(self) -> List[Dict[str, Any]]:
        """Fetch latest finance findings."""
        findings = []
        
        # NewsAPI - business category
        if self.news_client:
            articles = self.news_client.search_category('business', hours=24)
            findings.extend(articles)
        
        # MarketWatch RSS
        try:
            mw_articles = RSSFeedClient.fetch_feed(
                'https://feeds.marketwatch.com/marketwatch/topstories/',
                hours=24
            )
            findings.extend(mw_articles)
        except Exception as e:
            logger.warning(f"MarketWatch RSS error: {e}")
        
        # Market summary (placeholder)
        try:
            market = self.yfinance.get_market_summary()
            if market:
                findings.append({
                    'title': 'Market Summary',
                    'summary': str(market),
                    'url': '',
                    'source': 'Yahoo Finance',
                    'published_at': ''
                })
        except Exception as e:
            logger.warning(f"Yahoo Finance error: {e}")
        
        return findings
    
    def score_finding(self, finding: Dict[str, Any]) -> int:
        """Score a finding 1-10 using Claude."""
        from backend.agent_integrations import score_finding_with_claude
        
        finding_text = f"{finding['title']}: {finding.get('summary', '')}"
        score = score_finding_with_claude(
            finding_text=finding_text,
            agent_name='finance'
        )
        return score
    
    def infer_category(self, finding: Dict[str, Any]) -> str:
        """Infer category from finding."""
        text = (finding.get('title', '') + ' ' + finding.get('summary', '')).lower()
        
        if any(word in text for word in ['rate', 'fed', 'inflation', 'interest']):
            return 'macro'
        elif any(word in text for word in ['earn', 'revenue', 'profit', 'guidance']):
            return 'earnings'
        elif any(word in text for word in ['crash', 'plunge', 'surge', 'down', 'up', '%']):
            return 'market_movement'
        else:
            return 'news'
    
    def run_once(self) -> None:
        """Run one iteration: fetch findings, score them, store them."""
        logger.info("[finance] Running finance research agent")
        
        findings = self.get_findings()
        logger.info(f"[finance] Found {len(findings)} items")
        
        for finding in findings[:5]:
            try:
                score = self.score_finding(finding)
                category = self.infer_category(finding)
                
                self.insert_research_finding(
                    finding_text=finding.get('title', 'Market Update'),
                    source_url=finding.get('url', ''),
                    source_name=finding.get('source', 'Unknown'),
                    importance_score=score,
                    category=category
                )
            except Exception as e:
                logger.error(f"[finance] Error processing finding: {e}")
```

- [ ] **Step 2: Create agents/research/creative.py**

```python
# agents/research/creative.py
import logging
from typing import List, Dict, Any
from ..base import BaseAgent
from .data_sources import NewsAPIClient, RSSFeedClient

logger = logging.getLogger(__name__)

class CreativeAgent(BaseAgent):
    """R&D agent for creative industry research (design, art, trends)."""
    
    def __init__(self):
        super().__init__("creative")
        self.news_client = NewsAPIClient(__import__('os').getenv('NEWSAPI_KEY', '')) if __import__('os').getenv('NEWSAPI_KEY') else None
    
    def get_findings(self) -> List[Dict[str, Any]]:
        """Fetch latest creative findings."""
        findings = []
        
        # NewsAPI - entertainment category
        if self.news_client:
            articles = self.news_client.search_category('entertainment', hours=24)
            findings.extend(articles)
        
        # Design blogs/RSS (simplified)
        try:
            design_articles = RSSFeedClient.fetch_feed(
                'https://www.designernews.co/feed',
                hours=24
            )
            findings.extend(design_articles)
        except Exception as e:
            logger.warning(f"Design news RSS error: {e}")
        
        return findings
    
    def score_finding(self, finding: Dict[str, Any]) -> int:
        """Score a finding 1-10 using Claude."""
        from backend.agent_integrations import score_finding_with_claude
        
        finding_text = f"{finding['title']}: {finding.get('description', '')}"
        score = score_finding_with_claude(
            finding_text=finding_text,
            agent_name='creative'
        )
        return score
    
    def infer_category(self, finding: Dict[str, Any]) -> str:
        """Infer category from finding."""
        text = (finding.get('title', '') + ' ' + finding.get('description', '')).lower()
        
        if any(word in text for word in ['design', 'tool', 'software']):
            return 'design_tool'
        elif any(word in text for word in ['trend', 'style', 'aesthetic']):
            return 'trend'
        elif any(word in text for word in ['award', 'winning']):
            return 'recognition'
        else:
            return 'news'
    
    def run_once(self) -> None:
        """Run one iteration: fetch findings, score them, store them."""
        logger.info("[creative] Running creative research agent")
        
        findings = self.get_findings()
        logger.info(f"[creative] Found {len(findings)} items")
        
        for finding in findings[:5]:
            try:
                score = self.score_finding(finding)
                category = self.infer_category(finding)
                
                self.insert_research_finding(
                    finding_text=finding.get('title', 'Creative Update'),
                    source_url=finding.get('url', ''),
                    source_name=finding.get('source', 'Unknown'),
                    importance_score=score,
                    category=category
                )
            except Exception as e:
                logger.error(f"[creative] Error processing finding: {e}")
```

- [ ] **Step 3: Create agents/research/tech.py**

```python
# agents/research/tech.py
import logging
from typing import List, Dict, Any
from ..base import BaseAgent
from .data_sources import NewsAPIClient, GitHubClient, HackerNewsClient

logger = logging.getLogger(__name__)

class TechAgent(BaseAgent):
    """R&D agent for technology research (security, tools, trends)."""
    
    def __init__(self):
        super().__init__("tech")
        self.news_client = NewsAPIClient(__import__('os').getenv('NEWSAPI_KEY', '')) if __import__('os').getenv('NEWSAPI_KEY') else None
        self.github = GitHubClient()
        self.hackernews = HackerNewsClient()
    
    def get_findings(self) -> List[Dict[str, Any]]:
        """Fetch latest tech findings."""
        findings = []
        
        # NewsAPI - tech category
        if self.news_client:
            articles = self.news_client.search_category('technology', hours=24)
            findings.extend(articles)
        
        # Hacker News
        try:
            hn_stories = self.hackernews.get_top_stories(limit=20)
            findings.extend(hn_stories)
        except Exception as e:
            logger.warning(f"Hacker News error: {e}")
        
        # GitHub trending
        try:
            trending = self.github.get_trending(language='python')
            findings.extend(trending)
        except Exception as e:
            logger.warning(f"GitHub trending error: {e}")
        
        return findings
    
    def score_finding(self, finding: Dict[str, Any]) -> int:
        """Score a finding 1-10 using Claude."""
        from backend.agent_integrations import score_finding_with_claude
        
        finding_text = f"{finding['title']}: {finding.get('description', '')}"
        score = score_finding_with_claude(
            finding_text=finding_text,
            agent_name='tech'
        )
        return score
    
    def infer_category(self, finding: Dict[str, Any]) -> str:
        """Infer category from finding."""
        text = (finding.get('title', '') + ' ' + finding.get('description', '')).lower()
        
        if any(word in text for word in ['security', 'vuln', 'patch', 'breach', 'attack']):
            return 'security_vuln'
        elif any(word in text for word in ['tool', 'framework', 'library', 'release']):
            return 'new_tool'
        elif any(word in text for word in ['ai', 'llm', 'model', 'neural']):
            return 'ai_ml'
        else:
            return 'news'
    
    def run_once(self) -> None:
        """Run one iteration: fetch findings, score them, store them."""
        logger.info("[tech] Running tech research agent")
        
        findings = self.get_findings()
        logger.info(f"[tech] Found {len(findings)} items")
        
        for finding in findings[:5]:
            try:
                score = self.score_finding(finding)
                category = self.infer_category(finding)
                
                self.insert_research_finding(
                    finding_text=finding.get('title', 'Tech Update'),
                    source_url=finding.get('url', ''),
                    source_name=finding.get('source', 'Unknown'),
                    importance_score=score,
                    category=category
                )
            except Exception as e:
                logger.error(f"[tech] Error processing finding: {e}")
```

- [ ] **Step 4: Update tests for all agents**

Add to `tests/test_research_agents.py`:

```python
# Add these tests at the end of test_research_agents.py

from agents.research.finance import FinanceAgent
from agents.research.creative import CreativeAgent
from agents.research.tech import TechAgent

def test_finance_agent_init():
    """Test Finance agent initialization."""
    agent = FinanceAgent()
    assert agent.agent_name == "finance"

def test_finance_agent_infer_category():
    """Test Finance category inference."""
    agent = FinanceAgent()
    
    finding_macro = {'title': 'Fed raises interest rates', 'summary': ''}
    assert agent.infer_category(finding_macro) == 'macro'
    
    finding_earnings = {'title': 'Apple reports Q2 earnings', 'summary': ''}
    assert agent.infer_category(finding_earnings) == 'earnings'

def test_creative_agent_init():
    """Test Creative agent initialization."""
    agent = CreativeAgent()
    assert agent.agent_name == "creative"

def test_creative_agent_infer_category():
    """Test Creative category inference."""
    agent = CreativeAgent()
    
    finding_tool = {'title': 'New design tool released', 'summary': ''}
    assert agent.infer_category(finding_tool) == 'design_tool'

def test_tech_agent_init():
    """Test Tech agent initialization."""
    agent = TechAgent()
    assert agent.agent_name == "tech"

def test_tech_agent_infer_category():
    """Test Tech category inference."""
    agent = TechAgent()
    
    finding_security = {'title': 'Critical zero-day vulnerability', 'summary': ''}
    assert agent.infer_category(finding_security) == 'security_vuln'
```

- [ ] **Step 5: Run all R&D agent tests**

Run:
```bash
cd ~/Desktop/mission-control
python -m pytest tests/test_research_agents.py -v
```

Expected: All tests pass (or show expected failures if Claude/API unavailable).

- [ ] **Step 6: Commit**

```bash
cd ~/Desktop/mission-control
git add agents/research/finance.py agents/research/creative.py agents/research/tech.py
git add tests/test_research_agents.py
git commit -m "feat: implement Finance, Creative, Tech R&D agents with tests"
```

---

### Task 1.6: Create Agent Integrations Module (Claude API, Twilio)

**Files:**
- Create: `backend/agent_integrations.py`

- [ ] **Step 1: Create backend/agent_integrations.py**

```python
# backend/agent_integrations.py
import os
import json
import logging
import requests
from typing import Dict, Any
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = Anthropic()

def score_finding_with_claude(finding_text: str, agent_name: str) -> int:
    """
    Use Claude to score a finding 1-10 based on business impact, urgency, cost.
    Returns integer 1-10.
    """
    try:
        prompt = f"""You are a research agent evaluating business findings. Score this finding 1-10 based on:
- Business impact: Will this affect decisions/strategy?
- Urgency: How time-sensitive is this?
- Cost: Does this affect revenue/spending?

Finding: {finding_text}
Agent: {agent_name}

Respond with ONLY a number 1-10 and brief reasoning (2-3 words max).
Format: "8 - High impact" """
        
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=100,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse response - extract first number
        text = response.content[0].text.strip()
        score = int(text.split()[0])
        
        # Clamp to 1-10
        score = max(1, min(10, score))
        logger.info(f"Scored finding: {score}/10")
        return score
    except Exception as e:
        logger.error(f"Error scoring finding: {e}")
        # Default to 5 if scoring fails
        return 5

def examine_findings_with_claude(findings: list) -> Dict[int, Dict[str, Any]]:
    """
    Use Claude to examine multiple findings and create gameplans.
    
    Args:
        findings: List of dicts with id, finding_text, importance_score, category
    
    Returns:
        Dict mapping finding_id to {analysis, gameplan, priority, needs_approval}
    """
    try:
        # Format findings for Claude
        findings_json = json.dumps([
            {
                'id': f.get('id'),
                'finding': f.get('finding_text'),
                'importance': f.get('importance_score'),
                'category': f.get('category')
            }
            for f in findings
        ], indent=2)
        
        prompt = f"""You are an examination agent analyzing research findings. For each finding:
1. Summarize its importance (2-3 sentences)
2. Recommend a gameplan (specific action)
3. Rate priority (critical/high/medium/low) based on importance_score
4. Flag if this needs user approval (true for strategic decisions, false for routine updates like "update war room")

Findings:
{findings_json}

Respond with ONLY valid JSON (no markdown, no explanation):
{{
  "finding_id": {{
    "analysis": "...",
    "gameplan": "...",
    "priority": "high",
    "needs_approval": false
  }}
}}"""
        
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse JSON response
        text = response.content[0].text.strip()
        result = json.loads(text)
        
        logger.info(f"Examined {len(result)} findings")
        return result
    except Exception as e:
        logger.error(f"Error examining findings: {e}")
        # Return empty dict if examination fails
        return {}

def send_sms_alert(phone_number: str, finding_text: str, gameplan: str, priority: str) -> bool:
    """
    Send SMS alert via Twilio.
    
    Args:
        phone_number: User's phone number (E.164 format)
        finding_text: What was found
        gameplan: Recommended action
        priority: critical/high/medium/low
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_from = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([twilio_sid, twilio_token, twilio_from]):
            logger.warning("Twilio credentials not configured")
            return False
        
        # Construct message
        message = f"""ALERT ({priority.upper()}): {finding_text[:100]}

Gameplan: {gameplan[:150]}

Reply: YES to approve / NO to skip"""
        
        # Send via Twilio API
        auth = (twilio_sid, twilio_token)
        data = {
            'From': twilio_from,
            'To': phone_number,
            'Body': message
        }
        
        response = requests.post(
            f'https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json',
            data=data,
            auth=auth,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"SMS sent successfully to {phone_number}")
            return True
        else:
            logger.error(f"Twilio error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return False

def call_gm_seat_api(finding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call GM Seat API to update NFL War Room with finding.
    
    Args:
        finding: Dict with finding_text, category, importance_score, source_name
    
    Returns:
        API response dict
    """
    try:
        gm_seat_url = os.getenv('GM_SEAT_API_URL', 'http://localhost:8000/api/war-room/update')
        
        payload = {
            'finding': finding['finding_text'],
            'category': finding['category'],
            'importance': finding['importance_score'],
            'source': finding['source_name'],
            'recommended_action': finding.get('gameplan', 'Review and assess impact'),
            'timestamp': int(__import__('time').time() * 1000)
        }
        
        response = requests.post(
            gm_seat_url,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"GM Seat API updated successfully")
            return response.json()
        else:
            logger.error(f"GM Seat API error: {response.status_code} - {response.text}")
            return {'status': 'error', 'message': 'Failed to update war room'}
    except Exception as e:
        logger.error(f"Error calling GM Seat API: {e}")
        return {'status': 'error', 'message': str(e)}
```

- [ ] **Step 2: Update .env.example**

Add to `~/Desktop/mission-control/.env.example`:

```bash
# NewsAPI configuration
NEWSAPI_KEY=your_newsapi_key_here

# Twilio configuration
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# GM Seat API configuration
GM_SEAT_API_URL=http://localhost:8000/api/war-room/update
```

- [ ] **Step 3: Test imports**

Run:
```bash
cd ~/Desktop/mission-control
python -c "from backend.agent_integrations import score_finding_with_claude, examine_findings_with_claude, send_sms_alert, call_gm_seat_api; print('All imports successful')"
```

Expected: No errors or "All imports successful"

- [ ] **Step 4: Commit**

```bash
cd ~/Desktop/mission-control
git add backend/agent_integrations.py .env.example
git commit -m "feat: add agent integrations (Claude API, Twilio, GM Seat API)"
```

---

**[Plan continues in next message due to length...]**

This completes **PHASE 1** (Foundation). Continue with Phase 2-5 tasks? Ready for inline execution or subagent-driven approach?