#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOGS_DIR"

# Activate venv if present
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

cd "$PROJECT_DIR"
nohup python hesab/main.py >> "$LOGS_DIR/bot.log" 2>&1 &
BOT_PID=$!
echo "$BOT_PID" > "$LOGS_DIR/bot.pid"
echo "Bot started with PID: $BOT_PID"
