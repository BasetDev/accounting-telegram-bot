# Menu System Analysis — Hesab Telegram Bot

> **Scope:** Menu structure, navigation, and conversation flow only. No business logic, database, or deployment details.
>
> **Source files analyzed:**
> - `hesab/app/keyboards/markups.py` (395 lines — all keyboard definitions)
> - `hesab/app/handlers/main_handler.py` (3028 lines — all handlers, 106 handler decorators)
> - `hesab/app/utils/messages.py` (192 lines — all message strings)
> - `hesab/main.py` (66 lines — entry point)
> - `hesab/app/config.py` (46 lines — settings)

---

## 1. Complete Menu Tree

```
🏠 MAIN MENU (ReplyKeyboard — always visible)
│
├── 💰 ثبت درآمد (Register Income)
│   ├── Step 1: Enter Amount          [cancel_menu]
│   ├── Step 2: Enter Description     [cancel_back_menu]
│   ├── Step 3: Select Category       [income_categories]
│   ├── Step 4: Upload Photo (opt.)   [photo_skip_menu]
│   └── → Save → Return to Main Menu
│
├── 💸 ثبت هزینه (Register Expense)
│   ├── Step 1: Enter Amount          [cancel_menu]
│   ├── Step 2: Enter Description     [cancel_back_menu]
│   ├── Step 3: Select Category       [expense_categories]
│   ├── Step 4: Upload Photo (opt.)   [photo_skip_menu]
│   └── → Save → Return to Main Menu
│
├── 📋 ثبت بدهی (Register Debt)
│   ├── Step 1: Enter Amount          [cancel_menu]
│   ├── Step 2: Select/Enter Party    [party_keyboard or cancel_back_menu]
│   ├── Step 3: Enter Description     [cancel_back_menu]
│   ├── Step 4: Enter Due Date        [due_date_keyboard]
│   ├── Step 5: Upload Photo (opt.)   [photo_skip_menu]
│   ├── Step 6: Confirm               [confirm_keyboard (inline)]
│   └── → Save → Return to Main Menu
│
├── 📌 ثبت طلب (Register Receivable)
│   ├── Step 1: Enter Amount          [cancel_menu]
│   ├── Step 2: Select/Enter Party    [party_keyboard or cancel_back_menu]
│   ├── Step 3: Enter Description     [cancel_back_menu]
│   ├── Step 4: Enter Due Date        [due_date_keyboard]
│   ├── Step 5: Upload Photo (opt.)   [photo_skip_menu]
│   ├── Step 6: Confirm               [confirm_keyboard (inline)]
│   └── → Save → Return to Main Menu
│
├── 📋 لیست بدهی‌ها (Debt List)
│   └── Per item (inline):
│       ├── 📸 عکس (View Photo)       [if photo exists]
│       ├── ✏️ ویرایش (Edit)           → Edit Flow
│       └── 🗑 حذف (Delete)            → Confirm → Delete
│
├── 📌 لیست طلب‌ها (Receivable List)
│   └── Per item (inline):
│       ├── 📸 عکس (View Photo)       [if photo exists]
│       ├── ✏️ ویرایش (Edit)           → Edit Flow
│       └── 🗑 حذف (Delete)            → Confirm → Delete
│
├── 👥 مدیریت مشتریان (Customer Management)
│   ├── 👤 افزودن مشتری (Add Customer)
│   │   ├── Step 1: Enter Name        [cancel_menu]
│   │   ├── Step 2: Enter Phone (opt.)[customer_skip_menu]
│   │   ├── Step 3: Enter Address(opt)[customer_skip_menu]
│   │   ├── Step 4: Enter Notes (opt.)[customer_skip_menu]
│   │   └── → Save → Return to Customer Menu
│   │
│   ├── ✏️ ویرایش مشتری (Edit Customer)
│   │   ├── Select Customer           [customer_select_keyboard (inline)]
│   │   ├── Enter New Name            [cancel_back_menu]
│   │   └── → Save → Return to Customer Menu
│   │   **Note:** Only name can be edited. phone/address/notes states are defined but unused.
│   │
│   ├── 🗑 حذف مشتری (Delete Customer)
│   │   ├── Select Customer           [customer_select_keyboard (inline)]
│   │   ├── Confirm                   [confirm_keyboard (inline)]
│   │   └── → Delete → Return to Main Menu
│   │
│   ├── 🔍 جستجوی مشتری (Search Customer)
│   │   ├── Enter Query               [cancel_menu]
│   │   └── → Show Results → Return to Customer Menu
│   │
│   ├── 📋 لیست مشتریان (Customer List)
│   │   └── → Show List → Stay on Customer Menu
│   │
│   └── 🔙 بازگشت به منو (Back to Main Menu)
│
├── 📊 داشبورد مالی (Financial Dashboard)
│   └── Shows summary + export_menu (inline):
│       ├── 📊 Excel (Export)
│       └── 📄 PDF (Export)
│
├── 💳 ثبت شماره کارت و شبا (Card & Sheba)
│   ├── ➕ ثبت جدید (Add New)
│   │   ├── Step 1: Choose Name Method [card_name_choice_keyboard]
│   │   │   ├── ✏️ Manual Entry → Enter Name [cancel_back_menu]
│   │   │   └── 👥 From Customers → Select   [party_keyboard]
│   │   ├── Step 2: Enter Card Number [card_skip_menu]
│   │   ├── Step 3: Enter Sheba       [card_skip_menu]
│   │   ├── Step 4: Confirm           [confirm_keyboard (inline)]
│   │   └── → Save → Return to Card Menu
│   │
│   ├── 📋 لیست شماره کارت‌ها (Card List)
│   │   └── Per item (inline):
│   │       ├── 📋 کپی کارت (Copy Card)
│   │       ├── 📋 کپی شبا (Copy Sheba)
│   │       ├── 📩 ارسال پیامک (SMS Format)
│   │       ├── ✏️ ویرایش (Edit)       → Edit Flow
│   │       └── 🗑 حذف (Delete)        → Confirm → Delete
│   │
│   ├── 🔍 جستجوی کارت (Search Card)
│   │   ├── Enter Query               [cancel_menu]
│   │   └── → Show Results → Return to Card Menu
│   │
│   └── 🔙 بازگشت به منو (Back to Main Menu)
│
├── 📈 گزارش‌های مالی (Financial Reports)
│   ├── 📅 گزارش روزانه (Daily Report)
│   ├── 📅 گزارش هفتگی (Weekly Report)
│   ├── 📅 گزارش ماهانه (Monthly Report)
│   ├── 📅 گزارش سالانه (Yearly Report)
│   └── Each shows export_menu (inline):
│       ├── 📊 Excel
│       └── 📄 PDF
│
├── 🔍 جستجو (Search)
│   ├── Step 1: Enter Query           [cancel_menu]
│   ├── Step 2: Select Type           [transaction_type_keyboard (inline)]
│   │   ├── 💰 درآمد
│   │   ├── 💸 هزینه
│   │   ├── 📋 بدهی
│   │   ├── 📌 طلب
│   │   └── 🔙 همه
│   └── → Show Results → Return to Main Menu
│
├── 💾 پشتیبان‌گیری (Backup)
│   └── Inline keyboard:
│       ├── 📦 ایجاد پشتیبان (Create Backup)
│       ├── 🔄 بازیابی پشتیبان (Restore Backup)
│       └── 📋 لیست پشتیبان‌ها (Backup List)
│
└── ⚙️ تنظیمات (Settings)
    ├── 👤 اطلاعات کاربری (User Info)
    │   └── → Show Info → Stay on Settings Menu
    ├── 📊 خلاصه حساب (Account Summary)
    │   └── → Show Dashboard → Return to Main Menu
    └── 🔙 بازگشت به منو (Back to Main Menu)
```

