#!/bin/bash

echo "🚀 Mission Control Quick Start"
echo "=============================="
echo ""

# Check for .env
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "Create .env with these variables:"
    echo ""
    cat << 'ENVFILE'
ANTHROPIC_API_KEY=sk-ant-xxxxx
NEWSAPI_KEY=xxxxx
TWILIO_ACCOUNT_SID=ACxxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1234567890
USER_PHONE_NUMBER=+1234567890
GM_SEAT_API_URL=http://localhost:8000/api/war-room/update
ENVFILE
    echo ""
    exit 1
fi

echo "✅ .env file found"

# Create virtual environment
echo ""
echo "📦 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r backend/requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
cd backend
python db_init.py
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo ""
echo "Terminal 1 (NFL War Room on :8000):"
echo "  cd ~/Desktop/NFL\\ War\\ Room"
echo "  python -m uvicorn backend.app:app --reload --port 8000"
echo ""
echo "Terminal 2 (Mission Control Backend on :8001):"
echo "  cd ~/Desktop/mission-control"
echo "  source venv/bin/activate"
echo "  python -m uvicorn backend.app:app --reload --port 8001"
echo ""
echo "Terminal 3 (Mission Control Frontend on :5173):"
echo "  cd ~/Desktop/mission-control/frontend"
echo "  npm install  # if not done yet"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""
