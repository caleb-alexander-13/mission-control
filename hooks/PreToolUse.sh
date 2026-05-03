#!/usr/bin/env bash
set +e

DB="$HOME/Desktop/mission-control/backend/mission_control.db"
INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)
NOW=$(($(date +%s) * 1000))
CWD=$(pwd 2>/dev/null || echo "")

[ -z "$SESSION_ID" ] && exit 0

# Upsert session
sqlite3 "$DB" "INSERT OR IGNORE INTO sessions(session_id, project, started_at) VALUES('$SESSION_ID', '$CWD', $NOW);" 2>/dev/null

# Log PreToolUse event
TOOL_INPUT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('tool_input',{})))" 2>/dev/null | sed "s/'/''/g")
sqlite3 "$DB" "INSERT INTO tool_events(session_id, event_type, tool_name, tool_input_json, created_at) VALUES('$SESSION_ID', 'PreToolUse', '$TOOL_NAME', '$TOOL_INPUT', $NOW);" 2>/dev/null

# Extract file_path for Read/Write/Edit
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    inp = d.get('tool_input', {})
    tool = d.get('tool_name', '')
    if tool in ('Read', 'Write', 'Edit'):
        print(inp.get('file_path', inp.get('path', '')))
except:
    pass
" 2>/dev/null)

if [ -n "$FILE_PATH" ]; then
    EVENT_TYPE="read"
    [ "$TOOL_NAME" = "Write" ] && EVENT_TYPE="write"
    [ "$TOOL_NAME" = "Edit" ] && EVENT_TYPE="edit"
    FILE_PATH=$(echo "$FILE_PATH" | sed "s/'/''/g")
    sqlite3 "$DB" "INSERT INTO file_events(session_id, file_path, event_type, created_at) VALUES('$SESSION_ID', '$FILE_PATH', '$EVENT_TYPE', $NOW);" 2>/dev/null
fi

exit 0
