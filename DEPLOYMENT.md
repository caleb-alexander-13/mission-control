# Mission Control Deployment Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- Two terminal windows (one for backend, one for frontend)
- (Optional) Another terminal for NFL War Room

## Step 1: Set Environment Variables

Create `.env` file in `~/Desktop/mission-control/`:

```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxx

# NewsAPI (get free key from https://newsapi.org)
NEWSAPI_KEY=xxxxx

# Twilio (optional - for SMS alerts)
TWILIO_ACCOUNT_SID=ACxxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1234567890
USER_PHONE_NUMBER=+1234567890

# War Room API
GM_SEAT_API_URL=http://localhost:8000/api/war-room/update
```

## Step 2: Install Backend Dependencies

```bash
cd ~/Desktop/mission-control

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

## Step 3: Install Frontend Dependencies

```bash
cd ~/Desktop/mission-control/frontend
npm install
```

## Step 4: Initialize Database

```bash
cd ~/Desktop/mission-control/backend
python db_init.py
```

## Step 5: Start Services

### Terminal 1: NFL War Room (Port 8000)

```bash
cd ~/Desktop/NFL\ War\ Room
python -m uvicorn backend.app:app --reload --port 8000
```

Expected output:
```
Uvicorn running on http://127.0.0.1:8000
Press CTRL+C to quit
```

### Terminal 2: Mission Control Backend (Port 8001)

```bash
cd ~/Desktop/mission-control
source venv/bin/activate
python -m uvicorn backend.app:app --reload --port 8001
```

Expected output:
```
Uvicorn running on http://127.0.0.1:8001
Press CTRL+C to quit
```

You should see:
- ✅ Database tables created (research_findings, examinations, actions)
- ✅ Agents pipeline started
- ✅ All 6 agents initialized

### Terminal 3: Mission Control Frontend (Port 5173)

```bash
cd ~/Desktop/mission-control/frontend
npm run dev
```

Expected output:
```
  VITE v4.x.x ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

## Step 6: Verify Deployment

Open browser to **http://localhost:5173**

You should see:
- ✅ Mission Control dashboard loads
- ✅ Agent Pipeline section visible
- ✅ PixelOffice with 6 agents at desks
- ✅ All agents showing "Idle" status (green dots)
- ✅ Findings feed empty (agents running, no findings yet)
- ✅ Agent status panel showing all agents

## Step 7: Test Agent Loop

The agents automatically started when backend initialized. You should see findings appearing in 30-60 minutes as agents fetch data.

**To test immediately:**

```bash
# In a new terminal (with venv activated):
cd ~/Desktop/mission-control

python << 'PYTHON'
from agents.research.sports import SportsAgent
agent = SportsAgent()
agent.run_once()  # Manually trigger one iteration
PYTHON
```

Then check dashboard - you should see findings appear in the feed.

## Step 8: Monitor Agents

Watch the PixelOffice visualization:
- 🟢 Green dot = agent idle
- 🟡 Yellow pulsing dot = agent actively working
- Speech bubbles appear when finding important items

## Testing Checklist

- [ ] All 6 agents visible in PixelOffice
- [ ] Status indicators show (green for idle)
- [ ] Dashboard loads without errors
- [ ] API endpoints responding (check browser Network tab)
- [ ] Agents auto-refresh every 5 seconds in visualization
- [ ] Findings feed updates when agents run
- [ ] Examinations appear after findings are analyzed
- [ ] Executioner creates actions in log

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Missing Dependencies

```bash
pip install --upgrade anthropic requests feedparser
```

### Database Issues

```bash
rm backend/mission_control.db
python backend/db_init.py
```

### Frontend Build Issues

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## Next Steps

Once verified:
1. Check `/api/agent-pipeline/findings` endpoint
2. Wait for agents to fetch data (30-60 min)
3. Watch examinations generate gameplans
4. See executioner create actions
5. Approve/reject alerts via SMS or dashboard

Enjoy your autonomous agent system! 🚀
