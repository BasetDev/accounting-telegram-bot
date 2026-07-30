# Hesab (حساب) — Project Architecture Document

> **Generated from code analysis.** Date: 2026-06-30.
> This document describes the existing project structure, architecture, and design without suggesting or implementing any changes.

---

## 1. Project Overview

**Hesab** (Persian: حساب, meaning "account/calculation") is a Telegram bot for small-business financial management. It is written in **Python 3.13+** using the **aiogram 3.10** framework and **MongoDB** (via **pymongo**). The bot manages income, expenses, debts, receivables, customers, bank cards/IBANs, and generates Excel/PDF reports — all through an interactive Telegram interface using Persian (Farsi) language.

---

## 2. Complete File and Directory Structure

```
hesab/
├── .dockerignore
├── .env                          # Environment variables (BOT_TOKEN, DB_URL, etc.)
├── .gitignore
├── APP_STRUCTURE.md              # Menu navigation tree (hand-written doc)
├── Dockerfile                    # Python 3.13-slim container
├── MENU_ANALYSIS.md              # Menu system callback analysis (hand-written doc)
├── README.md                     # Bilingual project README (FA/EN)
├── SRS_AND_TECHNICAL_DESIGN.md   # Detailed SRS + technical design (hand-written doc)
├── Untitled-1                    # Empty/placeholder file
├── railway.json                  # Railway.app deployment config
├── requirements.txt              # Python dependency list
├── start_bot.sh                  # Shell launcher script
│
├── backups/                      # Database backup files (.db)
│   └── hesab_backup_1405-04-04.db
│
├── data/
│   └── hesab.db                  # SQLite database (live)
│
├── exports/                      # Generated report files
│   ├── transactions_1405-04-04.pdf
│   ├── transactions_1405-04-04.xlsx
│   ├── transactions_1405-04-06.xlsx
│   ├── transactions_1405-04-07.xlsx
│   └── transactions_1405-04-08.pdf
│
├── logs/
│   ├── hesab.log                 # Application log (rotating)
│   ├── bot.log                   # Startup log
│   └── bot_test.log
│
├── uploads/                      # Receipt photo uploads
│   └── *.jpg
│
└── hesab/                        # Main application package
    ├── main.py                   # Entry point
    ├── migrate_add_due_time.py   # Standalone migration script
    ├── migrate_add_backup_time.py# Standalone migration script
    │
    ├── app/
    │   ├── __init__.py           # (empty)
    │   ├── config.py             # Settings from .env
    │   │
    │   ├── database/
    │   │   ├── __init__.py       # (empty)
    │   │   ├── models.py         # 7 SQLAlchemy ORM models
    │   │   └── repository.py     # Data access layer (7 repository classes)
    │   │
    │   ├── handlers/
    │   │   ├── __init__.py       # (empty)
    │   │   └── main_handler.py   # ALL Telegram handlers (~4200 lines, ~106 functions)
    │   │
    │   ├── keyboards/
    │   │   ├── __init__.py       # (empty)
    │   │   └── markups.py        # All keyboard/menu factory functions (~30+)
    │   │
    │   ├── middleware/
    │   │   └── __init__.py       # (empty placeholder)
    │   │
    │   ├── services/
    │   │   ├── __init__.py       # (empty)
    │   │   └── export_service.py # Excel (openpyxl) + PDF (reportlab) generation
    │   │
    │   └── utils/
    │       ├── __init__.py       # (empty)
    │       ├── jdatetime_helper.py # Jalali date/time utilities + Persian num formatting
    │       ├── logger.py         # Logging configuration
    │       └── messages.py       # All Persian UI strings (~100+ strings)
    │
    └── __pycache__/              # Bytecode cache
```

---

## 3. Application Layers and Interaction

The application follows a modular layered architecture:

```
┌──────────────────────────────────────────────────────────┐
│                     Telegram User                         │
├──────────────────────────────────────────────────────────┤
│                    Telegram Bot API                        │
├──────────────────────────────────────────────────────────┤
│  main.py — Entry Point (Bot + Dispatcher + Router)        │
├──────────────────────────────────────────────────────────┤
│  handlers/main_handler.py — Controller Layer              │
│    ├── Command handlers                                   │
│    ├── FSM message handlers                               │
│    ├── Callback handlers                                  │
│    └── Fallback handler                                   │
├──────────────────────────────────────────────────────────┤
│  keyboards/markups.py — Presentation Layer                │
│    ├── ReplyKeyboard markup generation                    │
│    └── InlineKeyboard markup generation                   │
├──────────────────────────────────────────────────────────┤
│  services/export_service.py — Service Layer               │
│    └── Excel / PDF generation                             │
├──────────────────────────────────────────────────────────┤
│  database/repository.py — Data Access Layer               │
│    └── 7 repository classes (static CRUD methods)         │
├──────────────────────────────────────────────────────────┤
│  database/models.py — ORM / Entity Layer                  │
│    └── 7 SQLAlchemy declarative models                    │
├──────────────────────────────────────────────────────────┤
│  utils/ — Support Layer                                   │
│    ├── jdatetime_helper.py — Date/number utilities        │
│    ├── messages.py — UI string constants                  │
│    └── logger.py — Logging setup                          │
├──────────────────────────────────────────────────────────┤
│                  SQLite Database                           │
└──────────────────────────────────────────────────────────┘
```