---

## 2. Menu Hierarchy Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MAIN MENU                                   │
│  (ReplyKeyboard — persistent at bottom of screen)                   │
│                                                                     │
│  [💰 ثبت درآمد] [💸 ثبت هزینه]                                     │
│  [📋 ثبت بدهی]  [📌 ثبت طلب]                                       │
│  [📋 لیست بدهی‌ها] [📌 لیست طلب‌ها]                                  │
│  [👥 مدیریت مشتریان] [📊 داشبورد مالی]                              │
│  [💳 ثبت شماره کارت و شبا] [📈 گزارش‌های مالی]                      │
│  [🔍 جستجو] [💾 پشتیبان‌گیری]                                      │
│  [⚙️ تنظیمات]                                                      │
└──────────────┬──────────────────────────────────────────────────────┘
               │
       ┌───────┼───────┬──────────┬──────────┬──────────┬──────────┐
       ▼       ▼       ▼          ▼          ▼          ▼          ▼
   ┌───────┐┌──────┐┌───────┐┌────────┐┌────────┐┌────────┐┌─────────┐
   │ Income││Expense││ Debt  ││Receiv- ││Customer││Dashboard││ Reports │
   │ Flow  ││ Flow  ││ Flow  ││able    ││ Mgmt   ││  View  ││  Menu   │
   │       ││       ││       ││Flow    ││        ││        ││         │
   │(FSM)  ││(FSM)  ││(FSM)  ││(FSM)   ││(FSM)   ││        ││         │
   └───────┘└──────┘└───────┘└────────┘└────────┘└────────┘└─────────┘
                                                                │
                                                    ┌───────────┼───────────┐
                                                    ▼           ▼           ▼
                                                [Daily]    [Weekly]    [Monthly]
                                                              [Yearly]
                                                              
       ┌──────────┬──────────┬──────────┐
       ▼          ▼          ▼          ▼
   ┌───────┐┌────────┐┌────────┐┌─────────┐
   │Search ││Backup  ││Settings││Card &   │
   │Flow   ││Menu    ││Menu    ││Sheba    │
   │(FSM)  ││(Inline)││        ││Menu     │
   └───────┘└────────┘└────────┘└─────────┘
```

---

## 3. Navigation Flow

### 3.1 Keyboard Types Used

| Type | Class | Behavior |
|------|-------|----------|
| **ReplyKeyboard** | `ReplyKeyboardMarkup` | Persistent buttons at bottom. Always visible. User taps to send text message. |
| **InlineKeyboard** | `InlineKeyboardMarkup` | Attached to a specific message. User taps to trigger callback query. |

### 3.2 Navigation Buttons

| Button | Text | Where Used | Behavior |
|--------|------|------------|----------|
| **Cancel** | `❌ انصراف` | All FSM input steps | Clears FSM state → returns to Main Menu |
| **Back to Menu** | `🔙 بازگشت به منو` | Most input steps | Clears FSM state → returns to Main Menu |
| **Back** | `🔙 بازگشت` | Category selection, Customer form steps | Goes to previous FSM state (step back) |
| **Skip** | `⏭️ رد کردن` | Optional fields (phone, address, notes, card, sheba) | Skips field, moves to next step |
| **Skip Photo** | `⏭️ بدون عکس` | Photo upload steps | Skips photo, moves to next step |
| **Today** | `📅 امروز` | Due date input | Sets due date to today |
| **Manual Entry** | `✏️ وارد دستی` | Party selection | Allows typing name instead of selecting |

### 3.3 Global Navigation Rules

1. **`/start`** → Shows welcome message + Main Menu
2. **`/menu`** or **`🔙 بازگشت به منو`** → Clears all FSM state + shows Main Menu
3. **`/help`** → Shows help text + Main Menu
4. **`❌ انصراف`** → Clears FSM state + shows Main Menu (or parent menu for sub-menus)
5. **`🔙 بازگشت`** → Goes to previous FSM step (one step back in multi-step forms)
6. **Fallback** (any unrecognized text) → Shows Main Menu

### 3.4 Navigation Patterns

**Pattern A: Simple submenu (ReplyKeyboard)**
```
Main Menu → Tap button → Submenu appears (new ReplyKeyboard)
Submenu → Tap item → Action or further navigation
Submenu → 🔙 بازگشت به منو → Main Menu
```
Used by: Customer Management, Reports, Settings, Card Menu

**Pattern B: Multi-step FSM form**
```
Main Menu → Tap button → Step 1 (cancel_menu)
Step 1 → Enter data → Step 2 (cancel_back_menu)
Step 2 → Enter data → Step 3 (cancel_back_menu or specialized keyboard)
...
Final Step → Save → Main Menu
Any Step → ❌ انصراف → Main Menu
Any Step → 🔙 بازگشت به منو → Main Menu
```
Used by: Income, Expense, Debt, Receivable, Customer Add, Card Add, Search

**Pattern C: Inline list with actions**
```
Main Menu → Tap button → List of items (each with inline buttons)
Inline: Edit → Edit flow (FSM) → Save → Main Menu
Inline: Delete → Confirm (inline) → Delete → Main Menu
```
Used by: Debt List, Receivable List, Card List

**Pattern D: Inline menu**
```
Main Menu → Tap button → Message with inline buttons
Inline button → Action → Result message
```
Used by: Backup, Export, Search type filter

---

## 4. Conversation Flow Between Menus

### 4.1 Income Flow
```
[Main Menu] → "💰 ثبت درآمد"
  → [cancel_menu] Enter amount
  → [cancel_back_menu] Enter description
  → [income_categories] Select category
  → [photo_skip_menu] Upload photo or skip
  → Save (no confirmation step) → [Main Menu]
