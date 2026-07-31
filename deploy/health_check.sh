#!/bin/bash
# ============================================================
# Health Check Script for Hesab Bot on Micro-Server
# Run on server: bash deploy/health_check.sh
# ============================================================

echo "=========================================="
echo " Hesab Bot - Health Check"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# ---- System Resources ----
echo ""
echo "--- System Resources ---"
RAM_TOTAL=$(free -m | awk '/Mem:/{print $2}')
RAM_USED=$(free -m | awk '/Mem:/{print $3}')
RAM_AVAIL=$(free -m | awk '/Mem:/{print $7}')
SWAP_TOTAL=$(free -m | awk '/Swap:/{print $2}')
SWAP_USED=$(free -m | awk '/Swap:/{print $3}')
DISK_FREE=$(df -h / | awk 'NR==2{print $4}')
LOAD=$(uptime | awk -F'load average:' '{print $2}')

echo "  RAM: ${RAM_USED}MB / ${RAM_TOTAL}MB (Available: ${RAM_AVAIL}MB)"
echo "  Swap: ${SWAP_USED}MB / ${SWAP_TOTAL}MB"
echo "  Disk Free: ${DISK_FREE}"
echo "  Load:${LOAD}"

# ---- Warnings ----
if [ "$RAM_AVAIL" -lt 30 ]; then
    echo "  ⚠️  CRITICAL: Less than 30MB RAM available!"
fi
if [ "$SWAP_USED" -gt 500 ]; then
    echo "  ⚠️  WARNING: Swap usage > 500MB (heavy swapping)"
fi

# ---- PM2 Status ----
echo ""
echo "--- PM2 Process Status ---"
pm2 jlist 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for p in data:
        name = p['name']
        status = p['pm2_env']['status']
        pid = p['pid']
        restarts = p['pm2_env']['restart_time']
        mem = p['monist']['memory'] // 1024 // 1024
        uptime_ms = p['pm2_env'].get('pm_uptime', 0)
        from datetime import datetime
        if uptime_ms:
            uptime = str(datetime.now() - datetime.fromtimestamp(uptime_ms/1000)).split('.')[0]
        else:
            uptime = 'N/A'
        print(f'  Name: {name}')
        print(f'  Status: {status}')
        print(f'  PID: {pid}')
        print(f'  Memory: {mem}MB')
        print(f'  Restarts: {restarts}')
        print(f'  Uptime: {uptime}')
except Exception as e:
    print(f'  Error reading PM2 data: {e}')
" 2>/dev/null || echo "  PM2 not running or no processes"

# ---- Bot Process Check ----
echo ""
echo "--- Bot Process ---"
BOT_PID=$(pm2 jlist 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for p in data:
        if p['name'] == 'hesab-bot' and p['pm2_env']['status'] == 'online':
            print(p['pid'])
except: pass
" 2>/dev/null)

if [ -n "$BOT_PID" ] && [ "$BOT_PID" != "0" ]; then
    echo "  Bot is ONLINE (PID: ${BOT_PID})"
    # Check if process is actually alive
    if kill -0 "$BOT_PID" 2>/dev/null; then
        echo "  Process is alive and responsive."
    else
        echo "  ⚠️  WARNING: Process exists in PM2 but PID not responding!"
    fi
else
    echo "  ❌ Bot is NOT running!"
fi

# ---- MongoDB Connectivity ----
echo ""
echo "--- Database Connectivity ---"
cd /home/hesab/app
source venv/bin/activate
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app.database.models import get_database
    db = get_database()
    db.command('ping')
    print('  MongoDB: Connected')
except Exception as e:
    print(f'  MongoDB: FAILED - {e}')
" 2>/dev/null || echo "  Could not test DB connection"

# ---- Recent Errors ----
echo ""
echo "--- Recent Errors (last 5) ---"
if [ -f "/home/hesab/app/logs/pm2-error.log" ]; then
    tail -5 /home/hesab/app/logs/pm2-error.log 2>/dev/null | sed 's/^/  /' || echo "  No errors"
else
    echo "  No error log found"
fi

echo ""
echo "=========================================="