**Data flow:**

1. User sends a message to the Telegram bot.
2. aiogram `Dispatcher` receives the update.
3. The `Router` dispatches to the matching handler (by FSM state, command text, or callback data pattern).
4. The handler calls the appropriate `Repository` static method(s) via a database session.
5. The repository creates/updates SQLAlchemy model instances and commits to SQLite.
6. The handler constructs a response using Persian strings from `messages.py`.
7. The handler builds keyboard markup via `markups.py` factory functions.
8. The handler sends the response (text + keyboard) back through the aiogram API.

---

## 4. Module Organization and Responsibilities

### 4.1 `hesab/main.py` — Entry Point
- Creates `Bot` instance with the token from `config.py`.
- Creates `Dispatcher` with `MemoryStorage()` (in-memory FSM storage).
- Includes `router` from `handlers/main_handler.py`.
- Runs `await dp.start_polling(bot)` with a startup callback that prints bot info.

### 4.2 `hesab/app/config.py` — Configuration
- Exports a `settings` singleton object.
- Reads from `.env` via `python-dotenv`.
- Provides paths: `BASE_DIR`, `DATABASE_URL`, `LOG_FILE`, `BACKUP_DIR`, `EXPORT_DIR`, `UPLOAD_DIR`.
- `is_valid` property checks that `BOT_TOKEN` is set.

### 4.3 `hesab/app/database/models.py` — ORM Models
- 7 SQLAlchemy 2.0 `DeclarativeBase` models (see §5).
- `init_database()` function: creates tables and auto-migrates missing columns via `ALTER TABLE`.
- `SessionLocal` factory with `check_same_thread=False` and `StaticPool`.

### 4.4 `hesab/app/database/repository.py` — Data Access
- 7 repository classes with **only static methods** (no instances).
- `get_session()` context manager yields `SessionLocal()`.
- Each method opens, uses, and closes a session in a `try/finally` block.

### 4.5 `hesab/app/handlers/main_handler.py` — All Handlers
- Single `Router` instance.
- ~106 handler functions, ~4200 lines.
- 16 FSM classes defined within this file (see §8).
- Handles: commands, menu clicks, FSM data entry, inline callbacks, pagination.
- Contains all business logic inline (no separate service layer for business rules).

### 4.6 `hesab/app/keyboards/markups.py` — Keyboard Factories
- ~30+ keyboard factory functions returning `ReplyKeyboardMarkup` or `InlineKeyboardMarkup`.
- Static menus (income categories, expense categories) and dynamic menus (customer list, card list, transaction list).
- Some functions accept parameters for filtered/contextual menus.

### 4.7 `hesab/app/services/export_service.py` — Export Service
- `export_transactions_excel()`: Generates `.xlsx` with openpyxl. Applies RTL layout, Persian header styling.
- `export_transactions_pdf()`: Generates `.pdf` with reportlab using a Persian-compatible font.
- Both take a list of transactions and a file path; return the file path on success.

### 4.8 `hesab/app/utils/jdatetime_helper.py` — Date/Number Utilities
- Functions: `get_today_jalali()`, `get_now_jalali()`, `convert_persian_digits()`, `format_amount()`, `number_to_words_persian()`, `number_to_words_english()`.
- Provides consistent Jalali date formatting across the app.

### 4.9 `hesab/app/utils/messages.py` — UI Strings
- All user-facing Persian strings in one file.
- Sectioned by feature: `WELCOME`, `INCOME`, `EXPENSE`, `DEBT`, `RECEIVABLE`, `CUSTOMER`, `CARD`, `SEARCH`, `BACKUP`, `ERROR`, etc.

### 4.10 `hesab/app/utils/logger.py` — Logging
- Configures `RotatingFileHandler` (5 MB max, 3 backups) + `StreamHandler`.
- Log format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.

---

## 5. Database Architecture

### 5.1 Database Engine

- **Type:** MongoDB (via pymongo)
- **Connection URI:** Configured via `MONGO_URI` environment variable
- **Database Name:** Configured via `MONGO_DB_NAME` (default: `hesab`)
- **Indexes:** Auto-created by `init_database()` on startup
- **ID Generation:** Auto-increment via `counters` collection

### 5.2 Tables, Columns, and Constraints

#### `users`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `Integer` | PK, auto-increment |
| `telegram_id` | `BigInteger` | **UNIQUE**, NOT NULL, INDEXED |
| `username` | `String(255)` | NULLABLE |
| `first_name` | `String(255)` | NULLABLE |
| `last_name` | `String(255)` | NULLABLE |
| `is_admin` | `Boolean` | DEFAULT `False` |
| `is_active` | `Boolean` | DEFAULT `True` |
| `created_at` | `DateTime` | DEFAULT `utcnow` |
| `updated_at` | `DateTime` | `onupdate=utcnow` |

