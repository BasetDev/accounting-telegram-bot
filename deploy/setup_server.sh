#!/bin/bash
# ============================================================
# Micro-Server Setup Script for Hesab Telegram Bot
# Target: 256MB RAM, 0.25 CPU, 1GB Disk
# Run ONCE on the target server via SSH
# ============================================================
set -euo pipefail

APP_DIR="/home/hesab/app"
SWAP_FILE="/swapfile"
SWAP_SIZE="256M"

echo "=========================================="
echo " Hesab Bot - Micro-Server Setup"
echo "=========================================="

# ---- Step 1: System Update (minimal) ----
echo "[1/7] Updating package lists..."
apt-get update -qq > /dev/null 2>&1 || { echo "WARN: apt update failed, continuing..."; }

# ---- Step 2: Create Swap (CRITICAL for 256MB RAM) ----
echo "[2/7] Checking swap space..."
if [ "$(swapon --show | wc -l)" -eq 0 ] && [ ! -f "$SWAP_FILE" ]; then
    echo "  No swap detected. Creating ${SWAP_SIZE} swap file..."
    fallocate -l "$SWAP_SIZE" "$SWAP_FILE" 2>/dev/null || dd if=/dev/zero of="$SWAP_FILE" bs=1M count=256 status=progress
    chmod 600 "$SWAP_FILE"
    mkswap "$SWAP_FILE" > /dev/null
    swapon "$SWAP_FILE"
    # Persist across reboots
    if ! grep -q "$SWAP_FILE" /etc/fstab; then
        echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab
    fi
    echo "  Swap created: $(swapon --show | grep swap | awk '{print $3}')"
else
    echo "  Swap already active."
fi

# ---- Step 3: Install System Dependencies ----
echo "[3/7] Installing system dependencies..."
apt-get install -y -qq python3 python3-venv python3-pip nodejs npm curl > /dev/null 2>&1 || {
    echo "  Trying alternative package names..."
    apt-get install -y -qq python3.11 python3.11-venv python3-pip nodejs npm curl > /dev/null 2>&1 || true
}

# ---- Step 4: Install PM2 ----
echo "[4/7] Installing PM2..."
if ! command -v pm2 &> /dev/null; then
    npm install -g pm2 --no-optional 2>/dev/null || {
        echo "  npm install failed, trying with --force..."
        npm install -g pm2 --force 2>/dev/null
    }
fi
echo "  PM2: $(pm2 --version 2>/dev/null || echo 'installed')"

# ---- Step 5: Create App Directory ----
echo "[5/7] Creating application directory..."
mkdir -p "$APP_DIR"/{logs,backups,exports,uploads}
echo "  Created: $APP_DIR"

# ---- Step 6: Optimize OS for Low Memory ----
echo "[6/7] Applying low-memory OS optimizations..."
# Reduce swappiness (prefer keeping processes in RAM)
echo 10 > /proc/sys/vm/swappiness 2>/dev/null || true
# Reduce vfs_cache_pressure (reclaim inode/dentry cache less aggressively)
echo 50 > /proc/sys/vm/vfs_cache_pressure 2>/dev/null || true
# Persist
if ! grep -q "vm.swappiness" /etc/sysctl.conf; then
    echo "vm.swappiness=10" >> /etc/sysctl.conf
    echo "vm.vfs_cache_pressure=50" >> /etc/sysctl.conf
fi

# ---- Step 7: Verify ----
echo "[7/7] Verification..."
echo ""
echo "=========================================="
echo " Setup Complete!"
echo "=========================================="
echo " RAM:    $(free -m | awk '/Mem:/{print $2}')MB"
echo " Swap:   $(free -m | awk '/Swap:/{print $2}')MB"
echo " Disk:   $(df -h / | awk 'NR==2{print $4}') free"
echo " Python: $(python3 --version 2>&1)"
echo " Node:   $(node --version 2>&1)"
echo " PM2:    $(pm2 --version 2>&1)"
echo "=========================================="
echo ""
echo "Next: Run deploy.sh to deploy the bot code."
