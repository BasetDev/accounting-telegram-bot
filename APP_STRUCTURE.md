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
│   │   │   ├── models.py            # MongoDB connection, collections, indexes
│   │   │   └── repository.py        # Repository pattern (User, Transaction, Payment, Customer, Card, Reminder, Backup)
│   │   ├── handlers/
│   │   │   └── main_handler.py      # All handlers (~10,000 lines, single router)
│   │   ├── keyboards/
│   │   │   └── markups.py           # All keyboards (Inline + Reply)
│   │   ├── services/
│   │   │   └── export_service.py    # Excel/PDF export (openpyxl, reportlab)
│   │   ├── utils/
│   │   │   ├── messages.py          # All message templates
│   │   │   ├── logger.py            # Logging
│   │   │   └── jdatetime_helper.py  # Jalali date utilities
│   │   └── middleware/
│   │       └── (logging middleware in main_handler.py)
│   ├── uploads/                     # Photo attachments
│   ├── exports/                     # Generated Excel/PDF files
│   ├── backups/                     # Database backups (.db files)
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
- card_infos         → Card/IBAN information (card_number, sheba, bank_name)
- reminders          → Due date reminders
- backups            → Backup metadata

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
│   ├── 💳 پرداخت بدهی → Category Filter (inline) ── [debt_pay_cat]
│   │   ├── 📋 همه دسته‌ها          [debt_pay_cat:all]
│   │   │   └── Payment Selection List (inline) ── [PaymentForm.select]
│   │   │       ├── #{id} {party} | {remaining} تومان   [pay_select:{id}]
│   │   │       │   └── Payment Type (inline) ── [PaymentForm.payment_type]
│   │   │       │       ├── 💰 پرداخت کامل   [pay_type:full]
│   │   │       │       │   └── Confirmation (inline)
│   │   │       │       │       ├── [📩 پیامک]  [pay_sms:{id}]  (if payment info)
│   │   │       │       │       ├── ✅ تأیید پرداخت  [pay_confirm_yes] → Main Menu
│   │   │       │       │       └── ❌ رد              [pay_confirm_no]  → Main Menu
│   │   │       │       ├── 💰 پرداخت جزئی   [pay_type:partial]
│   │   │       │       │   └── Amount Input ── [PaymentForm.amount]
│   │   │       │       │       ├── [❌ انصراف] → Cancel → Main Menu
│   │   │       │       │       └── (amount) → Confirmation (inline)
│   │   │       │       │           ├── [📩 پیامک]  [pay_sms:{id}]
│   │   │       │       │           ├── ✅ تأیید پرداخت  [pay_confirm_yes] → Main Menu
│   │   │       │       │           └── ❌ رد              [pay_confirm_no]  → Main Menu
│   │   │       │       └── ❌ انصراف         [pay_type:cancel] → Main Menu
│   │   │       └── ❌ انصراف                [pay_select:cancel] → Main Menu
│   │   ├── 🏢 کسب‌وکار            [debt_pay_cat:🏢 کسب‌وکار]
│   │   │   └── Subcategory Filter → Payment Selection List (same as above)
│   │   ├── 👤 شخصی                [debt_pay_cat:👤 شخصی]
│   │   │   └── Subcategory Filter → Payment Selection List (same as above)
│   │   ├── سایر                   [debt_pay_cat:سایر] → Payment Selection List
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
│   │   ├── 👤 {party} | {remaining} تومان ({count} مورد)  [recv_detail:{key}:{party}]
│   │   │   └── Customer Detail View (inline):
│   │   │       ├── [📩 پیامک همه]  [recv_group_sms:{key}:{party}]
│   │   │       ├── [💵 دریافت]     [recv_group_pay:{key}:{party}]
│   │   │       │   └── Payment Selection List → PaymentForm FSM (same as debt pay)
│   │   │       └── [🔙 بازگشت به لیست]  [recv_group_back] → Receivable Submenu
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
│   ├── ⏰ سررسید امروز → Grouped by customer (same structure)
│   ├── 📅 سررسید این هفته → Grouped by customer (same structure)
│   │
│   ├── 📋 همه طلب‌ها → Category Filter (inline) ── [receivable_all_cat]
│   │   └── (same category/subcategory filter structure as settled)
│   │
│   ├── 💵 دریافت طلب → Category Filter (inline) ── [receivable_receive_cat]
│   │   ├── 📋 همه دسته‌ها          [recv_receive_cat:all]
│   │   │   └── Payment Selection List → PaymentForm FSM
│   │   ├── 🏢 کسب‌وکار            [recv_receive_cat:🏢 کسب‌وکار]
│   │   │   └── Subcategory Filter → Payment Selection List
│   │   ├── 👤 شخصی                [recv_receive_cat:👤 شخصی]
│   │   │   └── Subcategory Filter → Payment Selection List
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
│   ├── 📊 گزارش طلب‌ها → Summary report text → Receivable Submenu
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
│   ├── Shows: income, expense, receivable, debt, balance, status
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
│   │   │   │   ├── 🔤 نام           [card_sort:name]
│   │   │   │   ├── 📊 تعداد         [card_sort:count]
│   │   │   │   ├── 🏛 بانک          [card_sort:bank]
│   │   │   │   └── 📅 تاریخ         [card_sort:date]
│   │   │   ├── 🔽 فیلتر             [card_filter_menu:{key}]
│   │   │   │   ├── 💳 فقط کارت‌دار   [card_filter:has_card]
│   │   │   │   ├── 🏦 فقط شبا‌دار   [card_filter:has_sheba]
│   │   │   │   ├── 💳+🏦 هر دو      [card_filter:both]
│   │   │   │   └── 📋 همه           [card_filter:all]
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
│   │           └── [🔙 بازگشت]      [card_detail_back:{key}:{name}] → Level 2
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
│   ├── 📦 ایجاد پشتیبان → Creates .db file → sends as document
│   ├── 🔄 بازیابی پشتیبان → Shows list of .db files + manual instructions
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
SHARED INLINE ACTIONS (available on debt/receivable list items)
══════════════════════════════════════════════════════════════