#### `transactions`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `Integer` | PK, auto-increment |
| `user_id` | `Integer` | FK → `users.id`, NOT NULL, INDEXED |
| `transaction_type` | `String(50)` | NOT NULL, INDEXED (`income`/`expense`/`debt`/`receivable`) |
| `amount` | `Float` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `category` | `String(255)` | NULLABLE |
| `subcategory` | `String(255)` | NULLABLE |
| `party_name` | `String(255)` | NULLABLE |
| `customer_id` | `Integer` | FK → `customers.id`, NULLABLE |
| `jalali_date` | `String(20)` | NOT NULL |
| `jalali_time` | `String(20)` | NOT NULL |
| `jalali_full` | `String(50)` | NOT NULL |
| `due_jalali_date` | `String(20)` | NULLABLE |
| `due_jalali_time` | `String(20)` | NULLABLE |
| `photo_path` | `String(500)` | NULLABLE |
| `card_number` | `String(16)` | NULLABLE |
| `sheba` | `String(26)` | NULLABLE |
| `bank_name` | `String(255)` | NULLABLE |
| `created_at` | `DateTime` | DEFAULT `utcnow` |
| `is_settled` | `Boolean` | DEFAULT `False` |
| `settled_at` | `DateTime` | NULLABLE |

#### `customers`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `Integer` | PK, auto-increment |
| `user_id` | `Integer` | FK → `users.id`, NOT NULL, INDEXED |
| `full_name` | `String(255)` | NOT NULL |
| `phone` | `String(50)` | NULLABLE |
| `address` | `Text` | NULLABLE |
| `notes` | `Text` | NULLABLE |
| `total_debt` | `Float` | DEFAULT `0.0` |
| `total_receivable` | `Float` | DEFAULT `0.0` |
| `created_at` | `DateTime` | DEFAULT `utcnow` |
| `updated_at` | `DateTime` | `onupdate=utcnow` |

#### `card_info`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `Integer` | PK, auto-increment |
| `user_id` | `Integer` | FK → `users.id`, NOT NULL, INDEXED |
| `name` | `String(255)` | NOT NULL |
| `customer_id` | `Integer` | FK → `customers.id`, NULLABLE |
| `card_number` | `String(16)` | NULLABLE |
| `sheba` | `String(26)` | NULLABLE |
| `bank_name` | `String(255)` | NULLABLE |
| `created_at` | `DateTime` | DEFAULT `utcnow` |
| `updated_at` | `DateTime` | `onupdate=utcnow` |

#### `reminders`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `Integer` | PK, auto-increment |
| `user_id` | `Integer` | FK → `users.id`, NOT NULL, INDEXED |
| `transaction_id` | `Integer` | FK → `transactions.id`, NULLABLE |
| `reminder_type` | `String(50)` | NOT NULL |
| `title` | `String(255)` | NOT NULL |
| `message` | `Text` | NULLABLE |
| `reminder_jalali_date` | `String(20)` | NOT NULL |
| `reminder_time` | `String(20)` | NULLABLE |
| `is_sent` | `Boolean` | DEFAULT `False` |
| `sent_at` | `DateTime` | NULLABLE |
| `created_at` | `DateTime` | DEFAULT `utcnow` |

#### `backups`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `Integer` | PK, auto-increment |
| `user_id` | `Integer` | FK → `users.id`, NOT NULL |
| `filename` | `String(255)` | NOT NULL |
| `file_size` | `BigInteger` | DEFAULT `0` |
| `jalali_date` | `String(20)` | NOT NULL |
| `jalali_time` | `String(20)` | NULLABLE |
| `created_at` | `DateTime` | DEFAULT `utcnow` |

#### `payments`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `Integer` | PK, auto-increment |
| `transaction_id` | `Integer` | FK → `transactions.id`, NOT NULL, INDEXED |
| `user_id` | `Integer` | FK → `users.id`, NOT NULL, INDEXED |
| `amount` | `Float` | NOT NULL |
| `payment_type` | `String(50)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `photo_path` | `String(500)` | NULLABLE |
| `jalali_date` | `String(20)` | NOT NULL |
| `jalali_time` | `String(20)` | NOT NULL |
| `jalali_full` | `String(50)` | NOT NULL |
| `created_at` | `DateTime` | DEFAULT `utcnow` |

### 5.3 Entity Relationships

```
users ────1:N──── transactions
users ────1:N──── customers
users ────1:N──── card_info
users ────1:N──── reminders
users ────1:N──── backups
users ────1:N──── payments

customers ────1:N──── transactions
customers ────1:N──── card_info

