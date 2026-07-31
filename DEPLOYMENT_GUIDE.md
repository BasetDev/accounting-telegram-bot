# Hesab Telegram Bot — Deployment Guide

**Target Server:** 256MB RAM · 0.25 CPU · 1GB Disk
**Bot:** Hesab Accounting Bot v1.0.0 (Aiogram 3 + MongoDB Atlas)
**Entry Point:** `hesab/main.py` (long-polling mode)

---

## Section 1: Server Preparation & Security Optimization

Connect to your server via SSH, then run every command below in order.

### 1.1 — Create Swap File (Critical for 256MB RAM)

Without swap, `pip install` will trigger an OOM kill. This creates a 256MB swap file — safe for a 1GB disk.

```bash
# Check if swap already exists
swapon --show

# If NO swap is shown, create one:
sudo fallocate -l 256M /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Persist swap across reboots
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Tune kernel to prefer RAM over swap (reduces disk thrashing)
sudo sysctl vm.swappiness=10
sudo sysctl vm.vfs_cache_pressure=50
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf

# Verify
free -m
```

Expected output should show ~256MB under `Swap`.

### 1.2 — Install Minimum OS Prerequisites

```bash
# Update package lists (quiet mode to save RAM)
sudo apt-get update -qq

# Install ONLY what the bot needs
sudo apt-get install -y -qq python3 python3-venv python3-pip nodejs npm

# Verify installations
python3 --version
node --version
```

### 1.3 — Install PM2 (Process Manager)

```bash
# Install PM2 globally (no optional deps to save disk)
sudo npm install -g pm2 --no-optional

# Verify
pm2 --version
```

### 1.4 — Create Application Directory

```bash
# Create the deployment directory and subdirectories
sudo mkdir -p /home/hesab/app/{logs,backups,exports,uploads}

# Set ownership to your current user
sudo chown -R $(whoami):$(whoami) /home/hesab/app
```

---

## Section 2: Project Transfer & Secure Configuration

### 2.1 — Transfer Project Files to Server

Run this from your **LOCAL machine** (not the server). Replace `YOUR_SERVER_IP` and `YOUR_USER`.

```bash
# From your local machine — rsync the project (excludes venv, .git, logs, caches)
rsync -avz --progress \
  --exclude='venv/' \
  --exclude='.git/' \
  --exclude='__pycache__/' \
  --exclude='logs/*.log' \
  --exclude='backups/*.zip' \
  --exclude='exports/*.xlsx' \
  --exclude='exports/*.pdf' \
  --exclude='uploads/*' \
  --exclude='.env' \
  ./  YOUR_USER@YOUR_SERVER_IP:/home/hesab/app/
```

**Alternative — using `scp` if rsync is unavailable:**

```bash
# Create a clean archive locally
tar czf hesab-bot.tar.gz \
  --exclude='venv' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='logs/*.log' \
  --exclude='.env' \
  .

# Upload
scp hesab-bot.tar.gz YOUR_USER@YOUR_SERVER_IP:/home/hesab/app/

# On the server — extract
cd /home/hesab/app
tar xzf hesab-bot.tar.gz
rm hesab-bot.tar.gz
```

### 2.2 — Create and Secure the `.env` File

On the **server**, create the `.env` file with your credentials:

```bash
cd /home/hesab/app
nano .env
```

Paste the following content, replacing the placeholders with your real values:

```env
# Telegram Bot Configuration
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

# Admin Configuration
ADMIN_ID=YOUR_TELEGRAM_USER_ID
ADMIN_USERNAME=YOUR_ADMIN_USERNAME

# Database Configuration (MongoDB Atlas — do NOT run local MongoDB on 256MB RAM)
MONGO_URI=YOUR_MONGODB_ATLAS_CONNECTION_STRING
MONGO_DB_NAME=hesab

# Application Settings
APP_NAME=Hesab Accounting Bot
APP_VERSION=1.0.0
TIMEZONE=Asia/Tehran
LANGUAGE=fa

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/hesab.log

# Backup
BACKUP_DIR=backups/

# Export
EXPORT_DIR=exports/

# Upload
UPLOAD_DIR=uploads/
```

Save and exit: `Ctrl+O` → `Enter` → `Ctrl+X`.

### 2.3 — Lock Down `.env` Permissions

This is **critical** — prevents any other system user from reading your secrets.

```bash
chmod 600 .env
ls -la .env
```

Expected output: `-rw------- 1 youruser youruser ... .env`

---

## Section 3: Ultra-Lightweight Environment Setup

### 3.1 — Create Python Virtual Environment

```bash
cd /home/hesab/app

# Create venv (no pip cache, saves disk)
python3 -m venv venv

# Activate it
source venv/bin/activate
```

### 3.2 — Install Dependencies Without OOM or Disk Fill

This is the most RAM-intensive step. These flags are critical for a 256MB server:

```bash
cd /home/hesab/app
source venv/bin/activate

# Upgrade pip first (quiet mode)
pip install --no-cache-dir --quiet --upgrade pip

# Install all dependencies — no cache, quiet mode, saves ~50MB disk and ~100MB RAM
pip install --no-cache-dir --quiet -r requirements.txt
```

**What each flag does:**
- `--no-cache-dir` — does NOT store downloaded wheels in `~/.cache/pip`. Saves ~50MB disk and prevents RAM spikes.
- `--quiet` — suppresses verbose output, reducing memory usage during install.

### 3.3 — Verify Installation

```bash
cd /home/hesab/app
source venv/bin/activate

# Quick import test — loads the bot's config without starting Telegram polling
python3 -c "
import sys
sys.path.insert(0, '.')
from app.config import settings
print(f'BOT_TOKEN configured: {settings.is_valid}')
print(f'MONGO_URI configured: {settings.is_db_configured}')
print(f'Timezone: {settings.TIMEZONE}')
print('All imports OK')
"
```