📸 عکس [view_photo:{txn_id}]
    └── Displays photo attachment for transaction

📸 رسید پرداخت / رسید دریافت [view_payment_photo:{txn_id}]
    └── Displays receipt photo from payment record

📩 پیامک [debt_sms:{txn_id}] / [recv_sms:{txn_id}]
    └── Formats payment info (card, sheba, bank, name, amount) as copyable text

💳 پرداخت [quick_pay_debt:{txn_id}] / 💵 دریافت [quick_pay_recv:{txn_id}]
    └── → Payment Type Selection (inline)
        ├── 💰 پرداخت کامل / دریافت کامل  [pay_type:full]
        │   └── Confirmation (inline)
        │       ├── [📩 پیامک]          [pay_sms:{txn_id}]  (if payment info)
        │       ├── ✅ تأیید پرداخت      [pay_confirm_yes] → Main Menu
        │       └── ❌ رد                [pay_confirm_no]  → Main Menu
        ├── 💰 پرداخت جزئی / دریافت جزئی  [pay_type:partial]
        │   └── Amount input → Confirmation → Main Menu
        └── ❌ انصراف                    [pay_type:cancel] → Main Menu

✏️ ویرایش [edit_debt:{txn_id}] / [edit_receivable:{txn_id}]
    └── Edit Field Selection (inline):
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

🗑 حذف [delete_debt:{txn_id}] / [delete_receivable:{txn_id}]
    └── Confirmation (inline)
        ├── ✅ تأیید  [confirm_yes] → Delete → Main Menu
        └── ❌ رد     [confirm_no]  → Cancel → Main Menu

📜 تاریخچه پرداخت [debt_payment_history:{txn_id}] / [receivable_payment_history:{txn_id}]
    └── Displays payment history for a transaction

══════════════════════════════════════════════════════════════
CACHING STRATEGY
══════════════════════════════════════════════════════════════

The bot uses in-memory caches with asyncio.Lock for thread safety:

- _debt_groups_cache     → Debt active/overdue hierarchical view data
- _recv_groups_cache     → Receivable active/overdue hierarchical view data
- _debt_payments_cache   → Debt payments view + settlement data
- _recv_payments_cache   → Receivable collections view + settlement data
- _settlement_groups_cache → Settlement hierarchy data
- _card_groups_cache     → Card hierarchy data
- _callback_index        → Short ID → (cache_key, safe_party, extra_data) mapping

Cache eviction: max 100 entries per cache, oldest removed first.

══════════════════════════════════════════════════════════════
CALLBACK NAMING CONVENTIONS
══════════════════════════════════════════════════════════════

debt_*          → Debt module
recv_*          → Receivable module
pay_*           → Payment flow
edit_*          → Edit flow
delete_*        → Delete flow
confirm_*       → Confirmation dialogs
view_photo:*    → Photo display
debt_sms:*      → SMS generation
copy_*          → Copy to clipboard
export_*        → Excel/PDF export
debt_rpt_*      → Debt reports
recv_rpt_*      → Receivable reports
stl_*           → Settlement views
dvp_*           → Debt view payments
rvp_*           → Receivable view payments
debt_cust_detail:* → Debt customer detail (Level 2)
debt_item_detail:* → Debt item detail (Level 3)
card_*          → Card module
search_type_*   → Search type selection
backup_*        → Backup operations
settlement_*    → Settlement submenu

══════════════════════════════════════════════════════════════
EXPORT ARCHITECTURE
══════════════════════════════════════════════════════════════

Export Service: hesab/app/services/export_service.py
├── export_transactions_excel(transactions, filename) → .xlsx
└── export_transactions_pdf(transactions, filename)   → .pdf

Export triggers:
├── Dashboard → export_excel / export_pdf (all transactions)
├── Financial Reports → export_excel / export_pdf (period-filtered)
└── Debt Reports → debt_rpt_export_excel:{type} / debt_rpt_export_pdf:{type}

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
UNIVERSAL NAVIGATION BUTTONS
══════════════════════════════════════════════════════════════

🔙 بازگشت به منو  → clears state → Main Menu (available on most screens)
❌ انصراف          → clears state → Main Menu (available on most screens)
🔙 بازگشت         → returns to previous step (context-dependent)
⏭️ رد کردن         → skips optional field (context-dependent)
📅 امروز           → sets date to today (due date fields only)
```