transactions ────1:N──── reminders
transactions ────1:N──── payments
```

### 5.4 Index Coverage

| Table | Indexed Columns | Purpose |
|-------|----------------|---------|
| `users` | `telegram_id` (UNIQUE) | Fast user lookup |
| `transactions` | `user_id`, `transaction_type` | User-specific type queries, listing, filtering |
| `customers` | `user_id` | User-specific customer queries |
| `card_info` | `user_id` | User-specific card queries |
| `reminders` | `user_id` | User-specific reminder queries |
| `payments` | `transaction_id`, `user_id` | Payment history and user queries |

### 5.5 Migration Scripts

Located in `hesab/` as standalone Python scripts (not managed by Alembic):
- **`migrate_add_due_time.py`** — Adds `due_jalali_time` column to `transactions`.
- **`migrate_add_backup_time.py`** — Adds `jalali_time` column to `backups`.

All other schema migrations are handled at startup by `init_database()` in `models.py`, which iterates a hardcoded map of table/column/type and issues `ALTER TABLE ADD COLUMN` for any missing columns.

---

## 6. Business Logic Structure

All business logic is embedded within the handler functions in `main_handler.py`. There is **no separate business-logic service layer**. Key business rules:

### 6.1 Financial Calculations
- **Balance:** `balance = total_income - total_expense + total_receivables - total_debts`
- **Dashboard totals:** Computed live in `show_dashboard()` via repository aggregation queries.

### 6.2 Transaction Type Rules
- `income` / `expense` — Simple single-step recording with optional photo.
- `debt` / `receivable` — Multi-step flows with due date, customer linking, card/IBAN, payment tracking, edit/delete capability.

### 6.3 Settlement Logic
- Debts and receivables are marked `is_settled = True` when fully paid.
- Partial payments create `payments` records; the remaining balance is tracked via `get_remaining()`.
- A transaction is settled when `sum(payments.amount) >= transaction.amount`.

### 6.4 Customer Financial Summary
- `customers.total_debt` and `customers.total_receivable` are **cached values**.
- Updated on transaction create/edit/delete via `CustomerRepository.update_financial_summary()`.

### 6.5 Overdue Detection
- Based on `due_jalali_date < get_today_jalali()` and `is_settled = False`.
- Separate views for active, settled, and overdue debts/receivables.

### 6.6 Validation Rules
- **Amount:** Must be a positive number; decimals allowed.
- **Card number:** Exactly 16 digits, numeric only.
- **IBAN (Sheba):** Exactly 24 digits (the `IR` prefix is stripped).
- **Date:** Must match pattern `^\d{4}/\d{2}/\d{2}$`.
- **Duplicate check:** Card numbers and IBANs are checked per user before saving.

---

## 7. Services, Repositories, Utilities, and Shared Components

### 7.1 Repository Classes (`database/repository.py`)

All methods are `@staticmethod`. Each method manages its own session via `get_session()` context manager.

| Repository | Key Methods |
|------------|-------------|
| `UserRepository` | `get_or_create()`, `get_by_telegram_id()`, `get_by_id()`, `make_admin()`, `get_all_users()` |
| `TransactionRepository` | `create()`, `get_by_id()`, `get_by_user()`, `get_active()`, `get_settled()`, `get_overdue()`, `get_due_today()`, `get_due_this_week()`, `get_by_date_range()`, `get_by_customer()`, `get_summary()`, `get_total_by_type()`, `update()`, `settle_transaction()`, `delete()`, `search()` |
| `CustomerRepository` | `create()`, `get_by_id()`, `get_by_user()`, `search()`, `update()`, `delete()`, `update_financial_summary()` |
| `ReminderRepository` | `create()`, `get_pending()`, `mark_sent()` |
| `CardInfoRepository` | `create()`, `get_by_id()`, `get_by_user()`, `update()`, `delete()`, `search()` |
| `BackupRepository` | `create()`, `get_recent()` |
| `PaymentRepository` | `create()`, `get_by_transaction()`, `get_total_paid()`, `get_remaining()`, `get_by_user()` |

### 7.2 Service Layer (`services/export_service.py`)

| Function | Input | Output |
|----------|-------|--------|
| `export_transactions_excel(transactions, filepath)` | Transaction list + output path | `.xlsx` file |
| `export_transactions_pdf(transactions, filepath)` | Transaction list + output path | `.pdf` file |

### 7.3 Utilities (`utils/`)

| File | Contents |
|------|----------|
| `jdatetime_helper.py` | `get_today_jalali()`, `get_now_jalali()`, `convert_persian_digits()`, `format_amount()`, `number_to_words_persian()`, `number_to_words_english()` |
| `messages.py` | Persian UI strings organized by feature section |
| `logger.py` | Rotating file logger + console logger |

---

## 8. Handlers, Routers, Controllers, Middleware, and Navigation Flow

### 8.1 Router

A single `aiogram.Router` named `router` (module-level singleton in `main_handler.py`). Included in the dispatcher via `dp.include_router(router)` in `main.py`.

### 8.2 Handler Categories

| Category | Count | Mechanism |
|----------|-------|-----------|
| **Command handlers** | ~7 | `@router.message(Command("start"))`, etc. |
| **Menu button handlers** | ~13 | `@router.message(Text("💰 ثبت درآمد"))`, etc. — exact Persian text matching |
| **FSM message handlers** | ~28 | `@router.message(IncomeForm.amount)`, etc. — state-specific |
| **FSM callback handlers** | ~14 | `@router.callback_query(DebtForm.confirm)` — state-specific callbacks |
| **Inline callback handlers** | ~12 | `@router.callback_query(Text(startswith="edit_debt:"))` — callback data prefixes |
| **Item action handlers** | ~20 | `@router.callback_query(Text(startswith="view_photo:"))` — per-item actions |
| **Fallback handler** | 1 | `@router.message()` — catches any unmatched message |

### 8.3 Command Handlers (Entry Points)

| Command | Handler Function | Purpose |
|---------|-----------------|---------|
| `/start` | `cmd_start()` | Register user, show main menu |
| `/menu` | `cmd_menu()` | Show main menu |
| `/help` | `cmd_help()` | Show help text |
| `/dashboard` | `cmd_dashboard()` | Show financial summary |
| `/report` | `cmd_report()` | Show report options |
| `/backup` | `cmd_backup()` | Show backup options |
| `/search` | `cmd_search()` | Show search prompt |

### 8.4 Main Menu Flow

The main menu (shown on `/start` or `/menu`) offers 13 buttons. Each button triggers its own handler by exact text match:

```
💰 ثبت درآمد         → IncomeForm.amount
💸 ثبت هزینه         → ExpenseForm.amount
💳 بدهی‌ها            → debt_category_filter menu
🔁 دریافت‌ها          → receivable_category_filter menu
👤 مشتریان            → customer management menu
💳 کارت و شبا         → card management menu
📊 گزارشات            → report menu
📋 داشبورد            → dashboard display
🔍 جستجو               → search prompt
💾 پشتیبان‌گیری       → backup menu
❓ راهنما              → help text
📤 پشتیبانی           → contact support
🏠 منوی اصلی          → main menu (while in submenus)
```

### 8.5 Middleware

The `middleware/` directory contains only an empty `__init__.py`. **No middleware is currently implemented.** There is no rate limiting, user authorization middleware, logging middleware, or any other middleware layer.

---

## 9. State Management (FSM)

### 9.1 FSM Implementation

Uses **aiogram's built-in FSM** with `MemoryStorage` (in-memory, non-persistent). All 16 FSM classes are defined at the top of `main_handler.py`:

| # | FSM Class | States | Purpose |
|---|-----------|--------|---------|
| 1 | `IncomeForm` | `amount`, `description`, `category`, `photo`, `confirm` | Register income |
| 2 | `ExpenseForm` | `amount`, `description`, `category`, `photo`, `confirm` | Register expense |
| 3 | `DebtForm` | `category`, `subcategory`, `amount`, `party`, `description`, `due_date`, `photo`, `card_select`, `manual_card`, `sheba_select`, `manual_sheba`, `bank_name_select`, `manual_bank_name`, `customer_id`, `confirm` | Register debt (~15 states) |
| 4 | `ReceivableForm` | `category`, `subcategory`, `amount`, `party`, `description`, `due_date`, `photo`, `card_select`, `manual_card`, `sheba_select`, `manual_sheba`, `bank_name_select`, `manual_bank_name`, `customer_id`, `confirm` | Register receivable |
| 5 | `CustomerForm` | `name`, `phone`, `address`, `notes`, `confirm` | Add customer |
| 6 | `CustomerEditForm` | `select`, `name`, `phone`, `address`, `notes` | Edit customer |
| 7 | `CustomerDeleteForm` | `select`, `confirm` | Delete customer |
| 8 | `SearchForm` | `query`, `transaction_type` | Search transactions |
| 9 | `CustomerSearchForm` | `query` | Search customers |
| 10 | `DebtEditForm` | `edit_id`, `amount`, `party`, `description`, `due_date`, `confirm`, `delete_confirm` | Edit/delete debt |
| 11 | `ReceivableEditForm` | `edit_id`, `amount`, `party`, `description`, `due_date`, `confirm`, `delete_confirm` | Edit/delete receivable |
| 12 | `CardForm` | `name_choice`, `name_manual`, `name_customer_select`, `card_number`, `sheba`, `bank_name`, `confirm` | Register card/IBAN |
| 13 | `CardEditForm` | `select`, `field`, `value`, `confirm` | Edit card |
| 14 | `CardDeleteForm` | `select`, `confirm` | Delete card |
| 15 | `CardSearchForm` | `query` | Search cards |
| 16 | `PaymentForm` | `select`, `payment_type`, `amount`, `description`, `photo`, `confirm` | Process payment |

### 9.2 State Data Storage

FSM context data (accessed via `state.get_data()` / `state.update_data()`) stores partially collected form data during multi-step flows. The data dictionary is cleared on completion or cancellation.

### 9.3 Important Note

`MemoryStorage` means all FSM states are lost on bot restart. There is no Redis, database-backed, or file-backed FSM persistence.

### 9.4 In-Memory Cache

A single module-level dictionary `_recv_groups_cache` exists in `main_handler.py` to cache grouped receivable data for customer detail views. This is a volatile cache (lost on restart).

---

## 10. Configuration, Environment Variables, and Startup

### 10.1 Environment Variables (`.env`)

| Variable | Example Value | Purpose |
|----------|---------------|---------|
| `BOT_TOKEN` | `your_bot_token_here` | Telegram Bot API token (from @BotFather) |
| `ADMIN_ID` | `your_telegram_user_id_here` | Telegram user ID with admin access |
| `ADMIN_USERNAME` | `admin` | Admin username |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME` | `hesab` | MongoDB database name |
| `APP_NAME` | `Hesab Accounting Bot` | Application display name |
| `APP_VERSION` | `1.0.0` | Application version |
| `TIMEZONE` | `Asia/Tehran` | Default timezone |
| `LANGUAGE` | `fa` | Interface language |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | `logs/hesab.log` | Log file path |
| `BACKUP_DIR` | `backups/` | Database backup directory |
| `EXPORT_DIR` | `exports/` | Report export directory |
| `UPLOAD_DIR` | `uploads/` | Photo uploads directory |

