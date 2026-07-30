# Hesab - Telegram Accounting Bot

A professional Telegram bot for small and medium businesses to manage income, expenses, debts, receivables, customers, and financial reports directly from Telegram. Built with Python, aiogram 3, and MongoDB.

## Features

- **Income & Expense Tracking** - Register transactions with categories, descriptions, and photo attachments
- **Debt & Receivable Management** - Track debts and receivables with due dates, categories, and customer linking
- **Payment Recording** - Record full or partial payments against debts and receivables
- **Customer Management** - Add, edit, delete, and search customers with contact details
- **Financial Dashboard** - Real-time summary of income, expenses, debts, and receivables
- **Financial Reports** - Daily, weekly, monthly, and yearly reports for all transaction types
- **Excel & PDF Export** - Export reports as `.xlsx` or `.pdf` files
- **Backup & Restore** - Full, database-only, and media backups as ZIP files with integrity verification
- **Card & IBAN Management** - Store and manage card numbers and Sheba (IBAN) numbers
- **Search** - Search transactions by name, amount, date, category, or party
- **Persian (Farsi) UI** - Fully right-to-left interface with Jalali (Shamsi) calendar
- **Photo Attachments** - Attach receipt/document photos to any transaction

---

## Requirements

### Software

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.13+ | Runtime |
| MongoDB | 6.0+ | Database (local or Atlas) |
| pip | latest | Package installer |
| Git | any | Clone the repository |

### System Packages (for PDF export with Persian fonts)

- `fonts-dejavu`
- `fonts-freefont-ttf`

These are installed automatically in the Docker image. For bare-metal installs, the setup instructions below include the install command.

---

## Environment Variables

All configuration is loaded from a `.env` file in the project root via `python-dotenv`. The settings class is at `hesab/app/config.py`.

### Required

