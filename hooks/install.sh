#!/usr/bin/env bash
set -e

echo "Installing Mission Control hooks..."

# Create hooks directory
mkdir -p ~/.claude/hooks

# Copy hook scripts
cp PreToolUse.sh ~/.claude/hooks/PreToolUse
cp PostToolUse.sh ~/.claude/hooks/PostToolUse
cp Stop.sh ~/.claude/hooks/Stop
cp Notification.sh ~/.claude/hooks/Notification

# Make executable
chmod +x ~/.claude/hooks/PreToolUse
chmod +x ~/.claude/hooks/PostToolUse
chmod +x ~/.claude/hooks/Stop
chmod +x ~/.claude/hooks/Notification

echo "✓ Hook scripts installed to ~/.claude/hooks/"

# Merge hook config into settings.json
python3 << 'PYEOF'
import json
from pathlib import Path

settings_path = Path.home() / '.claude' / 'settings.json'
settings = {}

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text())
    except:
        pass

# Add hooks config
settings['hooks'] = {
    "PreToolUse": [{"matcher": "", "hooks": [{"type": "command", "command": "~/.claude/hooks/PreToolUse"}]}],
    "PostToolUse": [{"matcher": "", "hooks": [{"type": "command", "command": "~/.claude/hooks/PostToolUse"}]}],
    "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "~/.claude/hooks/Stop"}]}],
    "Notification": [{"matcher": "", "hooks": [{"type": "command", "command": "~/.claude/hooks/Notification"}]}]
}

settings_path.write_text(json.dumps(settings, indent=2))
print("✓ Hooks registered in ~/.claude/settings.json")
PYEOF

echo "✓ Mission Control hooks installed successfully!"
echo ""
echo "Next: Start the backend with:"
echo "  cd ~/Desktop/mission-control/backend && ./start.sh"
echo ""
echo "Then open a new Claude Code session and run a tool to verify hooks are working."
