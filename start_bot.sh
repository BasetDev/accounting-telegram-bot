#!/bin/bash
cd "/home/bac/New folder/New/hesab"
nohup python3 hesab/main.py > bot_output.log 2>&1 &
echo $!