### 10.2 Startup Process

1. `start_bot.sh` (or `python -m hesab.main`) launches the application.
2. `main.py` imports `settings` from `config.py`.
3. `init_database()` is called, creating tables and adding missing columns.
4. `Bot` is instantiated with `settings.BOT_TOKEN`.
5. `Dispatcher` is instantiated with `MemoryStorage()`.
6. `router` is included via `dp.include_router(router)`.
7. A startup callback prints bot information to console.
8. `dp.start_polling(bot)` begins polling.

### 10.3 Deployment

- **Docker:** `Dockerfile` uses `python:3.13-slim`, installs system fonts (fonts-farsiweb, fonts-dejavu-core) for PDF Persian rendering, copies the project, and runs `main.py`.
- **Railway.app:** `railway.json` specifies Dockerfile as the builder.

---

## 11. External APIs, Integrations, and Dependencies

### 11.1 Dependencies (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| `SQLAlchemy` | `>=2.0.0,<3.0.0` | ORM |
| `aiogram` | `>=3.10.0,<4.0.0` | Telegram Bot framework (async) |
| `jdatetime` | `>=5.0.0,<6.0.0` | Jalali (Persian) calendar conversion |
| `openpyxl` | `>=3.1.0,<4.0.0` | Excel (.xlsx) generation |
| `reportlab` | `>=4.1.0,<5.0.0` | PDF generation |
| `python-dotenv` | `>=1.0.0,<2.0.0` | Environment variable loader |
| `pytz` | `>=2024.1` | Timezone support |
| `persian-tools` | `>=0.0.10` | Persian text utilities |
| `aiofiles` | `>=24.1.0` | Async file I/O |

