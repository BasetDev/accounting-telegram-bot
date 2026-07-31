#!/bin/bash
# ============================================================
# Deploy Hesab Telegram Bot to Micro-Server
# Run from your LOCAL machine: bash deploy/deploy.sh <server_ip> <ssh_user>
# ============================================================
set -euo pipefail

SERVER="${1:?Usage: deploy.sh <server_ip> [ssh_user]}"
SSH_USER="${2:-root}"
APP_DIR="/home/hesab/app"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=========================================="
echo " Deploying Hesab Bot to ${SSH_USER}@${SERVER}"
echo "=========================================="

# ---- Step 1: Upload code ----
echo "[1/5] Uploading code..."
ssh "${SSH_USER}@${SERVER}" "mkdir -p ${APP_DIR}/{logs,backups,exports,uploads}"

rsync -avz --progress \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='node_modules/' \
    --exclude='logs/*.log' \
    --exclude='backups/*.zip' \
    --exclude='exports/*.xlsx' \
    --exclude='exports/*.pdf' \
    --exclude='uploads/*' \
    --exclude='.env' \
    --exclude='deploy/' \
    "${LOCAL_DIR}/" "${SSH_USER}@${SERVER}:${APP_DIR}/"

# ---- Step 2: Upload .env separately (secure) ----
echo "[2/5] Uploading .env..."
scp "${LOCAL_DIR}/.env" "${SSH_USER}@${SERVER}:${APP_DIR}/.env"

# ---- Step 3: Setup venv and install deps ----
echo "[3/5] Setting up Python venv (this may take 2-3 min on micro-server)..."
ssh "${SSH_USER}@${SERVER}" bash -s << 'REMOTE_SCRIPT'
set -e
APP_DIR="/home/hesab/app"
cd "$APP_DIR"

# Create venv if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  venv created."
fi

# Install deps with memory-saving flags
source venv/bin/activate
pip install --no-cache-dir --quiet --upgrade pip
pip install --no-cache-dir --quiet -r requirements.txt
echo "  Dependencies installed."

# Verify imports
python3 -c "
import sys
sys.path.insert(0, '.')
from app.config import settings
print(f'  Config loaded. BOT_TOKEN configured: {settings.is_valid}')
print(f'  DB configured: {settings.is_db_configured}')
"
REMOTE_SCRIPT

# ---- Step 4: Upload ecosystem config ----
echo "[4/5] Uploading PM2 config..."
scp "${LOCAL_DIR}/ecosystem.config.js" "${SSH_USER}@${SERVER}:${APP_DIR}/ecosystem.config.js"

# ---- Step 5: Start with PM2 ----
echo "[5/5] Starting bot with PM2..."
ssh "${SSH_USER}@${SERVER}" bash -s << 'REMOTE_START'
set -e
APP_DIR="/home/hesab/app"
cd "$APP_DIR"

# Stop existing process if running
pm2 delete hesab-bot 2>/dev/null || true

# Start fresh
pm2 start ecosystem.config.js
pm2 save

# Wait for startup
sleep 10

# Check status
pm2 status
echo ""
echo "--- Recent logs ---"
pm2 logs hesab-bot --nostream --lines 15 2>&1
REMOTE_START

echo ""
echo "=========================================="
echo " Deployment Complete!"
echo "=========================================="
echo " Monitor: ssh ${SSH_USER}@${SERVER} 'pm2 monit'"
echo " Logs:    ssh ${SSH_USER}@${SERVER} 'pm2 logs hesab-bot'"
echo " Status:  ssh ${SSH_USER}@${SERVER} 'pm2 status'"
echo "=========================================="
