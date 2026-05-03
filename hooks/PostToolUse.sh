#!/usr/bin/env bash
set +e

DB="$HOME/Desktop/mission-control/backend/mission_control.db"
NOW=$(($(date +%s) * 1000))

python3 << 'PYEOF' "$DB" "$NOW"
import sys
import json
import sqlite3

db = sys.argv[1]
now = int(sys.argv[2])

try:
    raw = sys.stdin.read()
    d = json.loads(raw)
except:
    sys.exit(0)

session_id = d.get('session_id', '')
usage = d.get('usage', {})
model = d.get('model', '')
message_id = d.get('message_id', '')

if not session_id:
    sys.exit(0)

try:
    conn = sqlite3.connect(db, timeout=10)
    conn.execute('PRAGMA journal_mode=WAL')

    if usage:
        conn.execute('''
            INSERT INTO token_usage(session_id, message_id, model,
                input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens, created_at)
            VALUES(?,?,?,?,?,?,?,?)
        ''', (
            session_id, message_id, model,
            usage.get('input_tokens', 0),
            usage.get('output_tokens', 0),
            usage.get('cache_read_input_tokens', 0),
            usage.get('cache_creation_input_tokens', 0),
            now
        ))

    conn.commit()
    conn.close()
except:
    pass

sys.exit(0)
PYEOF

exit 0