### 11.2 External Integrations

- **Telegram Bot API** (via aiogram) — the sole external integration.
- No third-party payment gateways, SMS APIs, email, or webhooks.
- No REST API endpoints.

---

## 12. Background Tasks, Schedulers, and Event Processing

**None currently implemented.** Specific observations:

- The `reminders` table exists with `ReminderRepository.get_pending()` and `mark_sent()` methods, but **no scheduler or background task calls them**.
- There is no APScheduler, cron job, asyncio background task, or periodic polling mechanism.
- There is no event-driven processing beyond handling Telegram updates synchronously within handler callbacks.

---

## 13. Security Architecture, Authentication, Authorization, and Permissions

### 13.1 Authentication
- Any Telegram user who sends `/start` to the bot is **auto-registered**.
- No password, PIN, or two-factor authentication.
- Authentication is implicit: the user's Telegram ID is the identity.

### 13.2 Authorization (Permissions)
- Every database query is scoped to `user_id` — users see only their own data.
- `is_admin` boolean on the `users` table. Admin features exist (admin check at handler level) but are minimal.
- Admin-only features: none explicitly gated beyond the `is_admin` flag; the bot's admin panel is not fully developed.

### 13.3 Input Validation (Security)
- **SQL injection:** Prevented by SQLAlchemy ORM parameterized queries.
- **Amount validation:** Must be a positive number.
- **Card number:** Must be exactly 16 numeric digits.
- **IBAN (Sheba):** Must be exactly 24 digits.
- **Date format:** Must match `YYYY/MM/DD` pattern.
- **File upload:** Photos saved to local filesystem with timestamp-based unique filenames.

### 13.4 Secrets Management
- `BOT_TOKEN` stored in `.env`, excluded from git via `.gitignore` and `.dockerignore`.
- Token is NOT hardcoded in source files.

### 13.5 Notable Gaps
- No rate limiting on commands or API calls.
- No read/write access control (all registered users have full access to all features).
- No FSM state persistence — restarting the bot destroys in-progress user sessions.
- No HTTPS-only requirement (Telegram API already uses HTTPS, but no webhook endpoint).
- Bot token is present in the `.env` file in the repository (should be removed from version control in production).

---

## 14. Logging, Error Handling, Validation, and Exception Flow

