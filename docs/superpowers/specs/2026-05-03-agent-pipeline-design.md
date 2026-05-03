# Agent Pipeline System Design

**Date:** 2026-05-03  
**Project:** Mission Control - Autonomous Agent Research & Execution Pipeline  
**Status:** Approved for implementation  

## Executive Summary

Build a cost-conscious autonomous agent system with 4 specialized R&D agents (Sports, Finance, Creative, Tech) that continuously research their domains, feed findings into an Examination agent for analysis, and trigger an Executioner agent to either take autonomous action (update NFL War Room) or alert you via SMS for high-value decisions requiring human judgment.

**Key constraints:**
- Minimize costs (target: ~$5-15/month)
- Use free data sources and APIs
- 1-10 scoring based on business impact, urgency, cost
- MVP: Only autonomous action is NFL War Room updates via GM Seat API

---

## System Architecture

### High-Level Flow

```
[4 R&D Agents] → [research_findings table]
                        ↓
            [Examination Agent] → [examinations table]
                        ↓
             [Executioner Agent]
                    ↙          ↘
            [Autonomous]    [Alert You]
            (update War    (SMS via
            Room API)      Twilio)
```

### Core Agents

**R&D Agents (4 parallel, independent loops):**
- **Sports Agent:** NewsAPI (sports), ESPN RSS, Reddit r/nfl → Finding: injuries, trades, rule changes
- **Finance Agent:** Yahoo Finance API, NewsAPI (business), MarketWatch RSS → Finding: market movements, earnings, economic data
- **Creative Agent:** NewsAPI (entertainment), Reddit r/design, Twitter trends → Finding: design trends, cultural shifts
- **Tech Agent:** Hacker News API, GitHub trending, Reddit r/programming, NewsAPI (tech) → Finding: security vulnerabilities, new tools, breakthroughs

**Examination Agent:**
- Batches pending findings every 15 minutes
- Uses Claude to analyze each: "What's the importance (1-10)? What should we do?"
- Outputs: priority level, gameplan, approval flag

**Executioner Agent:**
- Queries pending examinations every 5 minutes
- **Autonomous actions** (requires_approval = false):
  - Call GM Seat API to update NFL War Room
  - Log action to database
- **Alert actions** (requires_approval = true):
  - Send SMS via Twilio with finding + recommended action
  - Wait for user Y/N response
  - Execute or archive based on reply

---

## Database Schema

Add three new tables to Mission Control SQLite:

### `research_findings`

```sql
CREATE TABLE IF NOT EXISTS research_findings (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name        TEXT NOT NULL,  -- 'sports' | 'finance' | 'creative' | 'tech'
    finding_text      TEXT NOT NULL,
    source_url        TEXT,
    source_name       TEXT,           -- 'ESPN', 'Yahoo Finance', 'Hacker News', etc.
    importance_score  INTEGER,        -- 1-10, set by Claude
    category          TEXT,           -- 'injury', 'market_movement', 'security_vuln', etc.
    status            TEXT DEFAULT 'pending_examination',  -- pending_examination | examined | actioned | archived
    created_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
    updated_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
)

CREATE INDEX idx_research_findings_status ON research_findings(status)
CREATE INDEX idx_research_findings_agent ON research_findings(agent_name)
CREATE INDEX idx_research_findings_created ON research_findings(created_at DESC)
```

### `examinations`

```sql
CREATE TABLE IF NOT EXISTS examinations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id        INTEGER NOT NULL,
    claude_analysis   TEXT NOT NULL,  -- What Claude concluded about importance
    gameplan          TEXT NOT NULL,  -- Recommended action
    priority          TEXT,           -- 'critical' | 'high' | 'medium' | 'low'
    requires_approval INTEGER DEFAULT 0,  -- 0 = autonomous, 1 = needs user approval
    status            TEXT DEFAULT 'pending_action',  -- pending_action | approved | rejected | executed | archived
    created_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
    updated_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
    
    FOREIGN KEY (finding_id) REFERENCES research_findings(id)
)

CREATE INDEX idx_examinations_status ON examinations(status)
CREATE INDEX idx_examinations_finding ON examinations(finding_id)
```

### `actions`

```sql
CREATE TABLE IF NOT EXISTS actions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    examination_id    INTEGER NOT NULL,
    action_type       TEXT NOT NULL,  -- 'autonomous' | 'alert_user'
    action_description TEXT,
    result            TEXT,           -- What happened (success, failed, approved, rejected, pending)
    result_detail     TEXT,           -- Additional detail (API response, error, etc.)
    created_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
    executed_at       INTEGER,        -- When action was completed
    
    FOREIGN KEY (examination_id) REFERENCES examinations(id)
)

CREATE INDEX idx_actions_status ON actions(action_type)
CREATE INDEX idx_actions_examination ON actions(examination_id)
```

---

## Agent Implementation Details

### R&D Agent Loop (runs every 30-60 minutes per agent)