```
**Note:** IncomeForm has a `confirm` state defined but it is never used. The transaction is saved directly after the photo step.

### 4.2 Expense Flow
```
[Main Menu] → "💸 ثبت هزینه"
  → [cancel_menu] Enter amount
  → [cancel_back_menu] Enter description
  → [expense_categories] Select category
  → [photo_skip_menu] Upload photo or skip
  → Save (no confirmation step) → [Main Menu]
```
**Note:** ExpenseForm has a `confirm` state defined but it is never used. The transaction is saved directly after the photo step.

### 4.3 Debt Flow
```
[Main Menu] → "📋 ثبت بدهی"
  → [cancel_menu] Enter amount
  → [party_keyboard] Select/enter party (or [cancel_back_menu] if no customers)
  → [cancel_back_menu] Enter description
  → [due_date_keyboard] Enter due date
  → [photo_skip_menu] Upload photo or skip
  → [confirm_keyboard] Confirm (inline)
  → Save → [Main Menu]
```

### 4.4 Receivable Flow
```
[Main Menu] → "📌 ثبت طلب"
  → [cancel_menu] Enter amount
  → [party_keyboard] Select/enter party (or [cancel_back_menu] if no customers)
  → [cancel_back_menu] Enter description
  → [due_date_keyboard] Enter due date
  → [photo_skip_menu] Upload photo or skip
  → [confirm_keyboard] Confirm (inline)
  → Save → [Main Menu]
```

### 4.5 Debt List → Edit Flow
```
[Main Menu] → "📋 لیست بدهی‌ها"
  → List items with [debt_list_keyboard] inline
  → "✏️ ویرایش" → [edit_field_keyboard] Choose field
  → Enter new value → [edit_field_keyboard] Choose next field or save
  → "✅ تأیید و ذخیره" → [confirm_keyboard] Confirm
  → Save → [Main Menu]
```

### 4.6 Debt List → Delete Flow
```
[Main Menu] → "📋 لیست بدهی‌ها"
  → List items with [debt_list_keyboard] inline
  → "🗑 حذف" → [confirm_keyboard] Confirm
  → Delete → [Main Menu]
```

### 4.7 Customer Management Flow
```
[Main Menu] → "👥 مدیریت مشتریان"
  → [customer_menu] Submenu
    → "👤 افزودن مشتری"
      → [cancel_menu] Enter name
      → [customer_skip_menu] Enter phone (optional)
      → [customer_skip_menu] Enter address (optional)
      → [customer_skip_menu] Enter notes (optional)
      → Save → [customer_menu]
    → "✏️ ویرایش مشتری"
      → [customer_select_keyboard] Select customer (inline)
      → [cancel_back_menu] Enter new name
      → Save → [customer_menu]
    → "🗑 حذف مشتری"
      → [customer_select_keyboard] Select customer (inline)
      → [confirm_keyboard] Confirm (inline)
      → Delete → [Main Menu]
    → "🔍 جستجوی مشتری"
      → [cancel_menu] Enter query
      → Results → [customer_menu]
    → "📋 لیست مشتریان"
      → Show list → [customer_menu]
    → "🔙 بازگشت به منو" → [Main Menu]
```

### 4.8 Card & Sheba Flow
```
[Main Menu] → "💳 ثبت شماره کارت و شبا"
  → [card_menu] Submenu
    → "➕ ثبت جدید"
      → [card_name_choice_keyboard] Choose name method
        → "✏️ ورود دستی نام" → [cancel_back_menu] Enter name
        → "👥 انتخاب از مشتریان" → [party_keyboard] Select customer
      → [card_skip_menu] Enter card number (or skip)
      → [card_skip_menu] Enter sheba (or skip)
      → [confirm_keyboard] Confirm (inline)
      → Save → [card_menu]
    → "📋 لیست شماره کارت‌ها"
      → List items with [card_list_keyboard] inline
        → "📋 کپی کارت" → Copy to clipboard
        → "📋 کپی شبا" → Copy to clipboard
        → "📩 ارسال پیامک" → SMS format copy
        → "✏️ ویرایش" → [card_edit_field_keyboard] Edit flow
        → "🗑 حذف" → [confirm_keyboard] → Delete → [card_menu]
    → "🔍 جستجوی کارت"
      → [cancel_menu] Enter query
      → Results → [card_menu]
    → "🔙 بازگشت به منو" → [Main Menu]
```

### 4.9 Search Flow
```
[Main Menu] → "🔍 جستجو"
  → [cancel_menu] Enter search query
  → [transaction_type_keyboard] Select type (inline)
  → Results → [Main Menu]
```

### 4.10 Backup Flow
```
[Main Menu] → "💾 پشتیبان‌گیری"
  → [backup_menu] Inline keyboard + [Main Menu] below
    → "📦 ایجاد پشتیبان" → Create → Send file
    → "🔄 بازیابی پشتیبان" → Show backup list
    → "📋 لیست پشتیبان‌ها" → Show list
```

### 4.11 Dashboard Flow
```
[Main Menu] → "📊 داشبورد مالی"
  → Dashboard text + [export_menu] inline
    → "📊 Excel" → Export & send file
    → "📄 PDF" → Export & send file
  → [Main Menu] below
```

### 4.12 Reports Flow
```
[Main Menu] → "📈 گزارش‌های مالی"
  → [report_menu] Submenu
    → "📅 گزارش روزانه" → Report + [export_menu] inline
    → "📅 گزارش هفتگی" → Report + [export_menu] inline
    → "📅 گزارش ماهانه" → Report + [export_menu] inline
    → "📅 گزارش سالانه" → Report + [export_menu] inline
    → "🔙 بازگشت به منو" → [Main Menu]
```

### 4.13 Settings Flow
```
[Main Menu] → "⚙️ تنظیمات"
  → [settings_menu] Submenu
    → "👤 اطلاعات کاربری" → Show info → [settings_menu]
    → "📊 خلاصه حساب" → Dashboard → [Main Menu]
    → "🔙 بازگشت به منو" → [Main Menu]
