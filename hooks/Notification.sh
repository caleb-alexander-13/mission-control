#!/usr/bin/env bash
set +e

DB="$HOME/Desktop/mission-control/backend/mission_control.db"
INPUT=$(cat)
NOW=$(($(date +%s) * 1000))
PROJECT=$(pwd 2>/dev/null || echo "")

SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null)
MSG=$(echo "$INPUT" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    msg = d.get('message', d.get('notification',''))
    print(msg[:200] if msg else '')
except:
    pass
" 2>/dev/null | sed "s/'/''/g")

[ -z "$SESSION_ID" ] || [ -z "$MSG" ] && exit 0

sqlite3 "$DB" "INSERT INTO tasks(session_id, title, status, project, created_at, updated_at) VALUES('$SESSION_ID', '$MSG', 'done', '$PROJECT', $NOW, $NOW);" 2>/dev/null

exit 0