```python
while True:
    # 1. Query free data sources
    findings = query_data_source(agent_name)  # Returns list of new items
    
    # 2. For each finding, ask Claude to score it
    for item in findings:
        score = claude_score(item, agent_name)  # Returns 1-10
        
        # 3. Write to database
        insert_research_finding(
            agent_name=agent_name,
            finding_text=item.summary,
            source_url=item.url,
            importance_score=score,
            category=infer_category(item)
        )
    
    # 4. Sleep (cost-conscious)
    sleep(30-60 minutes)
```

**Scoring prompt to Claude:**
```
You are a research agent evaluating business findings. Score this finding 1-10 based on:
- Business impact: Will this affect decisions/strategy?
- Urgency: How time-sensitive is this?
- Cost: Does this affect revenue/spending?

Finding: [finding_text]
Agent: [sports|finance|creative|tech]

Respond with ONLY a number 1-10 and brief reasoning.
```

### Examination Agent Loop (runs every 15 minutes)

```python
while True:
    # 1. Get all pending findings
    pending = query_findings(status='pending_examination')
    
    # 2. Batch to Claude for analysis
    analysis = claude_examine(pending)  # Returns structured gameplan + approval flag
    
    # 3. Write examinations to database
    for finding_id, result in analysis.items():
        insert_examination(
            finding_id=finding_id,
            claude_analysis=result['analysis'],
            gameplan=result['gameplan'],
            priority=result['priority'],
            requires_approval=result['needs_approval']
        )
    
    sleep(15 minutes)
```

**Examination prompt to Claude:**
```
You are an examination agent analyzing research findings. For each finding:
1. Summarize its importance
2. Recommend a gameplan (specific action)
3. Rate priority (critical/high/medium/low) based on importance_score
4. Flag if this needs user approval (true/false) - approve if it's autonomous action (update War Room) with high confidence, flag otherwise

Findings:
[JSON array of findings with importance_score, category, finding_text]

Respond with JSON:
{
  "finding_id": {
    "analysis": "...",
    "gameplan": "...",
    "priority": "high",
    "needs_approval": false
  }
}
```

### Executioner Agent Loop (runs every 5 minutes)

```python
while True:
    # 1. Get pending examinations
    pending = query_examinations(status='pending_action')
    
    for exam in pending:
        if exam.requires_approval:
            # Alert user via SMS
            send_sms(
                message=f"ALERT ({exam.priority}): {exam.finding_text}\n\n"
                        f"Gameplan: {exam.gameplan}\n\n"
                        f"Reply YES to approve, NO to skip."
            )
            # Wait for user reply (handled async)
        else:
            # Autonomous action - only for War Room updates in MVP
            if exam.gameplan.contains("update war room"):
                try:
                    response = gm_seat_api.update_war_room(
                        finding=exam.finding_text,
                        category=exam.category,
                        importance=exam.importance_score,
                        source=exam.source_name
                    )
                    log_action(
                        examination_id=exam.id,
                        action_type='autonomous',
                        result='success',
                        result_detail=response
                    )
                except Exception as e:
                    log_action(
                        examination_id=exam.id,
                        action_type='autonomous',
                        result='failed',
                        result_detail=str(e)
                    )
    
    sleep(5 minutes)
```

---

## Data Sources (Free Tier)

| Agent | Source | Free Tier | Rate Limit |
|-------|--------|-----------|-----------|
| Sports | NewsAPI (sports category) | 100 req/day | Yes |
| Sports | ESPN RSS | Unlimited | No |
| Sports | Reddit r/nfl | Unlimited | Soft (respect robots.txt) |
| Finance | Yahoo Finance API | Unlimited | Yes |
| Finance | NewsAPI (business) | 100 req/day | Yes |
| Finance | MarketWatch RSS | Unlimited | No |
| Creative | NewsAPI (entertainment) | 100 req/day | Yes |
| Creative | Reddit r/design | Unlimited | Soft |
| Creative | Twitter API (free tier) | Limited | Yes |
| Tech | Hacker News API | Unlimited | Yes |
| Tech | GitHub API (free tier) | 60 req/hour | Yes |
| Tech | Reddit r/programming | Unlimited | Soft |
| Tech | NewsAPI (tech) | 100 req/day | Yes |

**Total cost for data sources: $0/month**

---

## SMS Alerts (Twilio)

**Free tier:** 1 SMS/day trial  
**After trial:** ~$0.0075 per SMS  
**Expected volume:** 3-5 actionable alerts/day  
**Monthly cost estimate:** $5-10/month

**SMS format:**
```
ALERT (HIGH): Player X injured for season

Gameplan: Re-evaluate KC roster projections and adjust War Room recommendations

Reply: YES to approve / NO to skip
```

---

## GM Seat API Integration

**Prerequisite:** GM Seat API must be built/updated first to accept findings.