```

---

## 5. Description of Each Menu and Its Purpose

### 5.1 Main Menu
- **Type:** ReplyKeyboard (persistent)
- **Purpose:** Central hub for all bot functionality
- **Buttons:** 13 buttons organized in 7 rows
- **Access:** Always visible; shown after every completed operation

### 5.2 Cancel Menu (`cancel_menu`)
- **Type:** ReplyKeyboard
- **Purpose:** Allow user to abort current operation
- **Buttons:** `❌ انصراف` (1 row)
- **Used in:** First step of multi-step forms (before any data is entered)

### 5.3 Cancel/Back Menu (`cancel_back_menu`)
- **Type:** ReplyKeyboard
- **Purpose:** Allow user to abort or return to main menu
- **Buttons:** `❌ انصراف` + `🔙 بازگشت به منو` (1 row)
- **Used in:** Middle steps of multi-step forms

### 5.4 Customer Skip Menu (`customer_skip_menu`)
- **Type:** ReplyKeyboard
- **Purpose:** Allow skip of optional fields in customer form
- **Buttons:** `⏭️ رد کردن` (row 1) + `🔙 بازگشت` + `❌ انصراف` (row 2)
- **Used in:** Customer add flow (phone, address, notes)

### 5.5 Photo Skip Menu (`photo_skip_menu`)
- **Type:** ReplyKeyboard
- **Purpose:** Allow skip of optional photo upload
- **Buttons:** `⏭️ بدون عکس` + `❌ انصراف` (1 row)
- **Used in:** Income, Expense, Debt, Receivable photo steps

### 5.6 Card Skip Menu (`card_skip_menu`)
- **Type:** ReplyKeyboard
- **Purpose:** Allow skip of optional card/sheba fields
- **Buttons:** `⏭️ رد کردن` (row 1) + `🔙 بازگشت` + `❌ انصراف` (row 2)
- **Used in:** Card number and sheba input steps

### 5.7 Customer Menu (`customer_menu`)
- **Type:** ReplyKeyboard
- **Purpose:** Sub-menu for customer management operations
- **Buttons:** Add, Edit, Delete, Search, List, Back to Menu (3 rows)
- **Access:** From Main Menu → "👥 مدیریت مشتریان"

### 5.8 Report Menu (`report_menu`)
- **Type:** ReplyKeyboard
- **Purpose:** Sub-menu for financial report periods
- **Buttons:** Daily, Weekly, Monthly, Yearly, Back to Menu (3 rows)
- **Access:** From Main Menu → "📈 گزارش‌های مالی"

### 5.9 Settings Menu (`settings_menu`)
- **Type:** ReplyKeyboard
- **Purpose:** Sub-menu for user settings
- **Buttons:** User Info, Account Summary, Back to Menu (2 rows)
- **Access:** From Main Menu → "⚙️ تنظیمات"

### 5.10 Card Menu (`card_menu`)
- **Type:** ReplyKeyboard
- **Purpose:** Sub-menu for card/sheba management
- **Buttons:** Add New, Card List, Search Card, Back to Menu (2 rows)
- **Access:** From Main Menu → "💳 ثبت شماره کارت و شبا"

### 5.11 Income Categories (`income_categories`)
- **Type:** ReplyKeyboard
- **Purpose:** Category selection for income transactions
- **Buttons:** 8 category buttons (1 per row) + Cancel + Back (1 row)
- **Categories:** فروش محصول, فروش خدمات, حقوق, سرمایه‌گذاری, پروژه, مشاوره, فروش آنلاین, سایر درآمدها

### 5.12 Expense Categories (`expense_categories`)
- **Type:** ReplyKeyboard
- **Purpose:** Category selection for expense transactions
- **Buttons:** 12 category buttons (1 per row) + Cancel + Back (1 row)
- **Categories:** اجاره, حقوق کارکنان, خرید کالا, حمل و نقل, تبلیغات, خدمات, قبوض, تعمیرات, مواد اولیه, مالیات, بیمه, سایر هزینه‌ها

### 5.13 Due Date Keyboard (`due_date_keyboard`)
- **Type:** ReplyKeyboard
- **Purpose:** Quick date selection for debt/receivable due dates
- **Buttons:** 📅 امروز (row 1) + ❌ انصراف + 🔙 بازگشت به منو (row 2)

### 5.14 Party Keyboard (`party_keyboard`)
- **Type:** ReplyKeyboard (dynamic)
- **Purpose:** Select a customer name or enter manually
- **Buttons:** One button per customer (1 per row) + ✏️ وارد دستی + Cancel + Back
- **Note:** Dynamically built from customer list

### 5.15 Card Name Choice Keyboard (`card_name_choice_keyboard`)
- **Type:** ReplyKeyboard
- **Purpose:** Choose how to enter name for card info
- **Buttons:** ✏️ Manual + 👥 From Customers (row 1) + Cancel + Back (row 2)

### 5.16 Confirm Keyboard (`confirm_keyboard`)
- **Type:** InlineKeyboard
- **Purpose:** Yes/No confirmation for save/delete operations
- **Buttons:** ✅ تأیید (confirm_yes) + ❌ رد (confirm_no)

### 5.17 Export Menu (`export_menu`)
- **Type:** InlineKeyboard
- **Purpose:** Export format selection
- **Buttons:** 📊 Excel (export_excel) + 📄 PDF (export_pdf)

### 5.18 Transaction Type Keyboard (`transaction_type_keyboard`)
- **Type:** InlineKeyboard
- **Purpose:** Filter search results by transaction type
- **Buttons:** Income, Expense, Debt, Receivable (2 rows) + All (1 row)

### 5.19 Backup Menu (`backup_menu`)
- **Type:** InlineKeyboard
- **Purpose:** Backup operations
- **Buttons:** Create, Restore, List (3 rows)

### 5.20 Debt List Keyboard (`debt_list_keyboard`)
- **Type:** InlineKeyboard (per item)
- **Purpose:** Actions on individual debt items
- **Buttons:** View Photo (if exists) + Edit + Delete (1 row)

### 5.21 Receivable List Keyboard (`receivable_list_keyboard`)
- **Type:** InlineKeyboard (per item)
- **Purpose:** Actions on individual receivable items
- **Buttons:** View Photo (if exists) + Edit + Delete (1 row)

### 5.22 Edit Field Keyboard (`edit_field_keyboard`)
- **Type:** InlineKeyboard
- **Purpose:** Select which field to edit in debt/receivable
- **Buttons:** Amount, Party, Description, Due Date (2 rows) + Save (1 row)

### 5.23 Card List Keyboard (`card_list_keyboard`)
- **Type:** InlineKeyboard (per item)
- **Purpose:** Actions on individual card info items
- **Buttons:** Copy Card, Copy Sheba (row 1) + SMS (row 2) + Edit, Delete (row 3)

### 5.24 Card Edit Field Keyboard (`card_edit_field_keyboard`)
- **Type:** InlineKeyboard
- **Purpose:** Select which field to edit in card info
- **Buttons:** Name, Card Number (row 1) + Sheba (row 2) + Save (row 3)

### 5.25 Card Copy Keyboard (`card_copy_keyboard`)
- **Type:** InlineKeyboard
- **Purpose:** Copy card/sheba data
- **Buttons:** Copy Card Number + Copy Sheba (1 row)

### 5.26 Customer Select Keyboard (`customer_select_keyboard`)
- **Type:** InlineKeyboard (dynamic)
- **Purpose:** Select a customer for edit/delete
- **Buttons:** One button per customer + Cancel
- **Note:** Disambiguates duplicate names by appending phone or ID

### 5.27 Pagination Keyboard (`pagination_keyboard`)
- **Type:** InlineKeyboard (dynamic)
- **Purpose:** Navigate through paginated lists
- **Buttons:** Previous + Next (conditional)
- **Note:** Defined but not actively used in current handlers

---

## 6. Callback Routing for Menu Buttons

### 6.1 Callback Data Patterns

| Pattern | Handler | Purpose |
|---------|---------|---------|
| `confirm_yes` | Multiple confirm handlers | Approve save/delete |
| `confirm_no` | Multiple confirm handlers | Cancel save/delete |
| `export_excel` | `handle_export` | Export to Excel |
| `export_pdf` | `handle_export` | Export to PDF |
| `search_type_income` | `search_type_selected` | Filter search: income |
| `search_type_expense` | `search_type_selected` | Filter search: expense |
| `search_type_debt` | `search_type_selected` | Filter search: debt |
| `search_type_receivable` | `search_type_selected` | Filter search: receivable |
| `search_type_all` | `search_type_selected` | Filter search: all |
| `backup_create` | `backup_create` | Create backup |
| `backup_restore` | `backup_restore` | Restore backup |
| `backup_list` | `backup_list` | List backups |
| `edit_debt:{id}` | `debt_edit_callback` | Start debt edit |
| `edit_receivable:{id}` | `receivable_edit_callback` | Start receivable edit |
| `edit_field:{field}` | `edit_field_selected` | Select field to edit |
| `delete_debt:{id}` | `debt_delete_callback` | Start debt delete |
| `delete_receivable:{id}` | `receivable_delete_callback` | Start receivable delete |
| `view_photo:{id}` | `view_photo_callback` | View transaction photo |
| `edit_customer:{id}` | `customer_edit_callback` | Select customer for edit |
| `edit_customer:cancel` | `customer_edit_callback` | Cancel customer edit |
| `delete_customer:{id}` | `customer_delete_callback` | Select customer for delete |
| `delete_customer:cancel` | `customer_delete_callback` | Cancel customer delete |
| `copy_card:{id}` | `card_copy_callback` | Copy card number |
| `copy_sheba:{id}` | `card_copy_callback` | Copy sheba number |
| `copy_sms:{id}` | `card_copy_callback` | Copy SMS format |
| `card_edit:{id}` | `card_edit_callback` | Start card edit |
| `card_delete:{id}` | `card_delete_callback` | Start card delete |
| `card_edit_field:{id}:{field}` | `card_edit_field_selected` | Select card field to edit |
| `{prefix}_page_{n}` | (defined but unused) | Pagination |

### 6.2 FSM State → Callback Routing

Callbacks are dispatched to handlers based on the current FSM state:

- `DebtEditForm.edit_id` / `ReceivableEditForm.edit_id` → `edit_field_selected`
- `DebtEditForm.confirm` → `debt_edit_confirm`
- `ReceivableEditForm.confirm` → `receivable_edit_confirm`
- `DebtEditForm.delete_confirm` → `debt_delete_confirm`
- `ReceivableEditForm.delete_confirm` → `receivable_delete_confirm`
- `DebtForm.confirm` → `debt_confirm`
- `ReceivableForm.confirm` → `receivable_confirm`
- `CustomerEditForm.select` → `customer_edit_callback`
- `CustomerDeleteForm.select` → `customer_delete_callback`
- `CustomerDeleteForm.confirm` → `customer_delete_execute`
- `SearchForm.transaction_type` → `search_type_selected`
- `CardForm.confirm` → `card_confirm`
- `CardEditForm.field` → `card_edit_field_selected`
- `CardEditForm.confirm` → `card_edit_confirm`
- `CardDeleteForm.confirm` → `card_delete_confirm`

---

## 7. Reusable Menu Components

### 7.1 Keyboard Functions (from `markups.py`)

| Function | Returns | Reusability |
|----------|---------|-------------|
| `main_menu()` | ReplyKeyboard | Used everywhere as the "home" keyboard |
| `cancel_menu()` | ReplyKeyboard | First step of any FSM form |
| `cancel_back_menu()` | ReplyKeyboard | Middle steps of any FSM form |
| `customer_skip_menu()` | ReplyKeyboard | Optional fields with skip |
| `photo_skip_menu()` | ReplyKeyboard | Photo upload steps |
| `card_skip_menu()` | ReplyKeyboard | Card/sheba optional fields |
| `confirm_keyboard()` | InlineKeyboard | Any yes/no confirmation |
| `export_menu()` | InlineKeyboard | After dashboard and reports |
| `pagination_keyboard()` | InlineKeyboard | Paginated lists (generic) |

### 7.2 Shared Helper Functions

| Function | Purpose | Used By |
|----------|---------|---------|
| `_save_photo()` | Download & save Telegram photo | Income, Expense, Debt, Receivable photo steps |
| `_process_photo_step()` | Generic photo step handler | (Defined but not directly called; logic duplicated) |
| `_process_edit_confirm()` | Generic edit confirmation | Debt edit, Receivable edit |
| `_process_delete_confirm()` | Generic delete confirmation | Debt delete, Receivable delete |
| `_start_edit_by_id()` | Start edit flow for debt/receivable | Debt edit callback, Receivable edit callback |
| `get_session()` | Get DB session | All handlers |
| `get_user()` | Get or create user | All handlers |

### 7.3 Shared FSM States Pattern

All multi-step forms follow the same pattern:
1. `amount` state → `cancel_menu`
2. Middle states → `cancel_back_menu`
3. Optional states → skip-capable keyboard
4. `confirm` state → `confirm_keyboard` (inline)

---

## 8. Inconsistencies and Duplicated Logic

### 8.1 Duplicated Form Flows

| Flow A | Flow B | Overlap |
|--------|--------|---------|
| Income Form | Expense Form | Identical structure: amount → description → category → photo → save |
| Debt Form | Receivable Form | Identical structure: amount → party → description → due_date → photo → confirm |
| DebtEditForm | ReceivableEditForm | Identical field selection and edit logic |
| Debt Delete | Receivable Delete | Identical confirm + delete logic |
| Card Edit | Debt/Receivable Edit | Similar field-selection → edit → confirm pattern |

### 8.2 Inconsistent Back Navigation

| Location | Back Button Text | Behavior |
|----------|-----------------|----------|
| Income category step | `🔙 بازگشت` | Goes to description step (correct step-back) |
| Expense category step | `🔙 بازگشت` | Goes to description step (correct step-back) |
| Customer phone step | `🔙 بازگشت` | Goes to name step (correct step-back) |
| Customer address step | `🔙 بازگشت` | Goes to phone step (correct step-back) |
| Customer notes step | `🔙 بازگشت` | Goes to address step (correct step-back) |
| Income description step | `🔙 بازگشت به منو` | Goes to Main Menu (NOT back to amount) |
| Expense description step | `🔙 بازگشت به منو` | Goes to Main Menu (NOT back to amount) |
| Debt party step | `🔙 بازگشت به منو` | Goes to Main Menu (NOT back to amount) |
| Debt description step | `🔙 بازگشت به منو` | Goes to Main Menu (NOT back to party) |
| Debt due_date step | `🔙 بازگشت به منو` | Goes to Main Menu (NOT back to description) |
| Card number step | `🔙 بازگشت` | Goes to name_choice (correct step-back) |
| Card sheba step | `🔙 بازگشت` | Goes to card_number (correct step-back) |

**Issue:** In Income/Expense/Debt/Receivable flows, the `🔙 بازگشت به منو` button in middle steps clears state and returns to Main Menu instead of going to the previous step. Only `❌ انصراف` should do this. The `🔙 بازگشت` (without "به منو") correctly goes back one step, but it's not consistently available in all middle steps.

### 8.3 Inconsistent Cancel Destination

| Flow | Cancel Destination |
|------|-------------------|
| Income, Expense, Debt, Receivable | Main Menu |
| Customer Management sub-flows | Customer Menu (not Main Menu) |
| Card Management sub-flows | Card Menu (not Main Menu) |
| Search | Main Menu |

This is actually **intentional** — sub-menus return to their parent menu on cancel, while top-level flows return to Main Menu. However, the behavior is not uniform.

### 8.4 Inconsistent Photo Step Handling

- Income and Expense photo steps handle cancel/back inline (duplicated code)
- `_process_photo_step()` helper exists but is **never called** — the logic is copy-pasted in each handler
- Debt and Receivable photo steps also have inline handling

### 8.5 Missing Back Navigation in Some Steps

- Debt/Receivable `amount` step: Only `cancel_menu`, no back (correct — it's the first step)
- Debt/Receivable `party` step: Has `cancel_back_menu` but "back" goes to Main Menu, not to amount
- Debt/Receivable `description` step: Has `cancel_back_menu` but "back" goes to Main Menu, not to party

### 8.6 Dual Keyboard Display

- Dashboard shows `export_menu` (inline) AND `main_menu` (reply) simultaneously
- Backup shows `backup_menu` (inline) AND `main_menu` (reply) simultaneously
- Reports show `export_menu` (inline) after the report, but no reply keyboard immediately

### 8.7 Unused Components

- `pagination_keyboard()` is defined but never used in any handler
- `card_copy_keyboard()` is defined but never used (individual copy buttons are used instead in `card_list_keyboard`)
- `_process_photo_step()` is defined but never called

### 8.8 Unused FSM States

| FSM Class | Unused State | Notes |
|-----------|-------------|-------|
| `IncomeForm` | `confirm` | Income is saved directly after photo step, no confirmation |
| `ExpenseForm` | `confirm` | Expense is saved directly after photo step, no confirmation |
| `CustomerForm` | `confirm` | Customer is saved directly after notes step, no confirmation |
| `CustomerEditForm` | `phone`, `address`, `notes` | Only `select` and `name` are used; edit is name-only |
| `CardEditForm` | `select` | Edit flow goes directly to `field` state (no selection step) |
| `DebtForm` | `customer_id` | Defined but party name is stored as text, not linked to customer ID |
| `ReceivableForm` | `customer_id` | Same as DebtForm |

### 8.9 Menu vs Submenu Back Text Inconsistency

- Some sub-menus use `🔙 بازگشت به منو` to return to their parent
- Customer menu: Cancel in add/edit/delete goes to `customer_menu`, but "back to menu" goes to `main_menu`
- Card menu: Cancel goes to `card_menu`, but "back to menu" goes to `main_menu`

### 8.10 Summary of All FSM State Groups

| # | FSM Class | States | Used In |
|---|-----------|--------|---------|
| 1 | `IncomeForm` | amount, description, category, photo, *(confirm unused)* | Income registration |
| 2 | `ExpenseForm` | amount, description, category, photo, *(confirm unused)* | Expense registration |
| 3 | `DebtForm` | amount, party, description, due_date, photo, *(customer_id unused)*, confirm | Debt registration |
| 4 | `ReceivableForm` | amount, party, description, due_date, photo, *(customer_id unused)*, confirm | Receivable registration |
| 5 | `CustomerForm` | name, phone, address, notes, *(confirm unused)* | Customer add |
| 6 | `CustomerEditForm` | select, name, *(phone/address/notes unused)* | Customer edit |
| 7 | `CustomerDeleteForm` | select, confirm | Customer delete |
| 8 | `SearchForm` | query, transaction_type | Transaction search |
| 9 | `CustomerSearchForm` | query | Customer search |
| 10 | `DebtEditForm` | edit_id, amount, party, description, due_date, confirm, delete_confirm | Debt edit/delete |
| 11 | `ReceivableEditForm` | edit_id, amount, party, description, due_date, confirm, delete_confirm | Receivable edit/delete |
| 12 | `CardForm` | name_choice, name_manual, name_customer_select, card_number, sheba, confirm | Card registration |
| 13 | `CardEditForm` | *(select unused)*, field, value, confirm | Card edit |
| 14 | `CardDeleteForm` | select, confirm | Card delete |
| 15 | `CardSearchForm` | query | Card search |

**Total:** 15 FSM state groups, ~70 states (of which ~10 are unused).

---

## 9. Recommendations for Recreating This Menu System

### 9.1 Architecture

1. **Use two keyboard layers:**
   - **ReplyKeyboard** for main menu and sub-menus (persistent navigation)
   - **InlineKeyboard** for contextual actions (edit, delete, confirm, export)

2. **FSM (Finite State Machine) for multi-step forms:**
   - Define a `StatesGroup` class for each form flow
   - Use `state.set_state()` to advance through steps
   - Use `state.update_data()` to accumulate form data

### 9.2 Navigation Components to Implement

| Component | Type | Purpose |
|-----------|------|---------|
| `main_menu()` | ReplyKeyboard | Always-visible home menu |
| `back_menu()` | ReplyKeyboard | Single "Back to Menu" button |
| `cancel_menu()` | ReplyKeyboard | Single "Cancel" button |
| `cancel_back_menu()` | ReplyKeyboard | Cancel + Back buttons |
| `skip_menu()` | ReplyKeyboard | Skip + Cancel (for optional fields) |
| `confirm_keyboard()` | InlineKeyboard | Yes/No confirmation |

### 9.3 Navigation Rules to Follow

1. **Cancel (`❌ انصراف`)** → Clear FSM state → Return to Main Menu (or parent sub-menu)
2. **Back to Menu (`🔙 بازگشت به منو`)** → Clear FSM state → Return to Main Menu
3. **Back (`🔙 بازگشت`)** → Go to previous FSM state (step back)
4. **Skip (`⏭️`)** → Skip optional field → Move to next FSM state
5. **All operations end** → Return to Main Menu or parent sub-menu
6. **Unknown input** → Show Main Menu (fallback)

### 9.4 FSM Form Template

```
Step 1: amount       → cancel_menu
Step 2: description  → cancel_back_menu (or skip_menu if optional)
Step 3: category     → specialized_keyboard (with back button)
Step 4: photo        → skip_menu
Step 5: confirm      → confirm_keyboard (inline)
→ Save → Main Menu
```

### 9.5 Sub-Menu Pattern

```
Main Menu → Button → Sub-Menu (ReplyKeyboard)
  Sub-Menu → Item 1 → Action/Flow → Sub-Menu
  Sub-Menu → Item 2 → Action/Flow → Sub-Menu
  Sub-Menu → Back → Main Menu
