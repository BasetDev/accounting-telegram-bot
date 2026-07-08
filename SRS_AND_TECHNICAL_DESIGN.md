# 📊 Hesab - Telegram Accounting Bot: Software Requirements Specification & Technical Design Document

> **Document Version:** 1.0  
> **Date:** 2025-06-28  
> **Language:** English (with Persian/RTL support in application)  

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Complete Feature List](#2-complete-feature-list)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)

---

## 1. Project Overview

**Hesab** (حساب, meaning "account/calculation" in Persian) is a professional Telegram bot for small and medium businesses to manage their accounting directly through Telegram. It provides income and expense tracking, debt and receivable management, customer management, financial reporting, card/IBAN storage, and backup/export capabilities.

### Core Purpose
Enable Iranian business owners to manage their finances entirely within Telegram, using Persian (Jalali) dates in a Persian-language interface with full RTL support.

### Target Users
- Small business owners
- Freelancers and independent workers
- Shop owners and merchants
- Anyone needing simple accounting via Telegram

---

## 2. Complete Feature List

### 2.1 Transaction Management
- ✅ **Income Registration** — Record income with amount, description, category, and optional photo attachment
- ✅ **Expense Registration** — Record expenses with amount, description, category, and optional photo attachment
- ✅ **Debt Registration** — Record debts with amount, party name, description, due date, and optional photo
- ✅ **Receivable Registration** — Record receivables with amount, party name, description, due date, and optional photo
- ✅ **Transaction List Viewing** — View lists of debts and receivables with inline action buttons
- ✅ **Transaction Editing** — Edit amount, party, description, and due date for debts and receivables
- ✅ **Transaction Deletion** — Delete debts and receivables with inline confirmation
- ✅ **Transaction Settlement** — Mark debts/receivables as settled (in debt/receivable list)

### 2.2 Customer Management
- ✅ **Add Customer** — Register customers with name, phone, address, and notes
- ✅ **Edit Customer** — Update customer information via inline selection
- ✅ **Delete Customer** — Remove customers with confirmation
- ✅ **List Customers** — View all customers with debt/receivable summaries
- ✅ **Search Customers** — Search by name or phone number
- ✅ **Auto-suggest Customers** — Customer names appear as keyboard options during debt/receivable entry

### 2.3 Financial Dashboard
- ✅ **Dashboard** — View total income, expenses, debts, receivables, and net balance
- ✅ **Balance Status** — Positive (green/profit), negative (red/loss), or zero (neutral/cleared) status indicator

### 2.4 Financial Reports
- ✅ **Daily Report** — Summary of today's transactions
- ✅ **Weekly Report** — Last 7 days summary
- ✅ **Monthly Report** — Current month summary
- ✅ **Yearly Report** — Current year summary

### 2.5 Export & Backup
- ✅ **Excel Export** — Export all transactions to `.xlsx` with formatted Persian headers and RTL layout
- ✅ **PDF Export** — Export transactions to `.pdf` with Persian font fallback
- ✅ **Database Backup** — Create timestamped backup copies of the SQLite database
- ✅ **Backup List** — View recent backup records
- ✅ **Backup Restore** — Restore from a backup file via Telegram upload

### 2.6 Card & IBAN Management
- ✅ **Register Card/Sheba** — Store card numbers (16 digits) and IBAN/SHEBA numbers (24 digits) with associated names
- ✅ **Name from Customers** — Select customer name from existing customers or enter manually
- ✅ **Duplicate Detection** — Prevent duplicate card/IBAN registration (check against existing records)
- ✅ **List Cards** — View all stored card/IBAN info with inline action buttons
- ✅ **Copy Card Number** — Tap to copy card number to clipboard
- ✅ **Copy IBAN** — Tap to copy IBAN to clipboard
- ✅ **SMS Format** — Copy card/IBAN as a formatted SMS-ready message (name + card + sheba)
- ✅ **Edit Cards** — Update card/IBAN fields
- ✅ **Delete Cards** — Remove card/IBAN records
- ✅ **Search Cards** — Search by name, card number, or IBAN

### 2.7 Search
- ✅ **Global Search** — Search transactions by amount, description, category, party name
- ✅ **Type Filter** — Filter search results by transaction type (income/expense/debt/receivable/all)

### 2.8 User Management (Auto)
- ✅ **Auto-registration** — Users are automatically registered upon first `/start`
- ✅ **Profile Updates** — Username, first/last name auto-updated on each interaction

### 2.9 Reminders System
- ⚠️ **Model exists** (`Reminder` table) but no active scheduler/handler is implemented
- ✅ **Data model supports** — Reminder type, title, message, date, sent status

5. [Technology Stack](#5-technology-stack)
6. [Project File Structure](#6-project-file-structure)
7. [Database Schema & Data Models](#7-database-schema--data-models)
8. [Module-by-Module Architecture](#8-module-by-module-architecture)
9. [Entry Points & Startup Sequence](#9-entry-points--startup-sequence)
10. [Menu Hierarchy & Navigation](#10-menu-hierarchy--navigation)
11. [Conversation Flows (FSM)](#11-conversation-flows-fsm)
12. [Command Handlers](#12-command-handlers)
13. [Callback Handlers & Routing Logic](#13-callback-handlers--routing-logic)
14. [Keyboard Generation System](#14-keyboard-generation-system)
15. [Repository / Data Access Layer](#15-repository--data-access-layer)
16. [Services Layer](#16-services-layer)
17. [Utility Modules](#17-utility-modules)
18. [Date & Time Handling](#18-date--time-handling)
19. [Configuration & Environment Variables](#19-configuration--environment-variables)
20. [Logging & Error Handling](#20-logging--error-handling)
21. [File & Image Upload System](#21-file--image-upload-system)
22. [Deployment Configuration](#22-deployment-configuration)
23. [Business Logic & Validation Rules](#23-business-logic--validation-rules)
24. [User Workflows](#24-user-workflows)
25. [Administrator Workflows](#25-administrator-workflows)
26. [Security Considerations](#26-security-considerations)
27. [Coding Standards & Design Patterns](#27-coding-standards--design-patterns)
28. [Performance Optimizations](#28-performance-optimizations)
29. [Error Handling Strategy](#29-error-handling-strategy)
30. [Logging Strategy](#30-logging-strategy)
31. [Future Scalability Recommendations](#31-future-scalability-recommendations)


---

## 3. Functional Requirements

### FR1: User Registration
- FR1.1: Any Telegram user who sends `/start` must be automatically registered in the database
- FR1.2: User's `telegram_id`, `username`, `first_name`, and `last_name` must be stored
- FR1.3: Existing users' profile info must be updated on each interaction

### FR2: Income Recording
- FR2.1: User selects "💰 ثبت درآمد" from main menu
- FR2.2: System prompts for amount (numeric only, in Iranian Toman) with cancel option
- FR2.3: System prompts for description (text) with cancel/back options
- FR2.4: System prompts for category selection from predefined list (8 categories)
- FR2.5: System prompts for optional photo attachment (photo or skip)
- FR2.6: System saves transaction with current Jalali date/time and sends confirmation

### FR3: Expense Recording
- FR3.1: Same flow as income but with 12 expense-specific categories
- FR3.2: Categories: rent, salary, purchases, transportation, advertising, services, utilities, repairs, raw materials, tax, insurance, other

### FR4: Debt Recording
- FR4.1: User selects "📋 ثبت بدهی" from main menu
- FR4.2: System prompts for amount, party name (with customer auto-suggest), description, due date, optional photo
- FR4.3: Due date can be "today" or manually entered in YYYY/MM/DD format
- FR4.4: Confirmation step showing summary before saving

### FR5: Receivable Recording
- FR5.1: Same 6-step flow as debt recording but labeled as receivable

### FR6: Customer Management
- FR6.1: CRUD operations for customers (add, edit, delete, list, search)
- FR6.2: Search by name or phone (LIKE %query%)
- FR6.3: Display financial summary (total debt/receivable) for each customer

### FR7: Dashboard
- FR7.1: Show totals for income, expenses, debts, receivables
- FR7.2: Calculate net balance: income - expense + receivables - debts
- FR7.3: Display status: positive/green, negative/red, or zero/neutral

### FR8: Reports
- FR8.1: Generate daily, weekly, monthly, yearly reports using Jalali calendar periods
- FR8.2: Show totals by transaction type within the period
- FR8.3: Show balance and status (same calculation as dashboard)

### FR9: Export
- FR9.1: Export all unsettled transactions to Excel (.xlsx) with Persian headers and RTL
- FR9.2: Export all unsettled transactions to PDF (.pdf) with Persian font support

### FR10: Backup
- FR10.1: Create database backup by copying the SQLite file
- FR10.2: Backup filename includes Jalali date and time
- FR10.3: Record backup metadata in backups table
- FR10.4: List recent backups (last 5)
- FR10.5: Restore database by uploading a backup file via Telegram

### FR11: Card/IBAN Management
- FR11.1: Register card number (16 digits) and/or IBAN (24 digits) with associated name
- FR11.2: Name entered manually or selected from customers
- FR11.3: Prevent duplicate entries per user
- FR11.4: Copy card/IBAN to clipboard, generate SMS-ready text
- FR11.5: Edit individual fields, delete with confirmation


---

## 5. Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.13+ |
| Bot Framework | aiogram | 3.10+ |
| Database ORM | SQLAlchemy | 2.0+ |
| Database | SQLite (upgradeable to PostgreSQL) | - |
| Date/Time | jdatetime, pytz | 5.0+, latest |
| Excel Export | openpyxl | 3.1+ |
| PDF Export | reportlab | 4.1+ |
| Environment | python-dotenv | 1.0+ |
| Async Runtime | asyncio | (stdlib) |
| Container | Docker | - |
| Deployment | Railway.app | - |

### Why These Choices
- **aiogram** - Modern async Telegram Bot API with FSM, type-safe
- **SQLAlchemy** - Mature ORM, SQLite to PostgreSQL migration path
- **jdatetime** - Persian (Jalali) date library for Iranian users
- **openpyxl/reportlab** - Excel/PDF generation with Persian font support

---

## 6. Project File Structure

```
hesab/
├── .dockerignore, .env, .gitignore

---

## 7. Database Schema & Data Models

### 7.1 Entity-Relationship Diagram

```
User(1) ---< Transaction(N)  : user_id FK
User(1) ---< Customer(N)      : user_id FK
User(1) ---< CardInfo(N)      : user_id FK
Customer(1) ---< Transaction(N) : customer_id FK
Customer(1) ---< CardInfo(N)    : customer_id FK
Transaction(1) ---< Reminder(N) : transaction_id FK
User(1) ---< Reminder(N)       : user_id FK
User(1) ---< Backup(N)         : user_id FK
```

### 7.2 Table: `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-inc | Internal ID |
| telegram_id | BigInteger | UNIQUE, NOT NULL, INDEX | Telegram user ID |
| username | String(255) | NULLABLE | Telegram @username |
| first_name | String(255) | NULLABLE | First name |
| last_name | String(255) | NULLABLE | Last name |
| is_admin | Boolean | DEFAULT FALSE | Admin flag |
| is_active | Boolean | DEFAULT TRUE | Active status |
| created_at | DateTime | DEFAULT utcnow | Created timestamp |
| updated_at | DateTime | onupdate=utcnow | Updated timestamp |

### 7.3 Table: `transactions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-inc | Internal ID |
| user_id | Integer | FK->users.id, NOT NULL, INDEX | Owner |
| transaction_type | String(50) | NOT NULL, INDEX | income/expense/debt/receivable |
| amount | Float | NOT NULL | Amount in Tomans |
| description | Text | NULLABLE | Description |
| category | String(255) | NULLABLE | Category |
| party_name | String(255) | NULLABLE | Counterparty (debt/receivable) |
| customer_id | Integer | FK->customers.id, NULLABLE | Linked customer |
| jalali_date | String(20) | NOT NULL | YYYY/MM/DD |
| jalali_time | String(20) | NOT NULL | HH:MM:SS |
| jalali_full | String(50) | NOT NULL | Combined datetime |
| due_jalali_date | String(20) | NULLABLE | Due date |
| due_jalali_time | String(20) | NULLABLE | Due time |
| photo_path | String(500) | NULLABLE | Photo file path |
| created_at | DateTime | DEFAULT utcnow | UTC timestamp |
| is_settled | Boolean | DEFAULT FALSE | Settled status |
| settled_at | DateTime | NULLABLE | When settled |

### 7.4 Table: `customers`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-inc | Internal ID |
| user_id | Integer | FK->users.id, NOT NULL, INDEX | Owner |
| full_name | String(255) | NOT NULL | Customer name |
| phone | String(50) | NULLABLE | Phone number |
| address | Text | NULLABLE | Address |
| notes | Text | NULLABLE | Notes |
| total_debt | Float | DEFAULT 0.0 | Cached total debt |
| total_receivable | Float | DEFAULT 0.0 | Cached total receivable |
| created_at | DateTime | DEFAULT utcnow | Created |
| updated_at | DateTime | onupdate=utcnow | Updated |

### 7.5 Table: `card_info`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-inc | Internal ID |
| user_id | Integer | FK->users.id, NOT NULL, INDEX | Owner |
| name | String(255) | NOT NULL | Associated name |
| customer_id | Integer | FK->customers.id, NULLABLE | Linked customer |
| card_number | String(16) | NULLABLE | 16-digit card |
| sheba | String(26) | NULLABLE | IBAN (24 digits, no IR) |
| created_at | DateTime | DEFAULT utcnow | Created |
| updated_at | DateTime | onupdate=utcnow | Updated |

### 7.6 Table: `reminders`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-inc | Internal ID |
| user_id | Integer | FK->users.id, NOT NULL, INDEX | Owner |
| transaction_id | Integer | FK->transactions.id, NULLABLE | Linked txn |
| reminder_type | String(50) | NOT NULL | debt/receivable/custom |
| title | String(255) | NOT NULL | Title |
| message | Text | NULLABLE | Message |
| reminder_jalali_date | String(20) | NOT NULL | Date |
| reminder_time | String(20) | NULLABLE | Time |
| is_sent | Boolean | DEFAULT FALSE | Sent status |
| sent_at | DateTime | NULLABLE | When sent |
| created_at | DateTime | DEFAULT utcnow | Created |

### 7.7 Table: `backups`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto-inc | Internal ID |
| user_id | Integer | FK->users.id, NOT NULL | Creator |
| filename | String(255) | NOT NULL | Backup filename |
| file_size | BigInteger | DEFAULT 0 | Size in bytes |
| jalali_date | String(20) | NOT NULL | Backup date |
| jalali_time | String(20) | NULLABLE | Backup time |
| created_at | DateTime | DEFAULT utcnow | Created |

├── Dockerfile, README.md, railway.json
├── requirements.txt, start_bot.sh

---

## 8. Module-by-Module Architecture

### 8.1 Module Dependency Graph

```
config.py ←── .env (via python-dotenv)
logger.py ←── config.py
messages.py (standalone - no deps)
jdatetime_helper.py ←── config.py
models.py ←── config.py
repository.py ←── models.py
markups.py ←── aiogram only
export_service.py ←── config, logger, jdatetime_helper, models, openpyxl/reportlab
main_handler.py ←── ALL modules above + aiogram
main.py ←── config, logger, main_handler
```

### 8.2 Module Responsibilities

| Module | Role | Key Exports |
|--------|------|-------------|
| main.py | Entry point, init, polling | `main()` |
| config.py | Env config | `Settings` class, `settings` singleton |
| models.py | ORM models | `User`, `Transaction`, `Customer`, `Reminder`, `CardInfo`, `Backup`, `init_database()` |
| repository.py | DAO layer | 6 Repository classes with static CRUD methods |
| main_handler.py | All Telegram logic | `router`, 17 FSM classes, 50+ handlers |
| markups.py | Keyboard builders | 20+ keyboard factory functions |
| export_service.py | File generation | `export_transactions_excel()`, `export_transactions_pdf()` |
| jdatetime_helper.py | Persian date utils | `get_jalali_date()`, `format_amount()`, `get_current_jalali_period()` |
| logger.py | Logging | `logger` singleton, `setup_logger()` |
| messages.py | UI strings | 100+ Persian string constants |

---

## 9. Entry Points & Startup Sequence

### 9.1 Sequence Diagram

```
1. python main.py
2. load_dotenv()                 # Read .env
3. setup_logger()                # Create logs/ dir, file+console handlers
4. init_database()               # Create data/ dir, SQLite engine, all tables
5. Create Bot(token)             # aiogram Bot with HTML parse_mode
6. Create Dispatcher(storage)    # MemoryStorage
7. dp.include_router(router)     # Register all handlers
8. Log startup info

---

## 11. Conversation Flows (FSM)

### 11.1 FSM States

```python
class IncomeForm:     amount -> description -> category -> photo -> confirm
class ExpenseForm:    amount -> description -> category -> photo -> confirm
class DebtForm:       amount -> party -> description -> due_date -> photo -> confirm
class ReceivableForm: amount -> party -> description -> due_date -> photo -> confirm
class CustomerForm:   name -> phone -> address -> notes -> confirm
class CustomerEditForm:   select -> name -> phone -> address -> notes
class CustomerDeleteForm: select -> confirm
class SearchForm:         query -> transaction_type
class CustomerSearchForm: query
class DebtEditForm:       edit_id -> amount|party|description|due_date -> confirm
class ReceivableEditForm: edit_id -> amount|party|description|due_date -> confirm
class CardForm:     name_choice -> name_manual|name_customer_select -> card_number -> sheba -> confirm
class CardEditForm: select -> field -> value -> confirm
class CardDeleteForm: select -> confirm
class CardSearchForm: query
```

### 11.2 Income/Expense Registration Flow

```
[Main Menu] -> Click "💰 ثبت درآمد"
-> Enter amount (numeric validation)
-> Enter description
-> Select category (from predefined list)
-> Optional photo (send photo or skip)
-> [Save transaction] -> Confirmation message
```

### 11.3 Debt/Receivable Registration Flow

```
[Main Menu] -> Click "📋 ثبت بدهی"
-> Enter amount (numeric validation)
-> Select party (customer list or manual entry)
-> Enter description
-> Enter due date (today button or YYYY/MM/DD)
-> Optional photo (send photo or skip)
-> Show summary -> [✅ تأیید] or [❌ رد]
-> If confirmed: Save transaction, show success
```

### 11.4 Customer Registration Flow

```
[Customer Menu] -> Click "👤 افزودن مشتری"
-> Enter name (required)
-> Enter phone (optional, skip available)
-> Enter address (optional, skip available)
-> Enter notes (optional, skip available)
-> [Save customer] -> Confirmation message
```

### 11.5 Card/IBAN Registration Flow

```
[Card Menu] -> Click "➕ ثبت جدید"
-> Choose name method: [✏️ ورود دستی] or [👥 انتخاب از مشتریان]
-> Enter name or select customer
-> Enter card number (16 digits, optional with skip)
-> Enter IBAN (24 digits, optional with skip)
-> Show confirmation -> [✅ تأیید] or [❌ رد]
-> Duplicate check -> Save or reject with message
```

### 11.6 Debt/Receivable Edit Flow

```
[Debt List] -> Click edit on an item
-> Show current values with field selection buttons
-> [💰 مبلغ] [👤 طرف حساب] [📝 توضیحات] [📅 سررسید] [✅ تأیید و ذخیره]
-> Select field -> Enter new value (or 0/- to keep)
-> Return to field selection
-> Click save -> Show summary -> Confirm
-> Update database -> Success message
```

### 11.7 Search Flow

```
[Main Menu] -> Click "🔍 جستجو"
-> Enter search query
-> Select transaction type filter (inline buttons)
-> Show results (up to 10, with count of more)
```

---

## 12. Command Handlers

| Command | Function | Description |
|---------|----------|-------------|
| `/start` | `cmd_start()` | Welcome, auto-register, show main menu |
| `/menu` | `cmd_menu()` | Clear FSM, show main menu |
| `/help` | (via menu) | Show help text |
| `/dashboard` | `show_dashboard()` | Show financial dashboard |
| `/report` | `show_report_menu()` | Show report period menu |
| `/backup` | `backup_menu_handler()` | Show backup options |
| `/search` | `search_start()` | Start search flow |

### Text Button Handlers (F.text)

| Button Text | Handler | Description |
|-------------|---------|-------------|
| 💰 ثبت درآمد | `income_start()` | Start income registration |
| 💸 ثبت هزینه | `expense_start()` | Start expense registration |
| 📋 ثبت بدهی | `debt_start()` | Start debt registration |
| 📌 ثبت طلب | `receivable_start()` | Start receivable registration |
| 📋 لیست بدهی‌ها | `debt_list()` | Show debt list with actions |
| 📌 لیست طلب‌ها | `receivable_list()` | Show receivable list with actions |
| 👥 مدیریت مشتریان | `customer_management()` | Show customer menu |
| 📊 داشبورد مالی | `show_dashboard()` | Show dashboard |
| 💳 ثبت شماره کارت و شبا | `card_menu_handler()` | Show card menu |
| 📈 گزارش‌های مالی | `show_report_menu()` | Show report menu |
| 🔍 جستجو | `search_start()` | Start search |
| 💾 پشتیبان‌گیری | `backup_menu_handler()` | Show backup menu |
| 🔙 بازگشت به منو | `cmd_menu()` | Return to main menu |
| ❌ انصراف | (inline in forms) | Cancel and return to menu |
| ⏭️ رد کردن/بدون عکس | (inline in forms) | Skip optional field |

---

## 13. Callback Handlers & Routing

### 13.1 Inline Callback Data Map

| Callback Pattern | Handler | Module |
|------------------|---------|--------|
| `confirm_yes`, `confirm_no` | Various FSM confirm handlers | main_handler |
| `export_excel`, `export_pdf` | `handle_export()` | main_handler |
| `backup_create`, `backup_restore`, `backup_list` | Respective handlers | main_handler |
| `search_type_*` | `search_type_selected()` | main_handler |
| `edit_customer:{id}`, `delete_customer:{id}` | Customer select handlers | main_handler |
| `edit_debt:{id}`, `edit_recv:{id}` | Txn edit start handlers | main_handler |
| `edit_field:amount|party|description|due_date|save` | `edit_field_selected()` | main_handler |
| `debt_delete:{id}`, `recv_delete:{id}` | Delete confirm handlers | main_handler |
| `card_edit:{id}`, `card_delete:{id}` | Card action handlers | main_handler |
| `card_edit_field:{id}:field` | `card_edit_field_handler()` | main_handler |
| `copy_card:{id}`, `copy_sheba:{id}`, `copy_sms:{id}` | `card_copy_callback()` | main_handler |
| `{prefix}_page_{n}` | Pagination (prepared) | markups.py |

### 13.2 Routing Priority

1. Command handlers (`/start`, `/menu`, etc.)
2. FSM State handlers (user in a specific state)
3. Text message handlers (F.text matching)
4. Callback query handlers (F.data patterns)
5. Fallback handler (catch-all for unknown messages)

9. await dp.start_polling(bot)   # Begin event loop
```

### 9.2 Critical Initialization Details

- **Bot**: `DefaultBotProperties(parse_mode=ParseMode.HTML)`
- **Dispatcher**: `MemoryStorage()` (in-memory FSM state)
- **Database**: SQLite with `check_same_thread=False`, `StaticPool`, `echo=False`
- **Tables**: Auto-created via `Base.metadata.create_all(engine)`
- **Router**: Single router with all handlers

---

## 10. Menu Hierarchy & Navigation

### 10.1 Menu Tree

```
Main Menu
├── 💰 ثبت درآمد                    (Income)
├── 💸 ثبت هزینه                    (Expense)
├── 📋 ثبت بدهی                     (Debt)
├── 📌 ثبت طلب                      (Receivable)
├── 📋 لیست بدهی‌ها                  (Debt List)
├── 📌 لیست طلب‌ها                   (Receivable List)
├── 👥 مدیریت مشتریان                (Customer Menu)
│   ├── 👤 افزودن مشتری
│   ├── ✏️ ویرایش مشتری
│   ├── 🗑 حذف مشتری
│   ├── 🔍 جستجوی مشتری
│   └── 📋 لیست مشتریان
├── 📊 داشبورد مالی                  (Dashboard)
├── 💳 ثبت شماره کارت و شبا          (Card Menu)
│   ├── ➕ ثبت جدید
│   ├── 📋 لیست شماره کارت‌ها
│   └── 🔍 جستجوی کارت
├── 📈 گزارش‌های مالی                (Report Menu)
│   ├── 📅 گزارش روزانه
│   ├── 📅 گزارش هفتگی
│   ├── 📅 گزارش ماهانه
│   └── 📅 گزارش سالانه
├── 🔍 جستجو                        (Search)
├── 💾 پشتیبان‌گیری                  (Backup)
└── ⚙️ تنظیمات                      (Settings - placeholder)
```

### 10.2 Navigation Rules

- Main menu: `/start`, `/menu`, or "🔙 بازگشت به منو"
- Cancel: "❌ انصراف" clears FSM, returns to main menu
- Back: "🔙 بازگشت" goes to previous step in multi-step forms
- Keyboard changes contextually (categories, customer list) based on current step

├── hesab/
│   ├── main.py                     # Entry point
│   ├── migrate_add_*.py            # DB migration scripts
│   ├── app/
│   │   ├── config.py               # Settings from env
│   │   ├── database/
│   │   │   ├── models.py           # SQLAlchemy models
│   │   │   └── repository.py       # CRUD repositories
│   │   ├── handlers/
│   │   │   └── main_handler.py     # All Telegram handlers
│   │   ├── keyboards/
│   │   │   └── markups.py          # Keyboard generators
│   │   ├── middleware/             # Placeholder
│   │   ├── services/
│   │   │   └── export_service.py   # Excel/PDF export
│   │   └── utils/
│   │       ├── jdatetime_helper.py # Persian date utils
│   │       ├── logger.py           # Logging setup
│   │       └── messages.py         # All Persian strings
│   ├── data/                       # SQLite files
│   ├── logs/                       # Log files
│   ├── backups/                    # DB backups
│   ├── exports/                    # Excel/PDF files
│   └── uploads/                    # Photos
├── data/, logs/, backups/, exports/, uploads/
```

### FR12: Search
- FR12.1: Search transactions by text (amount, description, category, party_name)
- FR12.2: Filter by transaction type via inline keyboard
- FR12.3: Show up to 10 results with count of additional results

---

## 4. Non-Functional Requirements

### NFR1: Performance
- NFR1.1: Bot responds within 2 seconds for standard operations
- NFR1.2: Database queries return within 500ms
- NFR1.3: File ops complete within 5 seconds

### NFR2: Reliability
- NFR2.1: Bot runs continuously with minimal downtime
- NFR2.2: DB sessions closed in finally blocks
- NFR2.3: Errors logged, user gets friendly message

### NFR3: Security
- NFR3.1: Bot token in env var only
- NFR3.2: SQLite file not publicly accessible
- NFR3.3: User data isolated by user_id

### NFR4: Usability
- NFR4.1: Full Persian language with RTL
- NFR4.2: Jalali dates with Persian month names
- NFR4.3: Persian digit formatting (۰-۹)
- NFR4.4: Cancel/back at every step

### NFR5: Maintainability
- NFR5.1: Modular architecture
- NFR5.2: All strings in messages.py
- NFR5.3: Config in config.py
- NFR5.4: Logger in logger.py

### NFR6: Portability
- NFR6.1: Python 3.13+
- NFR6.2: SQLite -> PostgreSQL upgrade path
- NFR6.3: Docker support
- NFR6.4: Railway.app deployment

### NFR7: Data Integrity
- NFR7.1: Amount validation (positive only)
- NFR7.2: Card number (16 digits)
- NFR7.3: IBAN (24 digits, no IR prefix)
- NFR7.4: Date format YYYY/MM/DD
- NFR7.5: Duplicate detection for card/IBAN