### 14.1 Logging (`utils/logger.py`)
- **RotatingFileHandler:** Writes to `logs/hesab.log`, max 5 MB per file, 3 backup rotations.
- **StreamHandler:** Also prints to stdout.
- **Log level:** Configurable via `LOG_LEVEL` env var (default `INFO`).
- **Format:** `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.
- Logger is module-level singleton: `logger = logging.getLogger(__name__)`.

### 14.2 Error Handling Patterns
- **Database sessions:** Always closed in `try/finally` blocks.
- **Database operations:** Wrapped in `try/except` with error logging.
- **User-facing errors:** Returned as Persian messages from `messages.py` (e.g., `ERROR_GENERAL`).
- **File operations (export, photo save):** Wrapped in `try/except` with user notification.
- **Import errors:** `openpyxl` and `reportlab` imports are caught, and the user is told the required library is missing.

### 14.3 Validation Flow
- Validation is performed **inside handler functions** before persisting data.
- Invalid input triggers `await message.reply(msg)` with a Persian error message and returns to the same FSM state (user can retry).
- There is no centralized validation schema or validator class.

### 14.4 Exception Flow Summary

```
User input arrives
  → Handler function
    → Input validation (if fails → reply with error → return to same state)
    → Database operation (if fails → log error → reply ERROR_GENERAL)
    → File operation (if fails → log error → reply ERROR_GENERAL)
    → Success → reply with confirmation → clear state → show menu
```

---

## 15. Data Flow Between Modules

### 15.1 Transaction Creation (Income Example)

```
User: /start
  → cmd_start() [main_handler.py]
    → UserRepository.get_or_create() [repository.py]
    → Main menu keyboard [markups.py]
    → message.answer("به ربات حسابداری خوش آمدید...", reply_markup=main_menu)

User: "💰 ثبت درآمد"
  → IncomeForm.amount state set
  → message.answer("مبلغ درآمد را وارد کنید:", reply_markup=cancel_back_menu)

User: "500000"
  → IncomeForm.description state
  → state.update_data(amount=500000)
  → message.answer("توضیحات را وارد کنید:", reply_markup=photo_skip_menu)

User: "فروش محصول"
  → IncomeForm.category state
  → state.update_data(description="فروش محصول")
  → income_categories keyboard

User: "🛍 فروش کالا"
  → IncomeForm.photo state
  → state.update_data(category="فروش کالا")
  → photo_skip_menu

User: "رد شدن"
  → TransactionRepository.create(...) [repository.py]
    → session.add(transaction) → session.commit()
  → message.answer("✅ درآمد ثبت شد.", reply_markup=main_menu)
  → state.clear()
```

### 15.2 Debt Payment Flow

```
User: منوی بدهی‌ها → لیست بدهی‌های فعال
  → inline callback → list of unpaid debts
  → user selects a debt → PaymentForm.select

User: selects payment type (full/partial)
  → PaymentForm.payment_type → PaymentForm.amount
  → user enters amount → PaymentForm.description
  → user enters description (optional) → PaymentForm.photo
  → user skips photo → PaymentForm.confirm

User: confirms
  → PaymentRepository.create(...) [repository.py]
  → If fully paid: TransactionRepository.settle_transaction(...)
  → CustomerRepository.update_financial_summary(...)
  → message.answer("✅ پرداخت ثبت شد.")
```

### 15.3 Report Export Flow

```
User: "📊 گزارشات" → report_menu
  → user selects period → transactions fetched from DB
  → inline export menu: Excel / PDF

User: Excel
  → export_transactions_excel(transactions, filepath) [export_service.py]
  → File sent to user via FSInputFile
```

---

## 16. Main Workflows and Feature Interactions

### 16.1 Complete Feature List

| Feature | Description |
|---------|-------------|
| **Income Registration** | Multi-step FSM: amount → description → category → photo (optional) → save |
| **Expense Registration** | Multi-step FSM: amount → description → category → photo (optional) → save |
| **Debt Registration** | Long multi-step FSM: category → subcategory → amount → party → description → due_date → photo → card/sheba/bank → customer → confirm |
| **Receivable Registration** | Same structure as debt |
| **Customer Management** | Add / edit / delete / search / view financial summary per customer |
| **Card & IBAN Management** | Add / edit / delete / search bank cards and IBAN numbers |
| **Transaction Listing** | Filter by: active, settled, overdue, due today/this week, by category, by customer, by date range |
| **Debt Tracking** | Full payment, partial payment, remaining balance calculation |
| **Receivable Tracking** | Full receive, partial receive, remaining balance |
| **Edit/Delete Transactions** | Modify amount, party, description, due date; or delete with confirmation |
| **Search** | Search transactions by text query across description, party, category, amount |
| **Dashboard** | Live-calculated summary: income, expenses, debts, receivables, balance |
| **Reports** | Period-based filtering with Excel/PDF export |
| **Database Backup** | Create backup copies, send to user, list recent backups |
| **Help** | List of available commands and features |

### 16.2 Feature Interaction Map

```
User Registration (/start)
  → All other features (auto-auth by Telegram ID)

Income / Expense Registration
  → Updates dashboard calculations
  → No customer linking (unlike debts/receivables)

Debt / Receivable Registration
  → Links to Customer (creates if new)
  → Optionally links to Card/IBAN
  → Updates customer financial summary
  → Payment flow settles partially or fully

