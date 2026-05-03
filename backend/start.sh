#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "Setting up Mission Control backend..."

# Create venv if it doesn't exist
if [ ! -d venv ]; then
    python3 -m venv venv
fi

# Activate and install
source venv/bin/activate
pip install -q -r requirements.txt

# Run
echo "Starting FastAPI server on http://localhost:8000"
echo ""
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