```

### 9.6 List + Inline Actions Pattern

```
Main Menu → Button → List of items (each with InlineKeyboard)
  Inline: Edit → Field Selection (InlineKeyboard) → Enter Value → Confirm → Main Menu
  Inline: Delete → Confirm (InlineKeyboard) → Delete → Main Menu
  Inline: View → Show Details
```

### 9.7 Key Design Decisions

1. **All text is in Persian (Farsi)** — RTL layout
2. **Jalali (Persian) calendar** for all dates
3. **No persistent menu state** — ReplyKeyboard is always rebuilt
4. **FSM state cleared on any navigation action** — no stale state
5. **Inline keyboards for item-level actions** — ReplyKeyboard for navigation
6. **Confirmation required for all mutations** (save, delete)
7. **Photo upload is always optional** — skip button always provided
8. **Dynamic keyboards** — customer list and party selection built from DB data

### 9.8 Callback Data Naming Convention

```
{action}:{entity_id}
{action}:{entity_id}:{field}
{action}_{sub_action}
```

Examples:
- `edit_debt:123`
- `card_edit_field:5:name`
- `confirm_yes`
- `export_excel`
- `search_type_income`

### 9.9 File Structure Recommendation

```
handlers/
  main_handler.py      # All handlers in one file (current approach)
