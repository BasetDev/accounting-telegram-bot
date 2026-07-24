# Application Navigation Structure

```
══════════════════════════════════════════════════════════════
PROJECT STRUCTURE
══════════════════════════════════════════════════════════════

hesab/
├── main.py                          # Entry point (aiogram 3.x polling)
├── .env                             # Configuration (BOT_TOKEN, MONGO_URI, etc.)
├── APP_STRUCTURE.md                 # This file
├── hesab/
│   ├── app/
│   │   ├── config.py                # Settings (env vars, paths)
│   │   ├── database/
│   │   │   ├── models.py            # MongoDB connection, document factories, indexes, auto-increment counters
│   │   │   └── repository.py        # Repository pattern (User, Transaction, Payment, Customer, Card, Reminder, Backup)
│   │   ├── handlers/
│   │   │   └── main_handler.py      # All handlers (~10,700 lines, single router), FSM states, middleware, caches
│   │   ├── keyboards/
│   │   │   └── markups.py           # All keyboards (Inline + Reply)
│   │   ├── services/
│   │   │   └── export_service.py    # Excel/PDF export (openpyxl, reportlab)
│   │   ├── utils/
│   │   │   ├── messages.py          # All message templates (Persian)
│   │   │   ├── logger.py            # Logging (RotatingFileHandler + console)
│   │   │   └── jdatetime_helper.py  # Jalali date utilities, amount formatting, number-to-words
│   │   └── middleware/
│   │       └── __init__.py          # (empty; LoggingMiddleware lives in main_handler.py)
│   ├── uploads/                     # Photo attachments
│   ├── exports/                     # Generated Excel/PDF files
│   ├── backups/                     # Database backups
│   ├── logs/                        # Log files
│   └── data/                        # Local data (if any)
├── test_hierarchy.py                # Test script for debt/receivable hierarchy
└── start_bot.sh                     # Bot startup script

══════════════════════════════════════════════════════════════
TECH STACK
══════════════════════════════════════════════════════════════

- Framework: aiogram 3.x (async, Router-based)
- Database: MongoDB (pymongo, Atlas or local)
- Date: jdatetime (Jalali/Persian calendar)
- Export: openpyxl (Excel), reportlab (PDF)
- FSM: aiogram FSM (MemoryStorage)

══════════════════════════════════════════════════════════════
MONGODB COLLECTIONS
══════════════════════════════════════════════════════════════

- users              → User profiles (telegram_id, username, etc.)
- transactions       → All financial transactions (income, expense, debt, receivable)
- payments           → Payment records (debt_payment, receivable_payment)
- customers          → Customer database (name, phone, address, notes)
- card_info          → Card/IBAN information (card_number, sheba, bank_name)
- reminders          → Due date reminders
- backups            → Backup metadata
- counters           → Auto-increment ID counters (sequence per collection)

══════════════════════════════════════════════════════════════
REPOSITORY LAYER (High-Level Methods)
══════════════════════════════════════════════════════════════

UserRepository
├── get_or_create(telegram_id, username, first_name, last_name)
├── get_by_telegram_id(telegram_id)
├── get_by_id(user_id)
├── make_admin(telegram_id)
└── get_all_users()

TransactionRepository
├── create(user_id, transaction_type, amount, jalali_date, jalali_time, jalali_full, ...)
├── get_by_id(txn_id)
├── get_by_user(user_id, transaction_type, limit, offset)
├── get_active(user_id, transaction_type, limit)         → non-settled
├── get_settled(user_id, transaction_type, limit)         → settled
├── get_with_payments(user_id, transaction_type, limit)   → has payments OR settled
├── get_overdue(user_id, transaction_type, today_jalali, limit)
├── get_due_today(user_id, transaction_type, today_jalali, limit)
├── get_due_this_week(user_id, transaction_type, today_jalali, week_end_jalali, limit)
├── get_by_date_range(user_id, start_date, end_date, transaction_type)
├── get_by_customer(customer_id)
├── get_summary(user_id, transaction_type)                → aggregate sum
├── get_total_by_type(user_id)                            → dict of totals per type
├── update(txn_id, **kwargs)
├── settle_transaction(txn_id)                            → set is_settled=True
├── delete(txn_id)
└── search(user_id, query_text, transaction_type, ...)

CustomerRepository
├── create(user_id, full_name, phone, address, notes)
├── get_by_id(customer_id)
├── get_by_user(user_id)
├── search(user_id, query)
├── update(customer_id, full_name, phone, address, notes)
├── delete(customer_id)
└── update_financial_summary(customer_id)                 → recalc total_debt/total_receivable

PaymentRepository
├── create(transaction_id, user_id, amount, payment_type, jalali_date, ...)
├── get_by_transaction(transaction_id)
├── get_total_paid(transaction_id)
├── get_remaining(transaction_id, original_amount)
├── get_by_user(user_id, limit)
└── get_by_user_and_type(user_id, payment_type, limit)

CardInfoRepository
├── create(user_id, name, card_number, sheba, customer_id, bank_name)
├── get_by_id(card_id)
├── get_by_user(user_id)
├── update(card_id, name, card_number, sheba, customer_id, bank_name)
├── delete(card_id)
└── search(user_id, query)                                → by name/card_number/sheba

ReminderRepository
├── create(user_id, reminder_type, title, reminder_jalali_date, ...)
├── get_pending(jalali_date)
└── mark_sent(reminder_id)

BackupRepository
├── create(user_id, filename, file_size, jalali_date, jalali_time)
└── get_recent(limit)

══════════════════════════════════════════════════════════════
BOT ENTRY POINTS
══════════════════════════════════════════════════════════════

🤖 COMMANDS
├── /start                    → WELCOME message → Main Menu
├── /menu                     → Main Menu
├── /help                     → HELP message → Main Menu
├── /dashboard                → Dashboard screen
├── /report                   → Reports Menu
├── /backup                   → Backup Menu
└── /search                   → Search Flow

══════════════════════════════════════════════════════════════
📋 MAIN MENU (ReplyKeyboardMarkup)
══════════════════════════════════════════════════════════════

├── 💰 ثبت درآمد (Register Income) ───────────────────────── [IncomeForm FSM]
│   ├── Step 1: Amount
│   │   ├── [❌ انصراف] → Cancel → Main Menu
│   │   └── (valid number) → Step 2
│   ├── Step 2: Description
│   │   ├── [❌ انصراف] → Cancel → Main Menu
│   │   ├── [🔙 بازگشت به منو] → Main Menu
│   │   └── (text) → Step 3
│   ├── Step 3: Category (ReplyKeyboard)
│   │   ├── فروش محصول
│   │   ├── فروش خدمات
│   │   ├── حقوق
│   │   ├── سرمایه‌گذاری
│   │   ├── پروژه
│   │   ├── مشاوره
│   │   ├── فروش آنلاین
│   │   ├── سایر درآمدها
│   │   ├── [❌ انصراف] → Cancel → Main Menu
│   │   ├── [🔙 بازگشت] → Step 2 (Description)
│   │   └── (category selected) → Step 4
│   ├── Step 4: Photo (optional)
│   │   ├── [⏭️ بدون عکس] → Skip photo → Save → Main Menu
│   │   ├── [❌ انصراف] → Cancel → Main Menu
│   │   ├── [🔙 بازگشت به منو] → Main Menu
│   │   └── (send photo) → Save → Main Menu
│   └── ✅ Confirmation message → Main Menu
│
├── 💸 ثبت هزینه (Register Expense) ──────────────────────── [ExpenseForm FSM]
│   ├── Step 1: Amount
│   │   ├── [❌ انصراف] → Cancel → Main Menu
│   │   └── (valid number) → Step 2
│   ├── Step 2: Description
│   │   ├── [❌ انصراف] → Cancel → Main Menu
│   │   ├── [🔙 بازگشت به منو] → Main Menu
│   │   └── (text) → Step 3
│   ├── Step 3: Category (ReplyKeyboard)
│   │   ├── اجاره
│   │   ├── حقوق کارکنان
│   │   ├── خرید کالا
│   │   ├── حمل و نقل
│   │   ├── تبلیغات
│   │   ├── خدمات
│   │   ├── قبوض
│   │   ├── تعمیرات
│   │   ├── مواد اولیه
│   │   ├── مالیات
│   │   ├── بیمه
│   │   ├── سایر هزینه‌ها
│   │   ├── [❌ انصراف] → Cancel → Main Menu
│   │   ├── [🔙 بازگشت] → Step 2 (Description)
│   │   └── (category selected) → Step 4
│   ├── Step 4: Photo (optional)
│   │   ├── [⏭️ بدون عکس] → Skip → Save → Main Menu
│   │   ├── [❌ انصراف] → Cancel → Main Menu
│   │   ├── [🔙 بازگشت به منو] → Main Menu
│   │   └── (send photo) → Save → Main Menu
│   └── ✅ Confirmation message → Main Menu
│
├── 💳 بدهی‌ها (Debts) ────────────────────────────────────── [Debt Submenu - Inline]
│   │
│   │  ┌─ Debt Submenu (InlineKeyboardMarkup) ─────────────────────┐
│   ├──┤  🟡 بدهی‌های فعال         [debt_active]                    │
│   │  │  🔴 سررسید گذشته          [debt_overdue]                   │
│   │  │  🟢 تسویه شده             [debt_settled_cat]               │
│   │  │  ⏰ سررسید امروز          [debt_due_today]                 │
│   │  │  📅 سررسید این هفته       [debt_due_week]                  │
│   │  │  📋 همه بدهی‌ها            [debt_all_cat]                   │
│   │  │  💳 پرداخت بدهی           [debt_pay_cat]                   │
│   │  │  📊 تسویه‌ها               [settlement_debt]                │
│   │  │  📜 پرداخت‌های انجام شده   [debt_view_payments]            │
│   │  │  📊 گزارش بدهی‌ها          [debt_reports]                   │
│   │  │  📋 ثبت بدهی جدید         [debt_register]                  │
│   │  └────────────────────────────────────────────────────────────┘
│   │
│   ├── 🟡 بدهی‌های فعال → 3-level hierarchical view:
│   │   │
│   │   ├── Level 1 — Customer Overview (inline) ── [debt_active]
│   │   │   ├── 📊 خلاصه کلی (Overall Summary)
│   │   │   │   ├── تعداد مشتریان
│   │   │   │   ├── تعداد بدهی‌ها
│   │   │   │   ├── مجموع بدهی‌ها
│   │   │   │   └── مجموع باقی‌مانده
│   │   │   ├── ────────────────────
│   │   │   ├── Per-customer blocks:
│   │   │   │   ├── 👤 {party}
│   │   │   │   │   ├── تعداد بدهی‌ها
│   │   │   │   │   ├── مجموع
│   │   │   │   │   └── باقی‌مانده / ✅ تسویه شده
│   │   │   ├── [▶ مشاهده بدهی‌های {party}]  [debt_cust_detail:{key}:{party}]  (per customer)
│   │   │   └── [🔙 بازگشت]                [debt_group_back] → Debt Submenu
│   │   │
│   │   ├── Level 2 — Customer Debt List (inline) ── [debt_cust_detail:{key}:{party}]
│   │   │   ├── 💳 {party} (customer summary)
│   │   │   ├── 📋 #{id} | {amount} تومان  [debt_item_detail:{key}:{party}:{id}]  (per debt, due-status emoji)
│   │   │   └── [🔙 بازگشت به مشتریان]     [debt_group_back] → Debt Submenu
│   │   │
│   │   └── Level 3 — Debt Detail (inline) ── [debt_item_detail:{key}:{party}:{id}]
│   │       ├── Full debt info (ID, party, category, amount, remaining, description, due date, card, sheba, bank)
│   │       └── Per-item inline buttons (dynamic):
│   │           ├── [📸 عکس]     [view_photo:{txn_id}]       (if photo exists)
│   │           ├── [📸 رسید پرداخت]  [view_payment_photo:{txn_id}]  (if payment receipt exists)
│   │           ├── [📩 پیامک]   [debt_sms:{txn_id}]         (if payment info exists)
│   │           ├── [💳 پرداخت]  [quick_pay_debt:{txn_id}]   (if remaining > 0)
│   │           ├── [✏️ ویرایش]  [edit_debt:{txn_id}]
│   │           ├── [🗑 حذف]     [delete_debt:{txn_id}]
│   │           ├── [📜 تاریخچه پرداخت]  [debt_payment_history:{txn_id}]
│   │           └── [🔙 بازگشت]           [debt_detail_back:{key}:{party}] → Level 2
│   │
│   ├── 🔴 سررسید گذشته → List of overdue debts (same per-item buttons)
│   │
│   ├── 🟢 تسویه شده → Category Filter (inline) ── [debt_settled_cat]
│   │   ├── 📋 همه دسته‌ها          [debt_settled_cat:all]
│   │   ├── 🏢 کسب‌وکار            [debt_settled_cat:🏢 کسب‌وکار]
│   │   │   └── Subcategory Filter:
│   │   │       ├── 📋 همه زیرمجموعه‌ها   [debt_settled_sub:all]
│   │   │       ├── تأمین‌کنندگان          [debt_settled_sub:تأمین‌کنندگان]
│   │   │       ├── خرید ضایعات            [debt_settled_sub:خرید ضایعات]
│   │   │       ├── حمل و نقل              [debt_settled_sub:حمل و نقل]
│   │   │       ├── حقوق کارکنان           [debt_settled_sub:حقوق کارکنان]
│   │   │       ├── مالیات                  [debt_settled_sub:مالیات]
│   │   │       ├── چک‌های صادره           [debt_settled_sub:چک‌های صادره]
│   │   │       ├── سایر                    [debt_settled_sub:سایر]
│   │   │       └── [🔙 بازگشت]            → back to category filter
│   │   ├── 👤 شخصی                [debt_settled_cat:👤 شخصی]
│   │   │   └── Subcategory Filter:
│   │   │       ├── 📋 همه زیرمجموعه‌ها   [debt_settled_sub:all]
│   │   │       ├── وام شخصی               [debt_settled_sub:وام شخصی]
│   │   │       ├── خانواده                 [debt_settled_sub:خانواده]
│   │   │       ├── دوستان                  [debt_settled_sub:دوستان]
│   │   │       ├── سایر                    [debt_settled_sub:سایر]
│   │   │       └── [🔙 بازگشت]            → back to category filter
│   │   ├── سایر                   [debt_settled_cat:سایر] → direct list
│   │   └── [🔙 بازگشت]           → Debt Submenu
│   │
│   │   Settled debt items → 3-level hierarchy:
│   │   ├── Level 1: Customer list [ds_cust:{id}]
│   │   ├── Level 2: Debt list per customer [ds_item:{txn_id}]
│   │   └── Level 3: Debt detail with payment history
│   │
│   ├── ⏰ سررسید امروز → List of today's debts (same per-item buttons)
│   │
│   ├── 📅 سررسید این هفته → List of this week's debts (same per-item buttons)
│   │
│   ├── 📋 همه بدهی‌ها → Category Filter (inline) ── [debt_all_cat]
│   │   ├── 📋 همه دسته‌ها          [debt_all_cat:all]
│   │   ├── 🏢 کسب‌وکار            [debt_all_cat:🏢 کسب‌وکار]
│   │   │   └── Subcategory Filter (same structure as settled)
│   │   ├── 👤 شخصی                [debt_all_cat:👤 شخصی]
│   │   │   └── Subcategory Filter (same structure as settled)
│   │   ├── سایر                   [debt_all_cat:سایر] → direct list
│   │   └── [🔙 بازگشت]           → Debt Submenu
│   │
│   │   All debts → 3-level hierarchy via [debt_all_cust:{id}]
│   │
│   ├── 💳 پرداخت بدهی → Category Filter (inline) ── [debt_pay_cat]
│   │   ├── 📋 همه دسته‌ها          [debt_pay_cat:all]
│   │   │   └── Subcategory Filter (same structure)
│   │   │       └── Customer List ── [debt_pay_cust:{id}]
│   │   │           └── PaymentForm FSM (see Payment Workflow below)
│   │   ├── 🏢 کسب‌وکار            [debt_pay_cat:🏢 کسب‌وکار]
│   │   │   └── Subcategory Filter → Customer List → PaymentForm FSM
│   │   ├── 👤 شخصی                [debt_pay_cat:👤 شخصی]
│   │   │   └── Subcategory Filter → Customer List → PaymentForm FSM
│   │   ├── سایر                   [debt_pay_cat:سایر] → Customer List → PaymentForm FSM
│   │   └── [🔙 بازگشت]           → Debt Submenu
│   │
│   ├── 📊 تسویه‌ها → Settlement view (inline) ── [settlement_debt]
│   │   ├── Level 1 — Customer Overview
│   │   │   ├── Summary (total amount, total paid, remaining, settlement rate)
│   │   │   ├── 👤 {party} | {paid}/{total} تومان ({pct}%)  [stl_cust:{short_id}]  (per customer)
│   │   │   └── [🔙 بازگشت]  [debt_view_payments] → Debt Submenu
│   │   ├── Level 2 — Customer Settlement List
│   │   │   ├── Customer summary
│   │   │   ├── 🟢/🟡 #{id} | {paid} از {total} تومان ({pct}%)  [stl_item:{txn_id}]  (per debt)
│   │   │   └── [🔙 بازگشت به مشتریان]  [stl_bc:{cache_key}] → Level 1
│   │   └── Level 3 — Settlement Detail
│   │       ├── Full debt info + payment history
│   │       ├── [📸 عکس] / [📸 رسید پرداخت]  (if photos exist)
│   │       ├── [📜 تاریخچه پرداخت]
│   │       └── [🔙 بازگشت به لیست]  [stl_bi:{cache_key}:{safe_party}] → Level 2
│   │
│   ├── 📜 پرداخت‌های انجام شده → 3-level payment history ── [debt_view_payments]
│   │   ├── Level 1 — Customer List
│   │   │   ├── Summary (total payments, payment count, customer count)
│   │   │   ├── 👤 {party} | {total_paid} تومان ({count} پرداخت)  [dvp_cust:{short_id}]  (per customer)
│   │   │   └── [🔙 بازگشت به منوی بدهی‌ها]  [debt_view_payments_back] → Debt Submenu
│   │   ├── Level 2 — Customer Payment List
│   │   │   ├── Customer summary
│   │   │   ├── 🟢/🟡 #{txn_id} | {paid} از {total} تومان ({pct}%)  [dvp_detail:{txn_id}]  (per debt)
│   │   │   │   └── Per-payment details (amount, date, description, photo indicator)
│   │   │   └── [🔙 بازگشت به مشتریان]  [dvp_bc:{cache_key}] → Level 1
│   │   └── Level 3 — Payment Detail
│   │       ├── Full debt info + payment history
│   │       ├── [📸 عکس] / [📸 رسید پرداخت]  (if photos exist)
│   │       ├── [📩 پیامک]  (if payment info exists)
│   │       ├── [✏️ ویرایش]  [edit_debt:{txn_id}]
│   │       ├── [📜 تاریخچه پرداخت]
│   │       └── [🔙 بازگشت به لیست]  [dvp_bi:{cache_key}:{safe_party}] → Level 2
│   │
│   ├── 📊 گزارش بدهی‌ها → Reports submenu (inline) ── [debt_reports]
│   │   │  ┌─ Debt Reports Submenu (InlineKeyboardMarkup) ────────────┐
│   │   │  │  📊 گزارش کلی            [debt_rpt_summary]               │
│   │   │  │  ⏳ بدهی‌های فعال        [debt_rpt_active]                │
│   │   │  │  ✅ تسویه شده            [debt_rpt_settled]               │
│   │   │  │  🔴 سررسید گذشته         [debt_rpt_overdue]               │
│   │   │  │  ⏰ سررسید امروز         [debt_rpt_due_today]             │
│   │   │  │  📅 سررسید این هفته      [debt_rpt_due_week]              │
│   │   │  │  👥 بر اساس مشتری        [debt_rpt_by_customer]           │
│   │   │  │  🏷 بر اساس دسته‌بندی     [debt_rpt_by_category]           │
│   │   │  │  💰 پرداخت‌ها             [debt_rpt_payments]              │
│   │   │  │  📊 مانده بدهی           [debt_rpt_remaining]             │
│   │   │  │  📅 گزارش روزانه          [debt_rpt_daily]                 │
│   │   │  │  📅 گزارش هفتگی          [debt_rpt_weekly]                │
│   │   │  │  📅 گزارش ماهانه         [debt_rpt_monthly]               │
│   │   │  │  📅 گزارش سالانه         [debt_rpt_yearly]                │
│   │   │  │  🔙 بازگشت به منوی بدهی‌ها  [debt_rpt_back]               │
│   │   │  └───────────────────────────────────────────────────────────┘
│   │   │
│   │   ├── Each report → Report text + Export Menu (inline)
│   │   │   ├── 📊 Excel    [debt_rpt_export_excel:{report_type}] → file download
│   │   │   ├── 📄 PDF      [debt_rpt_export_pdf:{report_type}]  → file download
│   │   │   └── 🔙 بازگشت به منوی گزارش‌ها  [debt_rpt_menu] → Reports submenu
│   │   │
│   │   └── [🔙 بازگشت]  [debt_rpt_back] → Debt Submenu
│   │
│   └── 📋 ثبت بدهی جدید ───────────────────────────────── [DebtForm FSM]
│       ├── Step 1: Category (inline)
│       │   ├── 🏢 کسب‌وکار           [debt_cat:🏢 کسب‌وکار]
│       │   │   └── Step 1b: Subcategory (inline)
│       │   │       ├── تأمین‌کنندگان       [debt_sub:تأمین‌کنندگان]
│       │   │       ├── خرید ضایعات         [debt_sub:خرید ضایعات]
│       │   │       ├── حمل و نقل           [debt_sub:حمل و نقل]
│       │   │       ├── حقوق کارکنان        [debt_sub:حقوق کارکنان]
│       │   │       ├── مالیات               [debt_sub:مالیات]
│       │   │       ├── چک‌های صادره        [debt_sub:چک‌های صادره]
│       │   │       ├── سایر                 [debt_sub:سایر]
│       │   │       └── [🔙 بازگشت]         → back to category
│       │   ├── 👤 شخصی               [debt_cat:👤 شخصی]
│       │   │   └── Step 1b: Subcategory (inline)
│       │   │       ├── وام شخصی             [debt_sub:وام شخصی]
│       │   │       ├── خانواده               [debt_sub:خانواده]
│       │   │       ├── دوستان                [debt_sub:دوستان]
│       │   │       ├── سایر                  [debt_sub:سایر]
│       │   │       └── [🔙 بازگشت]          → back to category
│       │   ├── سایر                    [debt_cat:سایر] → skip to Step 2
│       │   └── ❌ انصراف               [debt_cat:cancel] → Cancel → Main Menu
│       ├── Step 2: Amount
│       │   └── [❌ انصراف] → Cancel → Main Menu
│       ├── Step 3: Party (customer list or manual)
│       │   ├── {customer names from DB}    (ReplyKeyboard)
│       │   ├── ✏️ وارد دستی               (manual entry)
│       │   ├── [❌ انصراف] → Cancel → Main Menu
│       │   └── [🔙 بازگشت به منو] → Main Menu
│       ├── Step 4: Description
│       │   ├── [❌ انصراف] → Cancel → Main Menu
│       │   └── [🔙 بازگشت به منو] → Main Menu
│       ├── Step 5: Due Date
│       │   ├── 📅 امروز                 (set to today)
│       │   ├── (YYYY/MM/DD format)      (manual date)
│       │   ├── [❌ انصراف] → Cancel → Main Menu
│       │   └── [🔙 بازگشت به منو] → Main Menu
│       ├── Step 6: Photo (optional)
│       │   ├── [⏭️ بدون عکس]            → skip
│       │   ├── (send photo)              → save photo
│       │   ├── [❌ انصراف] → Cancel → Main Menu
│       │   └── [🔙 بازگشت به منو] → Main Menu
│       ├── Step 7: Card Number Selection (optional)
│       │   ├── {saved card names | last4****}  (ReplyKeyboard)
│       │   ├── ✏️ ورود دستی شماره کارت → Step 7a: Manual Card
│       │   │   ├── (16 digits)           → move to Step 8
│       │   │   ├── ⏭️ رد کردن            → skip → Step 8
│       │   │   ├── [🔙 بازگشت]           → back to Step 7
│       │   │   └── [❌ انصراف]            → Cancel → Main Menu
│       │   ├── ⏭️ رد کردن                → skip → Step 8
│       │   ├── [❌ انصراف] → Cancel → Main Menu
│       │   └── [🔙 بازگشت به منو] → Main Menu
│       ├── Step 8: Sheba/IBAN Selection (optional)
│       │   ├── {saved sheba names | IR****}  (ReplyKeyboard)
│       │   ├── ✏️ ورود دستی شماره شبا  → Step 8a: Manual Sheba
│       │   │   ├── (24 digits)           → move to Step 9
│       │   │   ├── ⏭️ رد کردن            → skip → Step 9
│       │   │   ├── [🔙 بازگشت]           → back to Step 8
│       │   │   └── [❌ انصراف]            → Cancel → Main Menu
│       │   ├── ⏭️ رد کردن                → skip → Step 9
│       │   ├── [❌ انصراف] → Cancel → Main Menu
│       │   └── [🔙 بازگشت به منو] → Main Menu
│       ├── Step 9: Bank Name Selection (optional)
│       │   ├── 🏛 {saved bank names}     (ReplyKeyboard)
│       │   ├── ✏️ ورود دستی نام بانک   → Step 9a: Manual Bank Name
│       │   │   ├── (text)                → Step 10
│       │   │   ├── ⏭️ رد کردن            → skip → Step 10
│       │   │   ├── [🔙 بازگشت]           → back to Step 9
│       │   │   └── [❌ انصراف]            → Cancel → Main Menu
│       │   ├── ⏭️ رد کردن                → skip → Step 10
│       │   ├── [❌ انصراف] → Cancel → Main Menu
│       │   └── [🔙 بازگشت به منو] → Main Menu
│       └── Step 10: Confirmation (inline)
│           ├── ✅ تأیید  [confirm_yes] → Save → Main Menu
│           └── ❌ رد     [confirm_no]  → Cancel → Main Menu
│
├── 💵 طلب‌ها (Receivables) ────────────────────────────────── [Receivable Submenu - Inline]
│   │
│   │  ┌─ Receivable Submenu (InlineKeyboardMarkup) ──────────────────┐
│   ├──┤  🟡 طلب‌های فعال           [receivable_active]                │
│   │  │  🔴 سررسید گذشته          [receivable_overdue]               │
│   │  │  🟢 تسویه شده             [receivable_settled_cat]           │
│   │  │  ⏰ سررسید امروز          [receivable_due_today]             │
│   │  │  📅 سررسید این هفته       [receivable_due_week]              │
│   │  │  📋 همه طلب‌ها              [receivable_all_cat]               │
│   │  │  💵 دریافت طلب            [receivable_receive_cat]           │
│   │  │  📊 تسویه‌ها               [settlement_recv]                  │
│   │  │  📜 دریافت‌های انجام شده   [recv_view_payments]              │
│   │  │  📊 گزارش طلب‌ها            [receivable_reports]               │
│   │  │  📌 ثبت طلب جدید           [receivable_register]              │
│   │  └──────────────────────────────────────────────────────────────┘
│   │
│   ├── 🟡 طلب‌های فعال → Grouped by customer (inline):
│   │   ├── Summary text (customer count, total, remaining)
│   │   ├── 👤 {party} | {remaining} تومان ({count} مورد)  [recv_cust_detail:{key}:{party}]
│   │   │   └── Customer Detail View (inline):
│   │   │       ├── [📩 پیامک همه]  [recv_group_sms:{key}:{party}]
│   │   │       ├── [💵 دریافت]     [recv_group_pay:{key}:{party}]
│   │   │       │   └── Customer-level FIFO payment → PaymentForm FSM
│   │   │       └── [🔙 بازگشت به لیست]  [recv_group_back] → Receivable Submenu
│   │   ├── Per-receivable items: [recv_item_detail:{key}:{party}:{id}]
│   │   └── ✅ {party} | تسویه شده ({count} مورد)
│   │
│   ├── 🔴 سررسید گذشته → Grouped by customer (same structure)
│   ├── 🟢 تسویه شده → Category Filter (inline) ── [receivable_settled_cat]
│   │   ├── 📋 همه دسته‌ها          [recv_settled_cat:all]
│   │   ├── 🏢 کسب‌وکار            [recv_settled_cat:🏢 کسب‌وکار]
│   │   │   └── Subcategory Filter:
│   │   │       ├── 📋 همه زیرمجموعه‌ها   [recv_settled_sub:all]
│   │   │       ├── فروش ضایعات
│   │   │       ├── مشتریان
│   │   │       ├── چک‌های دریافتی
│   │   │       ├── پروژه‌ها
│   │   │       ├── سایر
│   │   │       └── [🔙 بازگشت]
│   │   ├── 👤 شخصی                [recv_settled_cat:👤 شخصی]
│   │   │   └── Subcategory Filter:
│   │   │       ├── 📋 همه زیرمجموعه‌ها   [recv_settled_sub:all]
│   │   │       ├── دوستان
│   │   │       ├── خانواده
│   │   │       ├── وام شخصی
│   │   │       ├── سایر
│   │   │       └── [🔙 بازگشت]
│   │   ├── سایر                   [recv_settled_cat:سایر]
│   │   └── [🔙 بازگشت]           → Receivable Submenu
│   │
│   │   Settled receivable items → 3-level hierarchy:
│   │   ├── Level 1: Customer list [rs_cust:{id}]
│   │   ├── Level 2: Receivable list per customer [rs_item:{txn_id}]
│   │   └── Level 3: Receivable detail with payment history
│   │
│   ├── ⏰ سررسید امروز → Grouped by customer (same structure)
│   ├── 📅 سررسید این هفته → Grouped by customer (same structure)
│   │
│   ├── 📋 همه طلب‌ها → Category Filter (inline) ── [receivable_all_cat]
│   │   └── (same category/subcategory filter structure as settled)
│   │
│   ├── 💵 دریافت طلب → Category Filter (inline) ── [receivable_receive_cat]
│   │   ├── 📋 همه دسته‌ها          [recv_receive_cat:all]
│   │   │   └── Subcategory Filter → Customer List → PaymentForm FSM
│   │   ├── 🏢 کسب‌وکار            [recv_receive_cat:🏢 کسب‌وکار]
│   │   │   └── Subcategory Filter → Customer List → PaymentForm FSM
│   │   ├── 👤 شخصی                [recv_receive_cat:👤 شخصی]
│   │   │   └── Subcategory Filter → Customer List → PaymentForm FSM
│   │   ├── سایر                   [recv_receive_cat:سایر]
│   │   └── [🔙 بازگشت]           → Receivable Submenu
│   │
│   ├── 📊 تسویه‌ها → Settlement view (inline) ── [settlement_recv]
│   │   ├── Level 1 — Customer Overview
│   │   │   ├── Summary (total amount, total collected, remaining, collection rate)
│   │   │   ├── 👤 {party} | {collected}/{total} تومان ({pct}%)  [stl_cust:{short_id}]  (per customer)
│   │   │   └── [🔙 بازگشت]  [receivable_settled_cat] → Receivable Submenu
│   │   ├── Level 2 — Customer Settlement List
│   │   │   ├── Customer summary
│   │   │   ├── 🟢/🟡 #{id} | {collected} از {total} تومان ({pct}%)  [stl_item:{txn_id}]  (per receivable)
│   │   │   └── [🔙 بازگشت به مشتریان]  [stl_bc:{cache_key}] → Level 1
│   │   └── Level 3 — Settlement Detail
│   │       ├── Full receivable info + payment history
│   │       ├── [📸 عکس] / [📸 رسید پرداخت]  (if photos exist)
│   │       ├── [📜 تاریخچه پرداخت]
│   │       └── [🔙 بازگشت به لیست]  [stl_bi:{cache_key}:{safe_party}] → Level 2
│   │
│   ├── 📜 دریافت‌های انجام شده → 3-level collection history ── [recv_view_payments]
│   │   ├── Level 1 — Customer List
│   │   │   ├── Summary (total collections, collection count, customer count)
│   │   │   ├── 👤 {party} | {total_collected} تومان ({count} دریافت)  [rvp_cust:{short_id}]  (per customer)
│   │   │   └── [🔙 بازگشت به منوی طلب‌ها]  [recv_view_payments_back] → Receivable Submenu
│   │   ├── Level 2 — Customer Collection List
│   │   │   ├── Customer summary
│   │   │   ├── 🟢/🟡 #{txn_id} | {collected} از {total} تومان ({pct}%)  [rvp_detail:{txn_id}]  (per receivable)
│   │   │   │   └── Per-collection details (amount, date, description, photo indicator)
│   │   │   └── [🔙 بازگشت به مشتریان]  [rvp_bc:{cache_key}] → Level 1
│   │   └── Level 3 — Collection Detail
│   │       ├── Full receivable info + collection history
│   │       ├── [📸 عکس] / [📸 رسید دریافت]  (if photos exist)
│   │       ├── [📩 پیامک]  (if payment info exists)
│   │       ├── [✏️ ویرایش]  [edit_receivable:{txn_id}]
│   │       ├── [📜 تاریخچه دریافت]
│   │       └── [🔙 بازگشت به لیست]  [rvp_bi:{cache_key}:{safe_party}] → Level 2
│   │
│   ├── 📊 گزارش طلب‌ها → Reports submenu (inline) ── [receivable_reports]
│   │   │  ┌─ Receivable Reports Submenu (InlineKeyboardMarkup) ──────┐
│   │   │  │  📊 گزارش کلی            [recv_rpt_summary]               │
│   │   │  │  ⏳ طلب‌های فعال          [recv_rpt_active]                │
│   │   │  │  ✅ وصول شده              [recv_rpt_settled]               │
│   │   │  │  🔴 سررسید گذشته         [recv_rpt_overdue]               │
│   │   │  │  ⏰ سررسید امروز         [recv_rpt_due_today]             │
│   │   │  │  📅 سررسید این هفته      [recv_rpt_due_week]              │
│   │   │  │  👥 بر اساس مشتری        [recv_rpt_by_customer]           │
│   │   │  │  🏷 بر اساس دسته‌بندی     [recv_rpt_by_category]           │
│   │   │  │  💰 دریافت‌ها             [recv_rpt_payments]              │
│   │   │  │  📊 مانده طلب             [recv_rpt_remaining]             │
│   │   │  │  📅 گزارش روزانه          [recv_rpt_daily]                 │
│   │   │  │  📅 گزارش هفتگی          [recv_rpt_weekly]                │
│   │   │  │  📅 گزارش ماهانه         [recv_rpt_monthly]               │
│   │   │  │  📅 گزارش سالانه         [recv_rpt_yearly]                │
│   │   │  │  🔙 بازگشت به منوی طلب‌ها   [recv_rpt_back]               │
│   │   │  └───────────────────────────────────────────────────────────┘
│   │   │
│   │   ├── Each report → Report text + Export Menu (inline)
│   │   │   ├── 📊 Excel    [recv_rpt_export_excel:{report_type}] → file download
│   │   │   ├── 📄 PDF      [recv_rpt_export_pdf:{report_type}]  → file download
│   │   │   └── 🔙 بازگشت به منوی گزارش‌ها  [recv_rpt_menu] → Reports submenu
│   │   │
│   │   └── [🔙 بازگشت]  [recv_rpt_back] → Receivable Submenu
│   │
│   └── 📌 ثبت طلب جدید ───────────────────────────────── [ReceivableForm FSM]
│       └── (Same step structure as DebtForm:
│            category → subcategory → amount → party →
│            description → due_date → photo →
│            card_select → sheba_select → bank_name_select → confirm)
│
├── 👥 مدیریت مشتریان (Customer Management) ──────────────── [Customer Menu]
│   │
│   │  ┌─ Customer Menu (ReplyKeyboardMarkup) ──────────────┐
│   ├──┤  👤 افزودن مشتری       │  ✏️ ویرایش مشتری         │
│   │  │  🗑 حذف مشتری          │  🔍 جستجوی مشتری         │
│   │  │  📋 لیست مشتریان       │  🔙 بازگشت به منو        │
│   │  └────────────────────────────────────────────────────┘
│   │
│   ├── 👤 افزودن مشتری ──────────────────────────────── [CustomerForm FSM]
│   │   ├── Step 1: Name (required)
│   │   │   ├── [❌ انصراف] → Cancel → Customer Menu
│   │   │   └── (text) → Step 2
│   │   ├── Step 2: Phone (optional)
│   │   │   ├── [⏭️ رد کردن] → skip
│   │   │   ├── [🔙 بازگشت] → Step 1
│   │   │   ├── [❌ انصراف] → Cancel → Customer Menu
│   │   │   └── (text) → Step 3
│   │   ├── Step 3: Address (optional)
│   │   │   ├── [⏭️ رد کردن] → skip
│   │   │   ├── [🔙 بازگشت] → Step 2
│   │   │   ├── [❌ انصراف] → Cancel → Customer Menu
│   │   │   └── (text) → Step 4
│   │   └── Step 4: Notes (optional)
│   │       ├── [⏭️ رد کردن] → skip → Save → Customer Menu
│   │       ├── [🔙 بازگشت] → Step 3
│   │       ├── [❌ انصراف] → Cancel → Customer Menu
│   │       └── (text) → Save → Customer Menu
│   │
│   ├── ✏️ ویرایش مشتری ───────────────────────────── [CustomerEditForm FSM]
│   │   ├── Step 1: Select customer (inline list)
│   │   │   ├── {customer name}        [edit_customer:{id}]
│   │   │   ├── {customer (phone)}     [edit_customer:{id}]  (duplicate names)
│   │   │   └── ❌ انصراف              [edit_customer:cancel] → Customer Menu
│   │   └── Step 2: Enter new name (or "-" for no change)
│   │       ├── [❌ انصراف] → Cancel → Customer Menu
│   │       ├── [🔙 بازگشت به منو] → Main Menu
│   │       └── (text/-) → Save → Customer Menu
│   │
│   ├── 🗑 حذف مشتری ──────────────────────────────── [CustomerDeleteForm FSM]
│   │   ├── Step 1: Select customer (inline list)
│   │   │   ├── {customer name}        [delete_customer:{id}]
│   │   │   └── ❌ انصراف              [delete_customer:cancel] → Customer Menu
│   │   └── Step 2: Confirm (inline)
│   │       ├── ✅ تأیید  [confirm_yes] → Delete → Main Menu
│   │       └── ❌ رد     [confirm_no]  → Cancel → Main Menu
│   │
│   ├── 🔍 جستجوی مشتری ──────────────────────────── [CustomerSearchForm FSM]
│   │   ├── [❌ انصراف] → Cancel → Customer Menu
│   │   └── (text query) → Results → Customer Menu
│   │
│   └── 📋 لیست مشتریان → Customer list display → Customer Menu
│
├── 📊 داشبورد مالی (Financial Dashboard) ──────────────────── [Dashboard Screen]
│   ├── Shows: income, expense, receivable, debt, balance, percentages, progress bars
│   ├── Inline: Export Menu
│   │   ├── 📊 Excel    [export_excel] → file download
│   │   └── 📄 PDF      [export_pdf]   → file download
│   └── Main Menu below
│
├── 💳 ثبت شماره کارت و شبا (Card/IBAN Management) ────────── [Card Submenu - Inline]
│   │
│   │  ┌─ Card Submenu (InlineKeyboardMarkup) ────────────────┐
│   ├──┤  📋 همه کارت‌ها          [card_all]                    │
│   │  │  ➕ ثبت جدید             [card_register]               │
│   │  │  🔍 جستجوی کارت         [card_search_inline]          │
│   │  │  📊 گزارش کارت‌ها        [card_reports]                │
│   │  └────────────────────────────────────────────────────┘
│   │
│   ├── 📋 همه کارت‌ها → 3-level hierarchical view:
│   │   │
│   │   ├── Level 1 — Owner Overview (inline) ── [card_all]
│   │   │   ├── 📊 خلاصه کلی (Overall Summary)
│   │   │   │   ├── تعداد کارت‌ها
│   │   │   │   ├── تعداد مالکان
│   │   │   │   └── نوع (کارت/شبا)
│   │   │   ├── ────────────────────
│   │   │   ├── Per-owner blocks:
│   │   │   │   ├── 👤 {name}
│   │   │   │   │   └── تعداد کارت‌ها
│   │   │   ├── [👤 {name} | {count} کارت]  [card_cust_detail:{key}:{safe_name}]  (per owner)
│   │   │   ├── 🔃 مرتب‌سازی         [card_sort_menu:{key}]
│   │   │   │   ├── 🔤 نام           [card_sort:{key}:name]
│   │   │   │   ├── 📊 تعداد         [card_sort:{key}:count]
│   │   │   │   ├── 🏛 بانک          [card_sort:{key}:bank]
│   │   │   │   └── 📅 تاریخ         [card_sort:{key}:date]
│   │   │   ├── 🔽 فیلتر             [card_filter_menu:{key}]
│   │   │   │   ├── 💳 فقط کارت‌دار   [card_filter:{key}:has_card]
│   │   │   │   ├── 🏦 فقط شبا‌دار   [card_filter:{key}:has_sheba]
│   │   │   │   ├── 💳+🏦 هر دو      [card_filter:{key}:both]
│   │   │   │   └── 📋 همه           [card_filter:{key}:all]
│   │   │   └── [🔙 بازگشت]          [card_group_back] → Card Submenu
│   │   │
│   │   ├── Level 2 — Owner Card List (inline) ── [card_cust_detail:{key}:{name}]
│   │   │   ├── 👤 {name} (owner summary)
│   │   │   ├── 💳 #{id} | {last4}**** | شبا  [card_detail:{id}:{key}:{name}]  (per card)
│   │   │   └── [🔙 بازگشت به لیست]           [card_back:{key}] → Level 1
│   │   │
│   │   └── Level 3 — Card Detail (inline) ── [card_detail:{id}:{key}:{name}]
│   │       ├── Full card info (name, card number, sheba, bank, date)
│   │       └── Per-card inline buttons:
│   │           ├── 📋 کپی کارت      [copy_card:{id}]
│   │           ├── 📋 کپی شبا       [copy_sheba:{id}]
│   │           ├── 📩 ارسال پیامک   [copy_sms:{id}]
│   │           ├── 📋 بدهی‌ها ({n})  [card_linked_debt:{id}]     (if linked debts exist)
│   │           ├── 📌 طلب‌ها ({n})   [card_linked_recv:{id}]     (if linked receivables exist)
│   │           ├── 💳 پرداخت‌ها ({n}) [card_linked_pay:{id}]    (if linked payments exist)
│   │           ├── ✏️ ویرایش        [card_edit:{id}]
│   │           ├── 🗑 حذف           [card_delete:{id}]
│   │           └── [🔙 بازگشت]      [card_detail_back:{short_id}] → Level 2
│   │
│   ├── ➕ ثبت جدید ──────────────────────────────────── [CardForm FSM]
│   │   ├── Step 1: Name choice (ReplyKeyboard)
│   │   │   ├── ✏️ ورود دستی نام → Step 1a: Manual name entry
│   │   │   │   ├── [❌ انصراف] → Cancel → Card Submenu
│   │   │   │   ├── [🔙 بازگشت به منو] → Main Menu
│   │   │   │   └── (text) → Step 2
│   │   │   ├── 👥 انتخاب از مشتریان → Step 1b: Customer selection
│   │   │   │   ├── {customer names} (ReplyKeyboard)
│   │   │   │   ├── [❌ انصراف] → Cancel → Card Submenu
│   │   │   │   ├── [🔙 بازگشت به منو] → Main Menu
│   │   │   │   └── (select customer) → Step 2
│   │   │   ├── [❌ انصراف] → Cancel → Main Menu
│   │   │   └── [🔙 بازگشت به منو] → Main Menu
│   │   ├── Step 2: Card Number (optional)
│   │   │   ├── (16 digits) → Step 3
│   │   │   ├── ⏭️ رد کردن → skip → Step 3
│   │   │   ├── [🔙 بازگشت] → Step 1
│   │   │   └── [❌ انصراف] → Cancel → Card Submenu
│   │   ├── Step 3: Sheba/IBAN (optional)
│   │   │   ├── (24 digits) → Step 4
│   │   │   ├── ⏭️ رد کردن → skip → Step 4
│   │   │   ├── [🔙 بازگشت] → Step 2
│   │   │   └── [❌ انصراف] → Cancel → Card Submenu
│   │   ├── Step 4: Bank Name (ReplyKeyboard)
│   │   │   ├── 🏛 {saved bank names}
│   │   │   ├── ✏️ ورود دستی نام بانک → Manual input
│   │   │   ├── ⏭️ رد کردن → skip → Confirmation
│   │   │   ├── [🔙 بازگشت] → Step 3
│   │   │   └── [❌ انصراف] → Cancel → Card Submenu
│   │   └── Step 5: Confirmation (inline)
│   │       ├── ✅ تأیید  [confirm_yes] → Save → Card Submenu
│   │       └── ❌ رد     [confirm_no]  → Cancel → Card Submenu
│   │
│   ├── ✏️ ویرایش کارت ──────────────────────────────── [CardEditForm FSM]
│   │   ├── Select card → Edit Field Selection (inline):
│   │   │   ├── 👤 نام            [card_edit_field:{id}:name]
│   │   │   ├── 💳 شماره کارت    [card_edit_field:{id}:card]
│   │   │   ├── 🏦 شماره شبا     [card_edit_field:{id}:sheba]
│   │   │   ├── 🏛 نام بانک      [card_edit_field:{id}:bank]
│   │   │   └── ✅ تأیید و ذخیره  [card_edit_field:{id}:save]
│   │   └── Confirmation (inline) → Save
│   │
│   ├── 🗑 حذف کارت ─────────────────────────────────── [CardDeleteForm FSM]
│   │   └── Confirm → [confirm_yes] → Delete
│   │
│   └── 🔍 جستجوی کارت ───────────────────────────── [CardSearchForm FSM]
│       ├── [❌ انصراف] → Cancel → Card Submenu
│       └── (text query) → Results with per-card inline buttons → Card Submenu
│
├── 📈 گزارش‌های مالی (Financial Reports) ──────────────────── [Reports Menu]
│   │
│   │  ┌─ Report Menu (ReplyKeyboardMarkup) ─────────────────┐
│   ├──┤  📅 گزارش روزانه     │  📅 گزارش هفتگی              │
│   │  │  📅 گزارش ماهانه     │  📅 گزارش سالانه              │
│   │  │  🔙 بازگشت به منو                                  │
│   │  └────────────────────────────────────────────────────┘
│   │
│   ├── 📅 گزارش روزانه → Report + Export Menu (inline) → Main Menu
│   ├── 📅 گزارش هفتگی → Report + Export Menu (inline) → Main Menu
│   ├── 📅 گزارش ماهانه → Report + Export Menu (inline) → Main Menu
│   ├── 📅 گزارش سالانه → Report + Export Menu (inline) → Main Menu
│   └── [🔙 بازگشت به منو] → Main Menu
│
├── 🔍 جستجو (Search) ──────────────────────────────────── [SearchForm FSM]
│   ├── Step 1: Query text
│   │   ├── [❌ انصراف] → Cancel → Main Menu
│   │   └── (text) → Step 2
│   └── Step 2: Transaction Type (inline)
│       ├── 💰 درآمد      [search_type_income]
│       ├── 💸 هزینه      [search_type_expense]
│       ├── 📋 بدهی       [search_type_debt]
│       ├── 📌 طلب        [search_type_receivable]
│       ├── 🔙 همه        [search_type_all]
│       └── → Results display → Main Menu
│
├── 💾 پشتیبان‌گیری (Backup) ───────────────────────────────── [Backup Menu - Inline]
│   │  ┌─ Backup Menu (InlineKeyboardMarkup) ───────────────┐
│   ├──┤  📦 ایجاد پشتیبان       [backup_create]            │
│   │  │  🔄 بازیابی پشتیبان     [backup_restore]           │
│   │  │  📋 لیست پشتیبان‌ها      [backup_list]              │
│   │  └────────────────────────────────────────────────────┘
│   │
│   ├── 📦 ایجاد پشتیبان → Creates backup file → sends as document
│   ├── 🔄 بازیابی پشتیبان → Shows list of backup files + manual instructions
│   └── 📋 لیست پشتیبان‌ها → Lists backups (filename, date, size)
│
└── ⚙️ تنظیمات (Settings) ───────────────────────────────── [Settings Menu]
    │
    │  ┌─ Settings Menu (ReplyKeyboardMarkup) ───────────────┐
    ├──┤  👤 اطلاعات کاربری     │  📊 خلاصه حساب             │
    │  │  🔙 بازگشت به منو                                    │
    │  └────────────────────────────────────────────────────┘
    │
    ├── 👤 اطلاعات کاربری → User info display (ID, name, stats) → Settings Menu
    ├── 📊 خلاصه حساب → Dashboard (same as 📊 داشبورد مالی) → Main Menu
    └── [🔙 بازگشت به منو] → Main Menu

══════════════════════════════════════════════════════════════
PAYMENT WORKFLOW (PaymentForm FSM)
══════════════════════════════════════════════════════════════

Entry points:
├── 💳 پرداخت بدهی [debt_pay_cat] → Category → Subcategory → Customer [debt_pay_cust:{id}]
├── 💵 دریافت طلب [receivable_receive_cat] → Category → Subcategory → Customer [recv_pay_cust:{id}]
├── Quick pay from detail: [quick_pay_debt:{txn_id}] / [quick_pay_recv:{txn_id}]
└── Customer-level pay from receivable detail: [recv_group_pay:{key}:{party}]

Flow:
├── Step 1: Payment Type Selection [PaymentForm.payment_type]
│   ├── 💰 پرداخت کامل / دریافت کامل  [pay_type:full]  → auto-set full amount
│   ├── 💰 پرداخت جزئی / دریافت جزئی  [pay_type:partial]
│   │   └── Step 2: Amount Input [PaymentForm.amount]
│   │       └── (valid number ≤ remaining) → Step 3
│   └── ❌ انصراف  [pay_type:cancel] → Main Menu
├── Step 3: Receipt (optional) [PaymentForm.receipt]
│   ├── Send photo → save receipt photo
│   ├── Send text → save description
│   ├── [⏭️ بدون رسید] → skip
│   └── [❌ انصراف] → Cancel → Main Menu
└── Step 4: Confirmation [PaymentForm.confirm]
    ├── [📩 پیامک]  [pay_sms:{txn_id}]  (if payment info exists, shows card/sheba/bank/amount)
    ├── ✅ تأیید پرداخت  [pay_confirm_yes] → Save payment → Main Menu
    └── ❌ رد              [pay_confirm_no]  → Cancel → Main Menu

Customer-level FIFO payment:
├── Shows customer total remaining across all active debts/receivables
├── User enters total amount to pay
├── System distributes FIFO across transactions (oldest first)
├── Each transaction gets a payment record
└── Transactions fully paid are marked settled

══════════════════════════════════════════════════════════════
EDIT WORKFLOW (DebtEditForm / ReceivableEditForm FSM)
══════════════════════════════════════════════════════════════

Entry: [edit_debt:{txn_id}] or [edit_receivable:{txn_id}]

Edit Field Selection (inline):
├── 💰 مبلغ         [edit_field:amount]
│   └── Input new amount → Back to field selection
├── 👤 طرف حساب      [edit_field:party]
│   └── Input new party name → Back to field selection
├── 📝 توضیحات       [edit_field:description]
│   └── Input new description → Back to field selection
├── 📅 سررسید        [edit_field:due_date]
│   └── Input new date (YYYY/MM/DD) or 📅 امروز → Back to field selection
├── 📸 عکس           [edit_field:photo]
│   ├── 🗑 حذف عکس         (remove existing photo)
│   ├── ⏭️ بدون تغییر       (keep current photo)
│   ├── Send new photo      (replace existing photo)
│   └── ❌ انصراف / 🔙 بازگشت به منو
├── 🏷 دسته‌بندی      [edit_field:category]
│   ├── Category selection [debt_cat:{cat}] / [recv_cat:{cat}]
│   │   ├── 🏢 کسب‌وکار → Subcategory selection
│   │   ├── 👤 شخصی → Subcategory selection
│   │   └── سایر → Direct save
│   └── Subcategory selection [debt_sub:{sub}] / [recv_sub:{sub}]
│       └── [🔙 بازگشت] → Back to category
├── 💳 شماره کارت    [edit_field:card_number]
│   └── Input 16-digit card number or ⏭️ رد کردن → Back to field selection
├── 🏦 شبا           [edit_field:sheba]
│   └── Input 24-digit sheba (without IR) or ⏭️ رد کردن → Back to field selection
├── 🏛 بانک          [edit_field:bank_name]
│   └── Input bank name or ⏭️ رد کردن → Back to field selection
└── ✅ تأیید و ذخیره  [edit_field:save]
    └── Confirmation (inline)
        ├── ✅ تأیید  [confirm_yes] → Save to MongoDB → Main Menu
        └── ❌ رد     [confirm_no]  → Cancel → Main Menu

══════════════════════════════════════════════════════════════
SHARED INLINE ACTIONS (available on debt/receivable list items)
══════════════════════════════════════════════════════════════

📸 عکس [view_photo:{txn_id}]
    └── Displays photo attachment for transaction

📸 رسید پرداخت / رسید دریافت [view_payment_photo:{txn_id}]
    └── Displays receipt photo from payment record

📩 پیامک [debt_sms:{txn_id}] / [recv_sms:{txn_id}]
    └── Formats payment info (card, sheba, bank, name, amount) as copyable text
    └── Includes: card number (formatted), sheba, party name, bank name, amount (digits), amount (words)

💳 پرداخت [quick_pay_debt:{txn_id}] / 💵 دریافت [quick_pay_recv:{txn_id}]
    └── → PaymentForm FSM (see Payment Workflow above)

✏️ ویرایش [edit_debt:{txn_id}] / [edit_receivable:{txn_id}]
    └── → Edit Workflow (see Edit Workflow above)

🗑 حذف [delete_debt:{txn_id}] / [delete_receivable:{txn_id}]
    └── Confirmation (inline)
        ├── ✅ تأیید  [confirm_yes] → Delete → Main Menu
        └── ❌ رد     [confirm_no]  → Cancel → Main Menu

📜 تاریخچه پرداخت [debt_payment_history:{txn_id}] / [receivable_payment_history:{txn_id}]
    └── Displays payment history for a transaction

══════════════════════════════════════════════════════════════
SETTLEMENT MODULE
══════════════════════════════════════════════════════════════

Entry: 📊 تسویه‌ها from Debt or Receivable submenu

Settlement Submenu (InlineKeyboardMarkup):
├── 💳 تسویه بدهی‌ها    [settlement_debt]
├── 💵 تسویه طلب‌ها     [settlement_recv]
└── 📊 گزارش تسویه‌ها   [settlement_reports]

Settlement views (3-level hierarchy):
├── Level 1: Customers with payments grouped by name
│   ├── Summary (total amount, total paid, remaining, settlement %)
│   └── Per-customer: [stl_cust:{short_id}]
├── Level 2: Transactions per customer
│   ├── 🟢/🟡 #{id} | {paid} از {total} ({pct}%)
│   └── [stl_item:{txn_id}]
└── Level 3: Transaction detail + full payment history
    ├── [📸 عکس] / [📸 رسید پرداخت] (if exist)
    ├── [📜 تاریخچه پرداخت]
    └── [🔙 بازگشت به لیست]

Settlement Reports [settlement_reports]:
├── Comprehensive report showing debt + receivable settlement stats
├── Includes: total/paid/remaining/percentage per type
├── Fully settled vs partial counts
└── Net settlement (receivable_paid - debt_paid)

Navigation:
├── [stl_bc:{cache_key}] → Back to Level 1 (customers)
└── [stl_bi:{cache_key}:{safe_party}] → Back to Level 2 (items)

══════════════════════════════════════════════════════════════
CACHING STRATEGY
══════════════════════════════════════════════════════════════

The bot uses in-memory caches with asyncio.Lock for thread safety:

- _debt_groups_cache       → Debt active/overdue hierarchical view data
- _recv_groups_cache       → Receivable active/overdue hierarchical view data
- _debt_payments_cache     → Debt payments view data
- _recv_payments_cache     → Receivable collections view data
- _settlement_groups_cache → Settlement hierarchy data (debt + receivable)
- _card_groups_cache       → Card hierarchy data
- _debt_rpt_cache          → Debt report data for export
- _recv_rpt_cache          → Receivable report data for export
- _callback_index          → Short ID → (cache_key, safe_party, extra_data) mapping

Cache eviction: max 100 entries per cache, oldest removed first.

══════════════════════════════════════════════════════════════
FSM STATES
══════════════════════════════════════════════════════════════

IncomeForm
├── amount
├── description
├── category
├── photo
└── confirm

ExpenseForm
├── amount
├── description
├── category
├── photo
└── confirm

DebtForm
├── category
├── subcategory
├── amount
├── party
├── description
├── due_date
├── photo
├── card_select
├── manual_card
├── sheba_select
├── manual_sheba
├── bank_name_select
├── manual_bank_name
├── customer_id
└── confirm

ReceivableForm
├── (same states as DebtForm)

CustomerForm
├── name
├── phone
├── address
├── notes
└── confirm

CustomerEditForm
├── select
├── name
├── phone
├── address
└── notes

CustomerDeleteForm
├── select
└── confirm

CustomerSearchForm
└── query

SearchForm
├── query
└── transaction_type

DebtEditForm
├── edit_id
├── amount
├── party
├── description
├── due_date
├── jalali_date
├── photo
├── card_number
├── sheba
├── bank_name
├── confirm
└── delete_confirm

ReceivableEditForm
├── (same states as DebtEditForm)

CardForm
├── name_choice
├── name_manual
├── name_customer_select
├── card_number
├── sheba
├── bank_name
└── confirm

CardEditForm
├── select
├── field
├── value
└── confirm

CardDeleteForm
├── select
└── confirm

CardSearchForm
└── query

PaymentForm
├── select
├── payment_type
├── amount
├── receipt
└── confirm

══════════════════════════════════════════════════════════════
CALLBACK NAMING CONVENTIONS
══════════════════════════════════════════════════════════════

debt_*          → Debt module
recv_*          → Receivable module
pay_*           → Payment flow
edit_*          → Edit flow (debt/receivable/card)
delete_*        → Delete flow
confirm_*       → Confirmation dialogs
view_photo:*    → Photo display
view_payment_photo:* → Payment receipt photo display
debt_sms:*      → Debt SMS/payment info copy
recv_sms:*      → Receivable SMS/payment info copy
copy_*          → Card/sheba copy to clipboard
export_*        → Excel/PDF export
debt_rpt_*      → Debt reports
recv_rpt_*      → Receivable reports
stl_*           → Settlement views (unified)
ds_*            → Debt settled hierarchy
rs_*            → Receivable settled hierarchy
dvp_*           → Debt view payments
rvp_*           → Receivable view payments
debt_cust_detail:* → Debt customer detail (Level 2)
debt_item_detail:* → Debt item detail (Level 3)
debt_all_cust:*  → Debt "all" customer detail
card_*          → Card module
search_type_*   → Search type selection
backup_*        → Backup operations
settlement_*    → Settlement submenu/views

══════════════════════════════════════════════════════════════
EXPORT ARCHITECTURE
══════════════════════════════════════════════════════════════

Export Service: hesab/app/services/export_service.py
├── export_transactions_excel(transactions, filename) → .xlsx
└── export_transactions_pdf(transactions, filename)   → .pdf

Export triggers:
├── Dashboard → export_excel / export_pdf (all transactions)
├── Financial Reports → export_excel / export_pdf (period-filtered)
├── Debt Reports → debt_rpt_export_excel:{type} / debt_rpt_export_pdf:{type}
└── Receivable Reports → recv_rpt_export_excel:{type} / recv_rpt_export_pdf:{type}

══════════════════════════════════════════════════════════════
CATEGORY TAXONOMY
══════════════════════════════════════════════════════════════

DEBT_CATEGORIES:
├── 🏢 کسب‌وکار
│   ├── تأمین‌کنندگان
│   ├── خرید ضایعات
│   ├── حمل و نقل
│   ├── حقوق کارکنان
│   ├── مالیات
│   ├── چک‌های صادره
│   └── سایر
├── 👤 شخصی
│   ├── وام شخصی
│   ├── خانواده
│   ├── دوستان
│   └── سایر
└── سایر (no subcategories)

RECEIVABLE_CATEGORIES:
├── 🏢 کسب‌وکار
│   ├── فروش ضایعات
│   ├── مشتریان
│   ├── چک‌های دریافتی
│   ├── پروژه‌ها
│   └── سایر
├── 👤 شخصی
│   ├── دوستان
│   ├── خانواده
│   ├── وام شخصی
│   └── سایر
└── سایر (no subcategories)

INCOME_CATEGORIES:
├── فروش محصول
├── فروش خدمات
├── حقوق
├── سرمایه‌گذاری
├── پروژه
├── مشاوره
├── فروش آنلاین
└── سایر درآمدها

EXPENSE_CATEGORIES:
├── اجاره
├── حقوق کارکنان
├── خرید کالا
├── حمل و نقل
├── تبلیغات
├── خدمات
├── قبوض
├── تعمیرات
├── مواد اولیه
├── مالیات
├── بیمه
└── سایر هزینه‌ها

══════════════════════════════════════════════════════════════
DEBUGGING & ERROR HANDLING UTILITIES
══════════════════════════════════════════════════════════════

LoggingMiddleware (main_handler.py)
├── Attached to router.message and router.callback_query
├── Logs user_id, username, content_type/text preview for messages
├── Logs callback_data for callback queries
└── Level: DEBUG

Global Error Handler (@router.error)
├── Catches all unhandled exceptions in handlers
├── Logs with exc_info=True
└── Returns True (suppresses re-raising)

Helper Functions:
├── safe_callback_answer(callback, text, show_alert)
│   └── Safely answers callback, handles already-answered cases
├── safe_parse_callback_id(callback, index)
│   └── Safely parses integer ID from callback data, returns None on failure
├── safe_edit(message, text, reply_markup, parse_mode)
│   └── Safely edits message, falls back to send if edit fails
└── safe_delete(message)
    └── Safely deletes message, ignores errors

══════════════════════════════════════════════════════════════
STARTUP FLOW
══════════════════════════════════════════════════════════════

1. main.py: asyncio.run(main())
2. Validate BOT_TOKEN and MONGO_URI from settings
3. init_database() with 3 retries (MongoDB connection + index creation)
4. Create Bot (aiogram 3.x, HTML parse mode)
5. Create Dispatcher (MemoryStorage)
6. Include single router (main_handler.router)
7. Register bot commands (/start, /menu, /help, /dashboard, /report, /backup, /search)
8. dp.start_polling(bot)
9. On stop: close_database()

No explicit on_startup handler. User creation is lazy (get_or_create on first interaction).

══════════════════════════════════════════════════════════════
UNIVERSAL NAVIGATION BUTTONS
══════════════════════════════════════════════════════════════

🔙 بازگشت به منو  → clears state → Main Menu (available on most screens)
❌ انصراف          → clears state → Main Menu (available on most screens)
🔙 بازگشت         → returns to previous step (context-dependent)
⏭️ رد کردن         → skips optional field (context-dependent)
📅 امروز           → sets date to today (due date fields only)
```
