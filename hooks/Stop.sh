#!/usr/bin/env bash
set +e

DB="$HOME/Desktop/mission-control/backend/mission_control.db"
INPUT=$(cat)
NOW=$(($(date +%s) * 1000))

SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null)

[ -z "$SESSION_ID" ] && exit 0

sqlite3 "$DB" "UPDATE sessions SET ended_at=$NOW, status='ended' WHERE session_id='$SESSION_ID';" 2>/dev/null

exit 0