keyboards/
  markups.py           # All keyboard builders
utils/
  messages.py          # All message strings
config.py              # Settings
main.py                # Entry point
```

For a larger project, consider splitting handlers into separate files by feature (income.py, expense.py, customer.py, etc.) with a shared router.

### 9.10 Complete Handler Inventory (106 handlers)

#### Command Handlers (4)
| Trigger | Handler | Action |
|---------|---------|--------|
| `/start` | `cmd_start` | Welcome + Main Menu |
| `/menu` | `cmd_menu` | Clear state + Main Menu |
| `/help` | `cmd_help` | Help text + Main Menu |
| `/dashboard` | `show_dashboard` | Dashboard |
| `/report` | `show_report_menu` | Report menu |
| `/search` | `search_start` | Search flow |
| `/backup` | `backup_menu_handler` | Backup menu |

#### Main Menu Button Handlers (13)
| Button Text | Handler | Action |
|-------------|---------|--------|
| `💰 ثبت درآمد` | `income_start` | Start income FSM |
| `💸 ثبت هزینه` | `expense_start` | Start expense FSM |
| `📋 ثبت بدهی` | `debt_start` | Start debt FSM |
| `📌 ثبت طلب` | `receivable_start` | Start receivable FSM |
| `📋 لیست بدهی‌ها` | `debt_list` | Show debt list |
| `📌 لیست طلب‌ها` | `receivable_list` | Show receivable list |
| `👥 مدیریت مشتریان` | `customer_management` | Customer menu |
| `📊 داشبورد مالی` | `show_dashboard` | Dashboard |
| `💳 ثبت شماره کارت و شبا` | `card_info_menu` | Card menu |
| `📈 گزارش‌های مالی` | `show_report_menu` | Report menu |
| `🔍 جستجو` | `search_start` | Search flow |
| `💾 پشتیبان‌گیری` | `backup_menu_handler` | Backup menu |
| `⚙️ تنظیمات` | `settings_handler` | Settings menu |
| `🔙 بازگشت به منو` | `cmd_menu` | Clear state + Main Menu |

#### Customer Menu Handlers (6)
| Button Text | Handler | Action |
|-------------|---------|--------|
| `👤 افزودن مشتری` | `customer_add_start` | Start add customer FSM |
| `✏️ ویرایش مشتری` | `customer_edit_select` | Show customer select inline |
| `🗑 حذف مشتری` | `customer_delete_select` | Show customer select inline |
| `🔍 جستجوی مشتری` | `customer_search_start` | Start search FSM |
| `📋 لیست مشتریان` | `customer_list` | Show list |
| `🔙 بازگشت به منو` | `cmd_menu` | Clear state + Main Menu |

#### Card Menu Handlers (4)
| Button Text | Handler | Action |
|-------------|---------|--------|
| `➕ ثبت جدید` | `card_add_start` | Start add card FSM |
| `📋 لیست شماره کارت‌ها` | `card_list` | Show list |
| `🔍 جستجوی کارت` | `card_search_start` | Start search FSM |
| `🔙 بازگشت به منو` | `cmd_menu` | Clear state + Main Menu |

#### Report Menu Handlers (5)
| Button Text | Handler | Action |
|-------------|---------|--------|
| `📅 گزارش روزانه` | `report_daily` | Daily report |
| `📅 گزارش هفتگی` | `report_weekly` | Weekly report |
| `📅 گزارش ماهانه` | `report_monthly` | Monthly report |
| `📅 گزارش سالانه` | `report_yearly` | Yearly report |
| `🔙 بازگشت به منو` | `cmd_menu` | Clear state + Main Menu |

#### Settings Menu Handlers (3)
| Button Text | Handler | Action |
|-------------|---------|--------|
| `👤 اطلاعات کاربری` | `user_info` | Show user info |
| `📊 خلاصه حساب` | `account_summary` | Show dashboard |
| `🔙 بازگشت به منو` | `cmd_menu` | Clear state + Main Menu |

#### FSM Message Handlers (28)
| FSM State | Handler | Purpose |
|-----------|---------|---------|
| `IncomeForm.amount` | `income_amount` | Parse amount |
| `IncomeForm.description` | `income_description` | Capture description |
| `IncomeForm.category` | `income_category` | Select category |
| `IncomeForm.photo` | `income_photo` | Upload/skip photo + save |
| `ExpenseForm.amount` | `expense_amount` | Parse amount |
| `ExpenseForm.description` | `expense_description` | Capture description |
| `ExpenseForm.category` | `expense_category` | Select category |
| `ExpenseForm.photo` | `expense_photo` | Upload/skip photo + save |
| `DebtForm.amount` | `debt_amount` | Parse amount |
| `DebtForm.party` | `debt_party` | Select/enter party |
| `DebtForm.description` | `debt_description` | Capture description |
| `DebtForm.due_date` | `debt_due_date` | Enter due date |
| `DebtForm.photo` | `debt_photo` | Upload/skip photo + confirm |
| `ReceivableForm.amount` | `receivable_amount` | Parse amount |
| `ReceivableForm.party` | `receivable_party` | Select/enter party |
| `ReceivableForm.description` | `receivable_description` | Capture description |
| `ReceivableForm.due_date` | `receivable_due_date` | Enter due date |
| `ReceivableForm.photo` | `receivable_photo` | Upload/skip photo + confirm |
| `CustomerForm.name` | `customer_add_name` | Capture name |
| `CustomerForm.phone` | `customer_add_phone` | Capture/skip phone |
| `CustomerForm.address` | `customer_add_address` | Capture/skip address |
| `CustomerForm.notes` | `customer_add_notes` | Capture/skip notes + save |
| `CustomerEditForm.name` | `customer_edit_name` | Enter new name + save |
| `CustomerSearchForm.query` | `customer_search_result` | Search + show results |
| `SearchForm.query` | `search_query` | Capture query |
| `CardForm.*` | 6 handlers | Card add flow |
| `CardEditForm.value` | `card_edit_value_handler` | Enter new value |
| `CardSearchForm.query` | `card_search_result` | Search + show results |

#### FSM Callback Handlers (14)
| FSM State + Callback | Handler | Purpose |
|---------------------|---------|---------|
| `DebtForm.confirm` | `debt_confirm` | Confirm debt save |
| `ReceivableForm.confirm` | `receivable_confirm` | Confirm receivable save |
| `DebtEditForm.edit_id` + `edit_field:*` | `edit_field_selected` | Select field to edit |
| `ReceivableEditForm.edit_id` + `edit_field:*` | `edit_field_selected` | Select field to edit |
| `DebtEditForm.confirm` | `debt_edit_confirm` | Confirm edit save |
| `ReceivableEditForm.confirm` | `receivable_edit_confirm` | Confirm edit save |
| `DebtEditForm.delete_confirm` | `debt_delete_confirm` | Confirm delete |
| `ReceivableEditForm.delete_confirm` | `receivable_delete_confirm` | Confirm delete |
| `CustomerEditForm.select` + `edit_customer:*` | `customer_edit_callback` | Select customer |
| `CustomerDeleteForm.select` + `delete_customer:*` | `customer_delete_callback` | Select customer |
| `CustomerDeleteForm.confirm` | `customer_delete_execute` | Confirm delete |
| `SearchForm.transaction_type` | `search_type_selected` | Select type filter |
| `CardForm.confirm` | `card_confirm` | Confirm card save |
| `CardEditForm.field` + `card_edit_field:*` | `card_edit_field_selected` | Select field |
| `CardEditForm.confirm` | `card_edit_confirm` | Confirm edit save |
| `CardDeleteForm.confirm` | `card_delete_confirm` | Confirm delete |

#### Callback Handlers (not FSM-bound) (12)
| Callback Pattern | Handler | Purpose |
|-----------------|---------|---------|
| `edit_debt:*` | `debt_edit_callback` | Start debt edit |
| `edit_receivable:*` | `receivable_edit_callback` | Start receivable edit |
| `delete_debt:*` | `debt_delete_callback` | Start debt delete |
| `delete_receivable:*` | `receivable_delete_callback` | Start receivable delete |
| `view_photo:*` | `view_photo_callback` | View photo |
| `export_*` | `handle_export` | Export Excel/PDF |
| `backup_create` | `backup_create` | Create backup |
| `backup_restore` | `backup_restore` | Restore backup |
| `backup_list` | `backup_list` | List backups |
| `card_edit:*` | `card_edit_callback` | Start card edit |
| `card_delete:*` | `card_delete_callback` | Start card delete |
| `copy_card:*` / `copy_sheba:*` / `copy_sms:*` | `card_copy_callback` | Copy/SMS |

#### Fallback Handler (1)
| Trigger | Handler | Action |
|---------|---------|--------|
| Any unmatched message | `fallback_handler` | Show Main Menu (ignores pure numbers) |

### 9.11 Complete Button Text Reference

All button text strings used in the bot (for exact matching in handlers):

**Main Menu:**
```
💰 ثبت درآمد
💸 ثبت هزینه
📋 ثبت بدهی
📌 ثبت طلب
📋 لیست بدهی‌ها
📌 لیست طلب‌ها
👥 مدیریت مشتریان
📊 داشبورد مالی
💳 ثبت شماره کارت و شبا
📈 گزارش‌های مالی
🔍 جستجو
💾 پشتیبان‌گیری
⚙️ تنظیمات
```

**Navigation:**
```
❌ انصراف
🔙 بازگشت به منو
🔙 بازگشت
⏭️ رد کردن
⏭️ بدون عکس
📅 امروز
✏️ وارد دستی
```

**Customer Menu:**
```
👤 افزودن مشتری
✏️ ویرایش مشتری
🗑 حذف مشتری
🔍 جستجوی مشتری
📋 لیست مشتریان
```

**Card Menu:**
```
➕ ثبت جدید
📋 لیست شماره کارت‌ها
🔍 جستجوی کارت
```

**Card Name Choice:**
```
✏️ ورود دستی نام
👥 انتخاب از مشتریان
```

**Report Menu:**
```
📅 گزارش روزانه
📅 گزارش هفتگی
📅 گزارش ماهانه
📅 گزارش سالانه
```

**Settings Menu:**
```
👤 اطلاعات کاربری
📊 خلاصه حساب
```

**Income Categories:**
```
فروش محصول
فروش خدمات
حقوق
سرمایه‌گذاری
پروژه
مشاوره
فروش آنلاین
سایر درآمدها
```

**Expense Categories:**
```
اجاره
حقوق کارکنان
خرید کالا
حمل و نقل
تبلیغات
خدمات
قبوض
تعمیرات
مواد اولیه
مالیات
بیمه
سایر هزینه‌ها
```