| Variable | Example | Description |
|---|---|---|
| `BOT_TOKEN` | `1234567890:ABCdef...` | Telegram Bot API token from [@BotFather](https://t.me/BotFather) |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string. For Atlas: `mongodb+srv://user:pass@cluster.mongodb.net` |

### Optional

| Variable | Default | Description |
|---|---|---|
| `ADMIN_ID` | `0` | Telegram user ID of the admin. Get yours from [@userinfobot](https://t.me/userinfobot) |
| `ADMIN_USERNAME` | `admin` | Admin display name |
| `MONGO_DB_NAME` | `hesab` | MongoDB database name |
| `APP_NAME` | `Hesab Accounting Bot` | Application display name (shown in logs) |
| `APP_VERSION` | `1.0.0` | Application version string |
| `TIMEZONE` | `Asia/Tehran` | Timezone for Jalali date conversion |
| `LANGUAGE` | `fa` | Interface language |
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FILE` | `logs/hesab.log` | Path to the rotating log file |
| `BACKUP_DIR` | `backups/` | Directory for backup ZIP files |
| `EXPORT_DIR` | `exports/` | Directory for generated Excel/PDF files |
| `UPLOAD_DIR` | `uploads/` | Directory for uploaded photo attachments |

---

## Server Deployment (Ubuntu/Debian)

This section walks through deploying from scratch on a fresh Linux server.

### Step 1: System Update & Prerequisites

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl gnupg fonts-dejavu fonts-freefont-ttf
```

### Step 2: Install MongoDB (Local)

If you are using **MongoDB Atlas**, skip this step and use your Atlas connection string for `MONGO_URI`.

```bash
# Import the MongoDB public GPG key
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add the MongoDB 7.0 repository
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt update
sudo apt install -y mongodb-org

# Start and enable MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify MongoDB is running
mongosh --eval "db.stats()"
```

### Step 3: Clone the Repository

```bash
cd /home/$USER
git clone https://github.com/yourusername/hesab.git
cd hesab
```

### Step 4: Create a Virtual Environment & Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Create the `.env` File

```bash
cp .env.example .env
nano .env
```

Fill in at minimum the three required values:

```ini
BOT_TOKEN=your_bot_token_here
MONGO_URI=mongodb://localhost:27017
ADMIN_ID=your_telegram_user_id_here
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

### Step 6: Ensure Required Directories Exist

The repository ships with `.gitkeep` placeholders, but verify they exist:

```bash
mkdir -p logs backups exports uploads
```

### Step 7: Test the Bot

```bash
cd hesab
python main.py
```

You should see:

```
INFO: Connected to MongoDB Atlas: hesab
INFO: Database indexes created successfully.
INFO: Bot commands registered.
INFO: Hesab Accounting Bot v1.0.0 started!
```

Press `Ctrl+C` to stop. The bot handles `SIGTERM` and `SIGINT` for graceful shutdown (closes DB connection, stops polling).

---

## Running Permanently in Production

### Option 1: systemd (Recommended)

This is the recommended method for Linux servers. systemd automatically restarts the bot on failure and integrates with `journalctl` for log management.

Create the service file:

```bash
sudo nano /etc/systemd/system/hesab.service
```

Paste the following, replacing `your_username` with your actual Linux username and adjusting paths if your install location differs:

```ini
[Unit]
Description=Hesab Telegram Accounting Bot
After=network.target mongod.service

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/home/your_username/hesab/hesab
ExecStart=/home/your_username/hesab/venv/bin/python main.py
Restart=on-failure
RestartSec=15
KillSignal=SIGTERM
TimeoutStopSec=30
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hesab.service
sudo systemctl start hesab.service
```

Manage the service:

| Command | Purpose |
|---|---|
| `sudo systemctl status hesab.service` | Check if the bot is running |
| `sudo systemctl restart hesab.service` | Restart the bot |
| `sudo systemctl stop hesab.service` | Stop the bot |
| `sudo journalctl -u hesab.service -f` | Follow live logs |
| `sudo journalctl -u hesab.service -n 100` | Last 100 log lines |

### Option 2: tmux

```bash
tmux new-session -d -s hesab "cd /home/$USER/hesab && source venv/bin/activate && cd hesab && python main.py"
```

Reattach later:

```bash
tmux attach -t hesab
```

Detach: `Ctrl+B`, then `D`.

### Option 3: nohup

```bash
cd /home/$USER/hesab
chmod +x scripts/run_bot.sh
./scripts/run_bot.sh
```

This writes PID to `logs/bot.pid` and appends output to `logs/bot.log`.

To stop:

```bash
kill $(cat logs/bot.pid)
```

To follow logs:

```bash
tail -f logs/bot.log
```

### Option 4: Docker

The repository includes a `Dockerfile`. Build and run:

```bash
docker build -t hesab-bot .

docker run -d --name hesab-bot \
  --restart unless-stopped \
  -v $(pwd)/backups:/app/hesab/backups \
  -v $(pwd)/exports:/app/hesab/exports \
  -v $(pwd)/uploads:/app/hesab/uploads \
  -v $(pwd)/logs:/app/hesab/logs \
  -v $(pwd)/.env:/app/.env:ro \
  hesab-bot
```

The `.env` file is **not** copied into the image. You must mount it at runtime. The bot handles `SIGTERM` for clean container stops.

Manage the container:

```bash
docker logs -f hesab-bot          # View logs
docker stop hesab-bot             # Stop
docker start hesab-bot            # Start
docker rm hesab-bot               # Remove
```

---

## Updating the Bot

```bash
# 1. Navigate to the project directory
cd /home/$USER/hesab

# 2. Pull the latest code
git pull origin main

# 3. Activate the virtual environment and update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Restart the bot (pick the method you use)
#    systemd:
sudo systemctl restart hesab.service
#    Docker:
docker stop hesab-bot && docker rm hesab-bot
docker build -t hesab-bot .
# (re-run the docker run command from above)
```

---

## Troubleshooting

### Bot Fails to Start - Missing `.env`

**Symptom:** Logs show `Bot token is not configured!` or `MongoDB URI is not configured!`

**Solution:** Ensure the `.env` file exists in the project root (next to `requirements.txt`, not inside `hesab/`).

```bash
ls -la /home/$USER/hesab/.env
# If missing:
cp /home/$USER/hesab/.env.example /home/$USER/hesab/.env
nano /home/$USER/hesab/.env
```

### MongoDB Connection Timeout

**Symptom:** Logs show `MongoDB connection attempt X/3 failed` or `ServerSelectionTimeoutError`

**Solutions:**
- Verify MongoDB is running: `sudo systemctl status mongod`
- Check `MONGO_URI` in `.env` matches your MongoDB host/port
- For Atlas: whitelist your server's IP in the Atlas dashboard under Network Access
- The bot retries 3 times with 3-second delays, then exits

### Telegram API Error - Invalid Token

**Symptom:** Logs show `TelegramUnauthorizedError` or `401 Unauthorized`

**Solution:** Verify `BOT_TOKEN` in `.env`. Regenerate from [@BotFather](https://t.me/BotFather) if needed.

### Permission Errors

**Symptom:** `PermissionError` when writing to `logs/`, `backups/`, `exports/`, or `uploads/`

**Solution:**

```bash
cd /home/$USER/hesab
mkdir -p logs backups exports uploads
chown -R $USER:$USER logs backups exports uploads
chmod -R 755 logs backups exports uploads
```

### PDF Export Shows Broken Characters

**Symptom:** Persian text in PDF reports appears as boxes or garbled text

**Solution:** Install the required fonts:

```bash
sudo apt install -y fonts-dejavu fonts-freefont-ttf
```

The bot looks for fonts at these paths (defined in `hesab/app/services/export_service.py`):
- `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
- `/usr/share/fonts/truetype/freefont/FreeSans.ttf`

### systemd Restart Loop

**Symptom:** `systemctl status hesab.service` shows repeated restarts

**Diagnosis:**

```bash
# Check the last crash log
sudo journalctl -u hesab.service -n 50 --no-pager

# Common causes:
# 1. Missing .env file
# 2. MongoDB not running
# 3. Invalid BOT_TOKEN
# 4. Port conflict (not applicable - bot uses long-polling)
```

Fix the root cause, then restart:

```bash
sudo systemctl restart hesab.service
```

### Bot Starts But Does Not Respond

**Possible causes:**
- Another instance is already running and consuming updates. Stop all other instances.
- A webhook is set on the bot token. Delete it: `https://api.telegram.org/bot<TOKEN>/deleteWebhook`
- Network/firewall blocking outbound HTTPS to `api.telegram.org`

---

## MongoDB Collections

The bot creates these collections automatically on first run:

| Collection | Purpose |
|---|---|
| `users` | Telegram user records |
| `transactions` | Income, expense, debt, receivable records |
| `payments` | Payment history for debts/receivables |
| `customers` | Customer contact information |
| `card_info` | Saved card numbers and Sheba (IBAN) |
| `reminders` | Scheduled reminders |
| `backups` | Backup metadata records |
| `counters` | Auto-increment ID sequences |

No manual migration or schema setup is required. Database indexes are created at startup by `hesab/app/database/models.py`.

---

## Bot Commands

Registered automatically with Telegram on startup:

| Command | Description |
|---|---|
| `/start` | Start the bot |
| `/menu` | Main menu |
| `/help` | Help / guide |
| `/dashboard` | Financial dashboard |
| `/report` | Financial reports |
| `/backup` | Backup management |
| `/search` | Search transactions |

---

## Project Structure

```
hesab/
├── hesab/
│   ├── main.py                      # Entry point - bot startup and polling
│   └── app/
│       ├── config.py                # Settings loaded from .env
│       ├── database/
│       │   ├── models.py            # MongoDB connection, schemas, indexes
│       │   └── repository.py        # CRUD repositories
│       ├── handlers/
│       │   └── main_handler.py      # All Telegram handlers + FSM states
│       ├── keyboards/
│       │   └── markups.py           # Reply and inline keyboard definitions
│       ├── services/
│       │   ├── backup_service.py    # Backup/restore logic (ZIP, MongoDB)
│       │   └── export_service.py    # Excel and PDF report generation
│       ├── utils/
│       │   ├── jdatetime_helper.py  # Jalali date/time utilities
│       │   ├── logger.py            # Rotating file + console logger
│       │   └── messages.py          # All Persian message strings
│       └── middleware/
│           └── __init__.py
├── scripts/
│   ├── run_bot.sh                   # Background launch script (nohup + PID)
│   ├── start_bot.sh                 # Background launch script (simple nohup)
│   └── detect_orphan_media.py       # Utility: find orphaned upload files
├── backups/                         # Backup ZIP files (runtime, gitignored)
├── data/                            # Local data (runtime, gitignored)
├── docs/                            # Project documentation
├── exports/                         # Generated Excel/PDF (runtime, gitignored)
├── logs/                            # Log files (runtime, gitignored)
├── uploads/                         # Photo attachments (runtime, gitignored)
├── .env.example                     # Environment variable template
├── .gitignore
├── .dockerignore
├── Dockerfile
├── railway.json
├── requirements.txt
└── README.md
```

---

## License

This project is open-source. See the LICENSE file for details.