Expected output:
```
BOT_TOKEN configured: True
MONGO_URI configured: True
Timezone: Asia/Tehran
All imports OK
```

---

## Section 4: PM2 Deployment & Hardening

### 4.1 — Verify `ecosystem.config.js`

The file is already included in the project at `/home/hesab/app/ecosystem.config.js`. Verify it exists and is correct:

```bash
cat /home/hesab/app/ecosystem.config.js
```

Expected content (already optimized for 256MB):

```javascript
module.exports = {
  apps: [
    {
      name: "hesab-bot",
      cwd: "/home/hesab/app",
      script: "hesab/main.py",
      interpreter: "/home/hesab/app/venv/bin/python",
      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONDONTWRITEBYTECODE: "1",
      },
      // Restart policy — conservative for micro-server
      restart_delay: 8000,
      max_restarts: 15,
      min_uptime: "15s",
      exp_backoff_restart_delay: 500,
      // CRITICAL: 150M limit — OS+PM2 use ~80MB, leaving headroom on 256MB server
      max_memory_restart: "150M",
      // Log configuration
      error_file: "/home/hesab/app/logs/pm2-error.log",
      out_file: "/home/hesab/app/logs/pm2-out.log",
      merge_logs: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      // Graceful shutdown — shorter for micro-server
      kill_timeout: 15000,
      listen_timeout: 10000,
      shutdown_with_message: false,
      // Watch (disabled for production)
      watch: false,
      // PM2's own memory limit
      node_args: ["--max-old-space-size=30"],
      // Reduce PM2 overhead
      vizion: false,
      autorestart: true,
    },
  ],
};
```

**Key settings explained:**

| Setting | Value | Why |
|---|---|---|
| `max_memory_restart` | `150M` | Bot restarts at 150MB. OS+PM2 use ~80MB. Total stays under 256MB. |
| `node_args` | `--max-old-space-size=30` | PM2's own Node.js heap is capped at 30MB. |
| `restart_delay` | `8000` | 8-second delay between restarts prevents CPU spikes. |
| `exp_backoff_restart_delay` | `500` | Exponential backoff: 500ms, 1s, 2s, 4s... |
| `vizion` | `false` | Disables git metadata polling (saves CPU + disk). |
| `watch` | `false` | No file watching (saves CPU on micro-server). |
| `kill_timeout` | `15000` | 15s for graceful MongoDB disconnect on stop. |

### 4.2 — Start the Bot with PM2

```bash
cd /home/hesab/app

# Start the bot
pm2 start ecosystem.config.js

# Wait 10 seconds for MongoDB connection + Telegram registration
sleep 10

# Check status
pm2 status
```

Expected output should show `status: online` with a valid PID.

### 4.3 — Verify Bot Startup in Logs

```bash
# View last 15 log lines
pm2 logs hesab-bot --nostream --lines 15
```

You should see:
```
INFO: Connected to MongoDB Atlas: hesab
INFO: Database indexes created successfully.
INFO: MongoDB database initialized.
INFO: Bot commands registered.
INFO: Hesab Accounting Bot v1.0.0 started!
```

If you see errors, check that `.env` values are correct.

### 4.4 — Save PM2 Process List (Survives Reboot)

```bash
# Save current PM2 process list
pm2 save

# Generate startup script for auto-restart on reboot
pm2 startup
```

PM2 will output a command like `sudo env PATH=$PATH:/usr/bin pm2 startup ...`. **Copy and run that exact command.**

### 4.5 — Monitor the Bot

```bash
# Live logs (Ctrl+C to exit)
pm2 logs hesab-bot

# Memory and CPU monitor (press 'q' to exit)
pm2 monit

# Quick status check
pm2 status
```

### 4.6 — Common PM2 Commands Reference

```bash
# Restart the bot
pm2 restart hesab-bot

# Stop the bot
pm2 stop hesab-bot

# Delete from PM2 (does NOT delete code)
pm2 delete hesab-bot

# View detailed process info
pm2 describe hesab-bot

# Flush logs
pm2 flush hesab-bot
```

---

## Quick Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: aiofiles` | aiogram dependency missing | `source venv/bin/activate && pip install --no-cache-dir aiofiles` |
| Bot status is `errored` | Crash loop | `pm2 logs hesab-bot --lines 20` to see the error |
| `MongoDB connection failed` | Wrong `MONGO_URI` in `.env` | Verify your Atlas connection string |
| `BOT_TOKEN is not configured` | Missing or wrong token | Edit `.env` and set correct `BOT_TOKEN` |
| OOM kill in `dmesg` | Bot exceeded 256MB | PM2 should auto-restart at 150M. Check with `pm2 status` |
| Disk full | Logs or exports filling disk | `pm2 flush hesab-bot && rm -f exports/*.xlsx exports/*.pdf` |

---

## Security Checklist

- [ ] `.env` file permissions set to `600` (`chmod 600 .env`)
- [ ] `.env` is NOT in git (`echo '.env' >> .gitignore`)
- [ ] MongoDB Atlas uses a strong password and IP whitelist
- [ ] Server SSH uses key-based authentication (disable password auth)
- [ ] Firewall allows only SSH (port 22) — bot uses outbound connections only
- [ ] PM2 runs as a non-root user (never run as `root`)

---

## Disk Space Budget (1GB Total)

| Component | Size |
|---|---|
| OS + packages | ~400MB |
| Node.js + PM2 | ~60MB |
| Python venv | ~100MB |
| Bot code | ~2MB |
| Swap file | 256MB |
| **Total used** | **~818MB** |
| **Free** | **~182MB** |

Monitor disk usage: `df -h /`