**Executioner calls:**
```
POST /api/war-room/update
Content-Type: application/json

{
  "finding": "Patrick Mahomes reported ankle injury",
  "category": "injury",
  "importance": 8,
  "source": "ESPN",
  "recommended_action": "Re-evaluate KC playoff chances",
  "timestamp": 1746345600000
}
```

**Response:**
```
{
  "status": "success",
  "message": "War room updated",
  "updated_fields": ["injury_report", "playoff_projection"]
}
```

---

## Mission Control Dashboard Integration

**New panel: "Agent Pipeline"**

Displays:
- **Live findings feed** (all agents, color-coded by importance 1-10)
- **Pending examinations** (count + oldest waiting)
- **Pending decisions** (alerts waiting for your Y/N)
- **Recent actions** (what executioner did in last 24h)
- **Agent status** (idle/researching/analyzing, last finding per agent)
- **Cost summary** (tokens used, SMS sent, API calls made)

---

## Pixel Office Visualization

**4 R&D Agents** (at research desks):
- Display name + domain (Sports, Finance, Creative, Tech)
- Status: Idle / Researching / Found something
- Latest finding in speech bubble
- Importance score as visual indicator (color intensity)

**Examination Agent** (at analysis desk):
- Status: Idle / Analyzing
- Shows "X findings pending review"
- Visual papers stacking as findings await analysis

**Executioner Agent** (at action desk):
- Status: Idle / Executing / Awaiting approval
- Shows current action or alert pending
- Visual indicator for SMS sent ("📱 waiting for reply")

**Data flow arrows:** Finding → Examination → Decision → Action

---

## Scoring Examples

### Sports
- "Star RB injured" → 8 (high impact on War Room strategy)
- "Trade rumors" → 5 (useful context, lower urgency)
- "Rule change proposed" → 7 (affects strategy planning)

### Finance
- "Fed announces rate cut" → 9 (major business impact)
- "Tech stock crashes 15%" → 8 (significant market movement)
- "Earnings report released" → 6 (informational, known event)

### Creative
- "New design tool trending" → 4 (nice-to-know, low urgency)
- "Design award winner announced" → 5 (potentially relevant)

### Tech
- "Critical security patch for widely-used library" → 9 (urgent)
- "New JavaScript framework released" → 3 (informational)
- "Zero-day vulnerability disclosed" → 10 (highest priority)

---

## Cost Summary (Monthly)

| Item | Cost |
|------|------|
| Data sources | $0 |
| Twilio SMS (5/day avg) | $5-10 |
| Claude API (agent analysis) | ~$5-10 |
| Infrastructure (local/free) | $0 |
| **TOTAL** | **~$10-20/month** |

---

## Implementation Phases

**Phase 0 (Prerequisite):**
- Design & build GM Seat API (separate design)

**Phase 1 (Foundation):**
- Add 3 new tables to Mission Control DB
- Implement all 4 R&D agents (Sports, Finance, Creative, Tech)
- Test data source querying and scoring

**Phase 2 (Intelligence):**
- Implement Examination agent
- Test Claude analysis + gameplan generation
- Verify database writes

**Phase 3 (Action):**
- Implement Executioner agent
- Build GM Seat API integration
- Integrate Twilio SMS
- Test autonomous actions and alerts

**Phase 4 (Visibility):**
- Add "Agent Pipeline" panel to Mission Control dashboard
- Display findings, examinations, actions in real-time
- Add cost tracking

**Phase 5 (Visualization):**
- Build pixel office visualization
- Animate agents based on status
- Show data flow visually

---

## Testing Strategy

- **Unit tests:** Each agent loop in isolation
- **Integration tests:** End-to-end flow (finding → examination → action)
- **Manual tests:** Run agents for 1 week, verify:
  - Findings are meaningful and scored correctly
  - Examinations produce actionable gameplans
  - War Room updates work via executioner
  - SMS alerts are timely and accurate
  - Mission Control dashboard displays data correctly

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| API rate limits exceeded | Batch requests, cache results, respect rate limits |
| Claude scoring inconsistent | Provide clear scoring rubric, validate against human judgment |
| False alerts (SMS spam) | Set high threshold for requires_approval, test extensively |
| GM Seat API down | Graceful error handling, queue actions for retry |
| Cost overruns | Monitor token usage daily, adjust loop intervals if needed |

---

## Success Criteria

✅ All 4 R&D agents running and finding meaningful data  
✅ Examination agent accurately prioritizes findings  
✅ Executioner successfully updates NFL War Room  
✅ SMS alerts work and you can reply to approve/reject  
✅ Mission Control dashboard shows full pipeline  
✅ Monthly cost stays under $20  
✅ Zero false positives (wasteful alerts)  

---

## Next Steps

1. User reviews this spec and approves
2. Invoke writing-plans skill to create detailed implementation plan
3. Build GM Seat API (Phase 0)
4. Implement agent system (Phases 1-5)
