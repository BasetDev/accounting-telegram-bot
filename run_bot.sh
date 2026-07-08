#!/bin/bash
cd "/home/bac/New folder/New/hesab"
nohup python hesab/main.py >> bot.log 2>&1 &
echo $! > bot.pid
echo "Bot started with PID: $(cat bot.pid)"