Customer Management
  → Consolidated view of all debts + receivables for that customer
  → Financial summary cached (total_debt, total_receivable)

Card / IBAN Management
  → Used during debt/receivable registration
  → Linked optionally to customers

Backup
  → Copies the entire SQLite database file
  → Independent of all other operations

Search
  → Cross-cuts transactions, customers, and cards
  → Read-only operation
```

---

## 17. Existing Design Patterns and Architectural Decisions

### 17.1 Patterns in Use

| Pattern | Location | Description |
|---------|----------|-------------|
| **Repository Pattern** | `database/repository.py` | Static classes encapsulate all DB access; handlers never use SQLAlchemy directly |
| **Finite State Machine** | `main_handler.py` (16 FSM classes) | aiogram's FSM for multi-step conversational workflows |
| **Singleton** | `config.py` (`settings`), `logger.py` (`logger`), `main_handler.py` (`router`) | Single instance per module |
| **Factory Method** | `markups.py` | Functions that create and return keyboard markup objects |
| **Static Method** | `repository.py` | All repository methods are `@staticmethod` |
| **Layered Architecture** | App-wide | config → database → handlers → keyboards → services → utils |
| **Single-File Controller** | `main_handler.py` | All handlers in one file (~4200 lines) |

### 17.2 Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| SQLite over PostgreSQL | Simplicity for single-user/small-business use case; no concurrent write concerns |
| `MemoryStorage` for FSM | No Redis dependency; simpler deployment |
| Static repository methods | Avoids dependency injection complexity; simpler than class-based services |
| All handlers in one file | Rapid development; all callback patterns visible in one place |
| Persian-only UI | Target audience is Persian-speaking small business owners |
| Jalali (Shamsi) calendar | Required for Iranian business context |
| No background scheduler | Simplifies deployment; reminders would require a persistent process |
| Auto-migration via `ALTER TABLE` | Avoids Alembic complexity for a small schema |
| `check_same_thread=False` | Allows reuse of the same session across async handlers |

---

## 18. Known Dependencies Between Modules

### 18.1 Import Graph

```
main.py
  ├── app.config
  ├── app.database.models (init_database)
  ├── app.handlers.main_handler (router)
  └── aiogram (Bot, Dispatcher)

app.config
  └── dotenv

app.database.models
  └── sqlalchemy

app.database.repository
  ├── app.database.models
  └── app.utils.logger

app.handlers.main_handler
  ├── app.config (settings)
  ├── app.database.repository (all 7 repos)
  ├── app.keyboards.markups (all keyboard functions)
  ├── app.utils.jdatetime_helper
  ├── app.utils.messages
  ├── app.utils.logger
  ├── app.services.export_service
  └── aiogram (Router, FSM, types, filters)

app.keyboards.markups
  ├── app.config (settings)
  └── aiogram (types)

app.services.export_service
  ├── app.config (settings)
  ├── app.utils.logger
  ├── app.utils.jdatetime_helper
  ├── openpyxl
  └── reportlab

app.utils.jdatetime_helper
  ├── jdatetime
  └── persian_tools

app.utils.logger
  └── logging (stdlib)
```

### 18.2 Dependency Graph (Circular Dependencies)

No circular dependencies detected. The dependency graph is strictly acyclic:

```
config → independent
utils/* → independent (except logger)
models → config
repository → models, logger
markups → config
export_service → config, logger, jdatetime_helper
main_handler → config, repository, markups, jdatetime_helper, messages, logger, export_service
main.py → config, models, main_handler
```

---

## 19. Suggestions Section

> **Note:** This section contains observations only. No changes are proposed or implemented.

### Architecture
- The single `main_handler.py` (~4200 lines, ~106 handlers) handles all concerns: routing, FSM definition, business logic, validation, and presentation. This could be split into domain-specific handler modules.
- The `middleware/` directory is empty; no middleware is active.
- Business logic lives entirely in handler code rather than a dedicated service layer.
- All repository methods are static, which makes mocking in tests difficult.

### Database
- Auto-migration via `ALTER TABLE` in `init_database()` is fragile for production schema evolution.
- The `reminders` table has no active consumer.
- SQLite is used with `check_same_thread=False` — this works but bypasses SQLite's safety guarantees.
- No Alembic or other migration framework is used.
- Index coverage could be reviewed for query performance on larger datasets.

### State Management
- `MemoryStorage` is non-persistent; all FSM states are lost on bot restart.
- The `_recv_groups_cache` module-level dictionary is an in-memory cache with no invalidation strategy.

### Background Tasks
- Reminder scheduling (for debt/receivable due dates) is not implemented despite the `reminders` table existing.
- No periodic backup mechanism.

### Testing
- No test files or test framework configuration found in the project.

### Security
- The bot token is present in `.env` within the codebase.
- No rate limiting on any endpoint.
- No user session expiry or token revocation.
- Auto-registration means any user with the bot link can access all features.

### Deployment
- No health check endpoint.
- No graceful shutdown handling beyond what aiogram provides by default.
- No webhook mode configuration (uses polling only).

---

*End of Architecture Document*
