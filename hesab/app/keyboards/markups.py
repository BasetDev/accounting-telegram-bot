"""Telegram keyboard markups for the accounting bot."""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    """Main menu keyboard."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="💰 ثبت درآمد"),
        KeyboardButton(text="💸 ثبت هزینه")
    )
    builder.row(
        KeyboardButton(text="💳 بدهی‌ها"),
        KeyboardButton(text="💵 طلب‌ها")
    )
    builder.row(
        KeyboardButton(text="👥 مدیریت مشتریان"),
        KeyboardButton(text="📊 داشبورد مالی")
    )
    builder.row(
        KeyboardButton(text="💳 ثبت شماره کارت و شبا"),
        KeyboardButton(text="📈 گزارش‌های مالی")
    )
    builder.row(
        KeyboardButton(text="🔍 جستجو"),
        KeyboardButton(text="💾 پشتیبان‌گیری")
    )
    builder.row(
        KeyboardButton(text="⚙️ تنظیمات")
    )
    return builder.as_markup(resize_keyboard=True)


def back_menu() -> ReplyKeyboardMarkup:
    """Simple back button."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🔙 بازگشت به منو"))
    return builder.as_markup(resize_keyboard=True)


def cancel_menu() -> ReplyKeyboardMarkup:
    """Cancel button for input flows."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ انصراف"))
    return builder.as_markup(resize_keyboard=True)


def cancel_back_menu() -> ReplyKeyboardMarkup:
    """Cancel and back buttons."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="❌ انصراف"),
        KeyboardButton(text="🔙 بازگشت به منو")
    )
    return builder.as_markup(resize_keyboard=True)


def customer_skip_menu() -> ReplyKeyboardMarkup:
    """Cancel, skip, and back buttons for optional fields in customer form."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭️ رد کردن"),
    )
    builder.row(
        KeyboardButton(text="🔙 بازگشت"),
        KeyboardButton(text="❌ انصراف")
    )
    return builder.as_markup(resize_keyboard=True)


def customer_menu() -> ReplyKeyboardMarkup:
    """Customer management menu."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="👤 افزودن مشتری"),
        KeyboardButton(text="✏️ ویرایش مشتری")
    )
    builder.row(
        KeyboardButton(text="🗑 حذف مشتری"),
        KeyboardButton(text="🔍 جستجوی مشتری")
    )
    builder.row(
        KeyboardButton(text="📋 لیست مشتریان"),
        KeyboardButton(text="🔙 بازگشت به منو")
    )
    return builder.as_markup(resize_keyboard=True)


def report_menu() -> ReplyKeyboardMarkup:
    """Financial reports menu."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📅 گزارش روزانه"),
        KeyboardButton(text="📅 گزارش هفتگی")
    )
    builder.row(
        KeyboardButton(text="📅 گزارش ماهانه"),
        KeyboardButton(text="📅 گزارش سالانه")
    )
    builder.row(
        KeyboardButton(text="🔙 بازگشت به منو")
    )
    return builder.as_markup(resize_keyboard=True)


def export_menu() -> InlineKeyboardMarkup:
    """Export options inline keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Excel", callback_data="export_excel"),
        InlineKeyboardButton(text="📄 PDF", callback_data="export_pdf")
    )
    return builder.as_markup()


def debt_reports_submenu() -> InlineKeyboardMarkup:
    """Debt reports submenu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 گزارش کلی", callback_data="debt_rpt_summary"),
        InlineKeyboardButton(text="⏳ بدهی‌های فعال", callback_data="debt_rpt_active")
    )
    builder.row(
        InlineKeyboardButton(text="✅ تسویه شده", callback_data="debt_rpt_settled"),
        InlineKeyboardButton(text="🔴 سررسید گذشته", callback_data="debt_rpt_overdue")
    )
    builder.row(
        InlineKeyboardButton(text="⏰ سررسید امروز", callback_data="debt_rpt_due_today"),
        InlineKeyboardButton(text="📅 سررسید این هفته", callback_data="debt_rpt_due_week")
    )
    builder.row(
        InlineKeyboardButton(text="👥 بر اساس مشتری", callback_data="debt_rpt_by_customer"),
        InlineKeyboardButton(text="🏷 بر اساس دسته‌بندی", callback_data="debt_rpt_by_category")
    )
    builder.row(
        InlineKeyboardButton(text="💰 پرداخت‌ها", callback_data="debt_rpt_payments"),
        InlineKeyboardButton(text="📊 مانده بدهی", callback_data="debt_rpt_remaining")
    )
    builder.row(
        InlineKeyboardButton(text="📅 گزارش روزانه", callback_data="debt_rpt_daily"),
        InlineKeyboardButton(text="📅 گزارش هفتگی", callback_data="debt_rpt_weekly")
    )
    builder.row(
        InlineKeyboardButton(text="📅 گزارش ماهانه", callback_data="debt_rpt_monthly"),
        InlineKeyboardButton(text="📅 گزارش سالانه", callback_data="debt_rpt_yearly")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت به منوی بدهی‌ها", callback_data="debt_rpt_back")
    )
    return builder.as_markup()


def debt_report_export_menu(report_type: str) -> InlineKeyboardMarkup:
    """Export options for debt reports."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Excel", callback_data=f"debt_rpt_export_excel:{report_type}"),
        InlineKeyboardButton(text="📄 PDF", callback_data=f"debt_rpt_export_pdf:{report_type}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت به منوی گزارش‌ها", callback_data="debt_rpt_menu")
    )
    return builder.as_markup()


def transaction_type_keyboard() -> InlineKeyboardMarkup:
    """Transaction type filter for search."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 درآمد", callback_data="search_type_income"),
        InlineKeyboardButton(text="💸 هزینه", callback_data="search_type_expense")
    )
    builder.row(
        InlineKeyboardButton(text="📋 بدهی", callback_data="search_type_debt"),
        InlineKeyboardButton(text="📌 طلب", callback_data="search_type_receivable")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 همه", callback_data="search_type_all")
    )
    return builder.as_markup()


def income_categories() -> ReplyKeyboardMarkup:
    """Income category selection."""
    builder = ReplyKeyboardBuilder()
    categories = [
        "فروش محصول", "فروش خدمات", "حقوق",
        "سرمایه‌گذاری", "پروژه", "مشاوره",
        "فروش آنلاین", "سایر درآمدها"
    ]
    for cat in categories:
        builder.row(KeyboardButton(text=cat))
    builder.row(KeyboardButton(text="❌ انصراف"), KeyboardButton(text="🔙 بازگشت"))
    return builder.as_markup(resize_keyboard=True)


def expense_categories() -> ReplyKeyboardMarkup:
    """Expense category selection."""
    builder = ReplyKeyboardBuilder()
    categories = [
        "اجاره", "حقوق کارکنان", "خرید کالا",
        "حمل و نقل", "تبلیغات", "خدمات",
        "قبوض", "تعمیرات", "مواد اولیه",
        "مالیات", "بیمه", "سایر هزینه‌ها"
    ]
    for cat in categories:
        builder.row(KeyboardButton(text=cat))
    builder.row(KeyboardButton(text="❌ انصراف"), KeyboardButton(text="🔙 بازگشت"))
    return builder.as_markup(resize_keyboard=True)


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Yes/No confirmation."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ تأیید", callback_data="confirm_yes"),
        InlineKeyboardButton(text="❌ رد", callback_data="confirm_no")
    )
    return builder.as_markup()


def due_date_keyboard() -> ReplyKeyboardMarkup:
    """Due date options: today or manual input."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📅 امروز"))
    builder.row(KeyboardButton(text="❌ انصراف"), KeyboardButton(text="🔙 بازگشت به منو"))
    return builder.as_markup(resize_keyboard=True)


def party_keyboard(customers: list) -> ReplyKeyboardMarkup:
    """Party name selection from customer list + manual input."""
    builder = ReplyKeyboardBuilder()
    for c in customers:
        builder.row(KeyboardButton(text=c["full_name"]))
    builder.row(KeyboardButton(text="✏️ وارد دستی"))
    builder.row(KeyboardButton(text="❌ انصراف"), KeyboardButton(text="🔙 بازگشت به منو"))
    return builder.as_markup(resize_keyboard=True)


def pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Pagination inline keyboard."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"{prefix}_page_{page-1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="▶️ بعدی", callback_data=f"{prefix}_page_{page+1}"))
    if buttons:
        builder.row(*buttons)
    return builder.as_markup()


def backup_menu() -> InlineKeyboardMarkup:
    """Backup options."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📦 پشتیبان کامل", callback_data="backup_create_full"),
        InlineKeyboardButton(text="🗄 پشتیبان دیتابیس", callback_data="backup_create_db")
    )
    builder.row(
        InlineKeyboardButton(text="🖼 پشتیبان رسانه", callback_data="backup_create_media"),
        InlineKeyboardButton(text="📋 لیست پشتیبان‌ها", callback_data="backup_list")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 بازیابی", callback_data="backup_restore"),
        InlineKeyboardButton(text="📊 آمار پشتیبان‌ها", callback_data="backup_stats")
    )
    builder.row(
        InlineKeyboardButton(text="🧹 پاکسازی قدیمی‌ها", callback_data="backup_cleanup")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")
    )
    return builder.as_markup()


def backup_list_keyboard(backups: list) -> InlineKeyboardMarkup:
    """Keyboard for backup list with actions per backup."""
    builder = InlineKeyboardBuilder()
    for b in backups[:10]:
        size_kb = b["file_size"] / 1024
        label = f"📦 {b['jalali_date']} ({size_kb:.0f}KB)"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=f"backup_info:{b['filename']}"),
        )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="backup_menu_back")
    )
    return builder.as_markup()


def backup_action_keyboard(filename: str) -> InlineKeyboardMarkup:
    """Action keyboard for a specific backup."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬇️ دانلود", callback_data=f"backup_download:{filename}"),
        InlineKeyboardButton(text="🔍 اعتبارسنجی", callback_data=f"backup_verify:{filename}")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 بازیابی", callback_data=f"backup_restore_file:{filename}"),
        InlineKeyboardButton(text="🗑 حذف", callback_data=f"backup_delete:{filename}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت به لیست", callback_data="backup_list")
    )
    return builder.as_markup()


def backup_restore_confirm_keyboard(filename: str) -> InlineKeyboardMarkup:
    """Confirmation keyboard for restore."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ بله، بازیابی شود", callback_data=f"backup_restore_confirm:{filename}"),
        InlineKeyboardButton(text="❌ انصراف", callback_data="backup_list")
    )
    return builder.as_markup()


def backup_delete_confirm_keyboard(filename: str) -> InlineKeyboardMarkup:
    """Confirmation keyboard for delete."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ بله، حذف شود", callback_data=f"backup_delete_confirm:{filename}"),
        InlineKeyboardButton(text="❌ انصراف", callback_data=f"backup_info:{filename}")
    )
    return builder.as_markup()


def settings_menu() -> ReplyKeyboardMarkup:
    """Settings menu."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="👤 اطلاعات کاربری"),
        KeyboardButton(text="📊 خلاصه حساب")
    )
    builder.row(
        KeyboardButton(text="🔙 بازگشت به منو")
    )
    return builder.as_markup(resize_keyboard=True)


def debt_submenu() -> InlineKeyboardMarkup:
    """Debt submenu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🟡 بدهی‌های فعال", callback_data="debt_active"),
        InlineKeyboardButton(text="🔴 سررسید گذشته", callback_data="debt_overdue")
    )
    builder.row(
        InlineKeyboardButton(text="🟢 تسویه شده", callback_data="debt_settled_cat"),
        InlineKeyboardButton(text="⏰ سررسید امروز", callback_data="debt_due_today")
    )
    builder.row(
        InlineKeyboardButton(text="📅 سررسید این هفته", callback_data="debt_due_week"),
        InlineKeyboardButton(text="📋 همه بدهی‌ها", callback_data="debt_all_cat")
    )
    builder.row(
        InlineKeyboardButton(text="💳 پرداخت بدهی", callback_data="debt_pay_cat"),
        InlineKeyboardButton(text="📊 تسویه‌ها", callback_data="settlement_debt")
    )
    builder.row(
        InlineKeyboardButton(text="📜 پرداخت‌های انجام شده", callback_data="debt_view_payments")
    )
    builder.row(
        InlineKeyboardButton(text="📊 گزارش بدهی‌ها", callback_data="debt_reports"),
        InlineKeyboardButton(text="📋 ثبت بدهی جدید", callback_data="debt_register")
    )
    return builder.as_markup()


def receivable_submenu() -> InlineKeyboardMarkup:
    """Receivable submenu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🟡 طلب‌های فعال", callback_data="receivable_active"),
        InlineKeyboardButton(text="🔴 سررسید گذشته", callback_data="receivable_overdue")
    )
    builder.row(
        InlineKeyboardButton(text="🟢 تسویه شده", callback_data="receivable_settled_cat"),
        InlineKeyboardButton(text="⏰ سررسید امروز", callback_data="receivable_due_today")
    )
    builder.row(
        InlineKeyboardButton(text="📅 سررسید این هفته", callback_data="receivable_due_week"),
        InlineKeyboardButton(text="📋 همه طلب‌ها", callback_data="receivable_all_cat")
    )
    builder.row(
        InlineKeyboardButton(text="💵 دریافت طلب", callback_data="receivable_receive_cat"),
        InlineKeyboardButton(text="📊 تسویه‌ها", callback_data="settlement_recv")
    )
    builder.row(
        InlineKeyboardButton(text="📜 دریافت‌های انجام شده", callback_data="recv_view_payments")
    )
    builder.row(
        InlineKeyboardButton(text="📊 گزارش طلب‌ها", callback_data="receivable_reports"),
        InlineKeyboardButton(text="📌 ثبت طلب جدید", callback_data="receivable_register")
    )
    return builder.as_markup()


def receivable_reports_submenu() -> InlineKeyboardMarkup:
    """Receivable reports submenu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 گزارش کلی", callback_data="recv_rpt_summary"),
        InlineKeyboardButton(text="⏳ طلب‌های فعال", callback_data="recv_rpt_active")
    )
    builder.row(
        InlineKeyboardButton(text="✅ وصول شده", callback_data="recv_rpt_settled"),
        InlineKeyboardButton(text="🔴 سررسید گذشته", callback_data="recv_rpt_overdue")
    )
    builder.row(
        InlineKeyboardButton(text="⏰ سررسید امروز", callback_data="recv_rpt_due_today"),
        InlineKeyboardButton(text="📅 سررسید این هفته", callback_data="recv_rpt_due_week")
    )
    builder.row(
        InlineKeyboardButton(text="👥 بر اساس مشتری", callback_data="recv_rpt_by_customer"),
        InlineKeyboardButton(text="🏷 بر اساس دسته‌بندی", callback_data="recv_rpt_by_category")
    )
    builder.row(
        InlineKeyboardButton(text="💰 دریافت‌ها", callback_data="recv_rpt_payments"),
        InlineKeyboardButton(text="📊 مانده طلب", callback_data="recv_rpt_remaining")
    )
    builder.row(
        InlineKeyboardButton(text="📅 گزارش روزانه", callback_data="recv_rpt_daily"),
        InlineKeyboardButton(text="📅 گزارش هفتگی", callback_data="recv_rpt_weekly")
    )
    builder.row(
        InlineKeyboardButton(text="📅 گزارش ماهانه", callback_data="recv_rpt_monthly"),
        InlineKeyboardButton(text="📅 گزارش سالانه", callback_data="recv_rpt_yearly")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت به منوی طلب‌ها", callback_data="recv_rpt_back")
    )
    return builder.as_markup()


def recv_report_export_menu(report_type: str) -> InlineKeyboardMarkup:
    """Export options for receivable reports."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Excel", callback_data=f"recv_rpt_export_excel:{report_type}"),
        InlineKeyboardButton(text="📄 PDF", callback_data=f"recv_rpt_export_pdf:{report_type}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت به منوی گزارش‌ها", callback_data="recv_rpt_menu")
    )
    return builder.as_markup()


# --- Category & Subcategory keyboards for Debt ---

DEBT_CATEGORIES = {
    "🏢 کسب‌وکار": [
        "تأمین‌کنندگان", "خرید ضایعات", "حمل و نقل",
        "حقوق کارکنان", "مالیات", "چک‌های صادره", "سایر"
    ],
    "👤 شخصی": [
        "وام شخصی", "خانواده", "دوستان", "سایر"
    ],
    "سایر": []
}

RECEIVABLE_CATEGORIES = {
    "🏢 کسب‌وکار": [
        "فروش ضایعات", "مشتریان", "چک‌های دریافتی", "پروژه‌ها", "سایر"
    ],
    "👤 شخصی": [
        "دوستان", "خانواده", "وام شخصی", "سایر"
    ],
    "سایر": []
}


def debt_category_keyboard() -> InlineKeyboardMarkup:
    """Top-level category selection for debt."""
    builder = InlineKeyboardBuilder()
    for cat_name in DEBT_CATEGORIES:
        builder.row(InlineKeyboardButton(text=cat_name, callback_data=f"debt_cat:{cat_name}"))
    builder.row(InlineKeyboardButton(text="❌ انصراف", callback_data="debt_cat:cancel"))
    return builder.as_markup()


def debt_subcategory_keyboard(category: str) -> InlineKeyboardMarkup:
    """Subcategory selection based on chosen debt category."""
    builder = InlineKeyboardBuilder()
    subs = DEBT_CATEGORIES.get(category, [])
    for sub in subs:
        builder.row(InlineKeyboardButton(text=sub, callback_data=f"debt_sub:{sub}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="debt_sub:back"))
    return builder.as_markup()


def debt_category_filter_keyboard(prefix: str) -> InlineKeyboardMarkup:
    """Category filter keyboard for debt list sections (all/settled/pay)."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 همه دسته‌ها", callback_data=f"{prefix}_cat:all"))
    for cat_name in DEBT_CATEGORIES:
        builder.row(InlineKeyboardButton(text=cat_name, callback_data=f"{prefix}_cat:{cat_name}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"{prefix}_cat:back"))
    return builder.as_markup()


def debt_subcategory_filter_keyboard(prefix: str, category: str) -> InlineKeyboardMarkup:
    """Subcategory filter keyboard for debt list sections."""
    builder = InlineKeyboardBuilder()
    subs = DEBT_CATEGORIES.get(category, [])
    builder.row(InlineKeyboardButton(text="📋 همه زیرمجموعه‌ها", callback_data=f"{prefix}_sub:all"))
    for sub in subs:
        builder.row(InlineKeyboardButton(text=sub, callback_data=f"{prefix}_sub:{sub}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"{prefix}_sub:back"))
    return builder.as_markup()


def receivable_category_keyboard() -> InlineKeyboardMarkup:
    """Top-level category selection for receivable."""
    builder = InlineKeyboardBuilder()
    for cat_name in RECEIVABLE_CATEGORIES:
        builder.row(InlineKeyboardButton(text=cat_name, callback_data=f"recv_cat:{cat_name}"))
    builder.row(InlineKeyboardButton(text="❌ انصراف", callback_data="recv_cat:cancel"))
    return builder.as_markup()


def receivable_subcategory_keyboard(category: str) -> InlineKeyboardMarkup:
    """Subcategory selection based on chosen receivable category."""
    builder = InlineKeyboardBuilder()
    subs = RECEIVABLE_CATEGORIES.get(category, [])
    for sub in subs:
        builder.row(InlineKeyboardButton(text=sub, callback_data=f"recv_sub:{sub}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="recv_sub:back"))
    return builder.as_markup()


def receivable_category_filter_keyboard(prefix: str) -> InlineKeyboardMarkup:
    """Category filter keyboard for receivable list sections (all/settled/receive)."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 همه دسته‌ها", callback_data=f"{prefix}_cat:all"))
    for cat_name in RECEIVABLE_CATEGORIES:
        builder.row(InlineKeyboardButton(text=cat_name, callback_data=f"{prefix}_cat:{cat_name}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"{prefix}_cat:back"))
    return builder.as_markup()


def receivable_subcategory_filter_keyboard(prefix: str, category: str) -> InlineKeyboardMarkup:
    """Subcategory filter keyboard for receivable list sections."""
    builder = InlineKeyboardBuilder()
    subs = RECEIVABLE_CATEGORIES.get(category, [])
    builder.row(InlineKeyboardButton(text="📋 همه زیرمجموعه‌ها", callback_data=f"{prefix}_sub:all"))
    for sub in subs:
        builder.row(InlineKeyboardButton(text=sub, callback_data=f"{prefix}_sub:{sub}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"{prefix}_sub:back"))
    return builder.as_markup()


def card_info_choice_keyboard(cards: list) -> ReplyKeyboardMarkup:
    """Keyboard for choosing card/IBAN during debt/receivable registration.

    Shows existing saved cards as options, plus manual entry and skip.
    """
    builder = ReplyKeyboardBuilder()
    for card in cards[:10]:  # Limit to 10 cards
        label = card["name"]
        if card["card_number"]:
            label += f" | {card['card_number'][-4:]}****"
        if card["sheba"]:
            label += f" | شبا"
        builder.row(KeyboardButton(text=label))
    builder.row(KeyboardButton(text="✏️ ورود دستی کارت/شبا"))
    builder.row(KeyboardButton(text="⏭️ رد کردن"))
    builder.row(KeyboardButton(text="❌ انصراف"))
    return builder.as_markup(resize_keyboard=True)


def card_select_keyboard(cards: list) -> ReplyKeyboardMarkup:
    """Keyboard for selecting card number from saved cards during debt/receivable registration."""
    builder = ReplyKeyboardBuilder()
    seen_cards = set()
    for card in cards[:10]:
        if card["card_number"] and card["card_number"] not in seen_cards:
            seen_cards.add(card["card_number"])
            label = f"💳 {card['card_number'][-4:]}****"
            if card["name"]:
                label = f"{card['name']} | {card['card_number'][-4:]}****"
            builder.row(KeyboardButton(text=label))
    builder.row(KeyboardButton(text="✏️ ورود دستی شماره کارت"))
    builder.row(KeyboardButton(text="⏭️ رد کردن"))
    builder.row(KeyboardButton(text="❌ انصراف"))
    return builder.as_markup(resize_keyboard=True)


def sheba_select_keyboard(cards: list) -> ReplyKeyboardMarkup:
    """Keyboard for selecting sheba/IBAN from saved cards during debt/receivable registration."""
    builder = ReplyKeyboardBuilder()
    seen_sheba = set()
    for card in cards[:10]:
        if card["sheba"] and card["sheba"] not in seen_sheba:
            seen_sheba.add(card["sheba"])
            label = f"🏦 IR{card['sheba'][-4:]}****"
            if card["name"]:
                label = f"{card['name']} | IR{card['sheba'][-4:]}****"
            builder.row(KeyboardButton(text=label))
    builder.row(KeyboardButton(text="✏️ ورود دستی شماره شبا"))
    builder.row(KeyboardButton(text="⏭️ رد کردن"))
    builder.row(KeyboardButton(text="❌ انصراف"))
    return builder.as_markup(resize_keyboard=True)


def bank_name_select_keyboard(bank_names: list) -> ReplyKeyboardMarkup:
    """Keyboard for selecting bank name from previously saved banks."""
    builder = ReplyKeyboardBuilder()
    for name in bank_names[:10]:
        builder.row(KeyboardButton(text=f"🏛 {name}"))
    builder.row(KeyboardButton(text="✏️ ورود دستی نام بانک"))
    builder.row(KeyboardButton(text="⏭️ رد کردن"))
    builder.row(KeyboardButton(text="❌ انصراف"))
    return builder.as_markup(resize_keyboard=True)


def receipt_skip_menu() -> ReplyKeyboardMarkup:
    """Keyboard for unified receipt step - text, photo, or skip."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="⏭️ بدون رسید"))
    builder.row(KeyboardButton(text="🔙 بازگشت"), KeyboardButton(text="❌ انصراف"))
    return builder.as_markup(resize_keyboard=True)


def photo_skip_menu() -> ReplyKeyboardMarkup:
    """Keyboard with skip photo and cancel options."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭️ بدون عکس"),
        KeyboardButton(text="❌ انصراف")
    )
    builder.row(
        KeyboardButton(text="🔙 بازگشت به منو"),
    )
    return builder.as_markup(resize_keyboard=True)


def card_skip_menu() -> ReplyKeyboardMarkup:
    """Keyboard with skip options for card/sheba input."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭️ رد کردن"),
    )
    builder.row(
        KeyboardButton(text="🔙 بازگشت"),
        KeyboardButton(text="❌ انصراف")
    )
    return builder.as_markup(resize_keyboard=True)


def customer_select_keyboard(customers: list, action: str = "edit") -> InlineKeyboardMarkup:
    """Inline keyboard for selecting a customer by name.

    If multiple customers share the same name, appends phone number or ID to distinguish.
    """
    builder = InlineKeyboardBuilder()

    name_counts = {}
    for c in customers:
        name_counts[c["full_name"]] = name_counts.get(c["full_name"], 0) + 1

    prefix = "edit_customer" if action == "edit" else "delete_customer"

    for c in customers:
        label = c["full_name"]
        if name_counts[c["full_name"]] > 1:
            if c["phone"]:
                label = f"{c['full_name']} ({c['phone']})"
            else:
                label = f"{c['full_name']} (🆔 {c['id']})"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"{prefix}:{c['id']}"))

    builder.row(InlineKeyboardButton(text="❌ انصراف", callback_data=f"{prefix}:cancel"))
    return builder.as_markup()


def edit_field_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting which field to edit."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 مبلغ", callback_data="edit_field:amount"),
        InlineKeyboardButton(text="👤 طرف حساب", callback_data="edit_field:party")
    )
    builder.row(
        InlineKeyboardButton(text="📝 توضیحات", callback_data="edit_field:description"),
        InlineKeyboardButton(text="📅 سررسید", callback_data="edit_field:due_date")
    )
    builder.row(
        InlineKeyboardButton(text="📸 عکس", callback_data="edit_field:photo"),
        InlineKeyboardButton(text="🏷 دسته‌بندی", callback_data="edit_field:category")
    )
    builder.row(
        InlineKeyboardButton(text="💳 شماره کارت", callback_data="edit_field:card_number"),
        InlineKeyboardButton(text="🏦 شبا", callback_data="edit_field:sheba")
    )
    builder.row(
        InlineKeyboardButton(text="🏛 بانک", callback_data="edit_field:bank_name")
    )
    builder.row(
        InlineKeyboardButton(text="✅ تأیید و ذخیره", callback_data="edit_field:save")
    )
    return builder.as_markup()


def edit_photo_keyboard(has_photo: bool = False) -> ReplyKeyboardMarkup:
    """Keyboard for photo management during edit."""
    builder = ReplyKeyboardBuilder()
    if has_photo:
        builder.row(KeyboardButton(text="🗑 حذف عکس"))
    builder.row(KeyboardButton(text="⏭️ بدون تغییر"))
    builder.row(
        KeyboardButton(text="❌ انصراف"),
        KeyboardButton(text="🔙 بازگشت به منو")
    )
    return builder.as_markup(resize_keyboard=True)


def card_menu() -> ReplyKeyboardMarkup:
    """Card management menu."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="➕ ثبت جدید"),
        KeyboardButton(text="📋 لیست شماره کارت‌ها")
    )
    builder.row(
        KeyboardButton(text="🔍 جستجوی کارت"),
        KeyboardButton(text="🔙 بازگشت به منو")
    )
    return builder.as_markup(resize_keyboard=True)


def card_submenu() -> InlineKeyboardMarkup:
    """Card section submenu (consistent with debt/receivable submenus)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 همه کارت‌ها", callback_data="card_all"),
        InlineKeyboardButton(text="➕ ثبت جدید", callback_data="card_register")
    )
    builder.row(
        InlineKeyboardButton(text="🔍 جستجوی کارت", callback_data="card_search_inline"),
        InlineKeyboardButton(text="📊 گزارش کارت‌ها", callback_data="card_reports")
    )
    return builder.as_markup()


def card_sort_keyboard(cache_key: str = None) -> InlineKeyboardMarkup:
    """Keyboard for sorting options in card list."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔤 نام", callback_data=f"card_sort:{cache_key}:name"),
        InlineKeyboardButton(text="📊 تعداد", callback_data=f"card_sort:{cache_key}:count")
    )
    builder.row(
        InlineKeyboardButton(text="🏛 بانک", callback_data=f"card_sort:{cache_key}:bank"),
        InlineKeyboardButton(text="📅 تاریخ", callback_data=f"card_sort:{cache_key}:date")
    )
    back_cb = f"card_back:{cache_key}" if cache_key else "card_group_back"
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data=back_cb)
    )
    return builder.as_markup()


def card_filter_keyboard(cache_key: str = None) -> InlineKeyboardMarkup:
    """Keyboard for filtering options in card list."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 فقط کارت‌دار", callback_data=f"card_filter:{cache_key}:has_card"),
        InlineKeyboardButton(text="🏦 فقط شبا‌دار", callback_data=f"card_filter:{cache_key}:has_sheba")
    )
    builder.row(
        InlineKeyboardButton(text="💳+🏦 هر دو", callback_data=f"card_filter:{cache_key}:both"),
        InlineKeyboardButton(text="📋 همه", callback_data=f"card_filter:{cache_key}:all")
    )
    back_cb = f"card_back:{cache_key}" if cache_key else "card_group_back"
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data=back_cb)
    )
    return builder.as_markup()


def card_owner_overview_keyboard(buttons_data: list, cache_key: str) -> InlineKeyboardMarkup:
    """Keyboard for owner overview with sort/filter options."""
    builder = InlineKeyboardBuilder()
    for item in buttons_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(
        InlineKeyboardButton(text="🔃 مرتب‌سازی", callback_data=f"card_sort_menu:{cache_key}"),
        InlineKeyboardButton(text="🔽 فیلتر", callback_data=f"card_filter_menu:{cache_key}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="card_group_back")
    )
    return builder.as_markup()


def card_linked_txn_keyboard(card_id: int, txn_type: str, cache_key: str = None, safe_name: str = None) -> InlineKeyboardMarkup:
    """Keyboard for viewing linked transactions from card detail."""
    builder = InlineKeyboardBuilder()
    back_cb = f"card_back_from_linked:{card_id}"
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت به کارت", callback_data=back_cb)
    )
    return builder.as_markup()


def card_customer_keyboard(customers_data: list) -> InlineKeyboardMarkup:
    """Keyboard for selecting a customer/name to view their cards."""
    builder = InlineKeyboardBuilder()
    for item in customers_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="card_group_back"))
    return builder.as_markup()


def card_items_keyboard(items_data: list, cache_key: str) -> InlineKeyboardMarkup:
    """Keyboard showing cards of a customer with detail buttons."""
    builder = InlineKeyboardBuilder()
    for item in items_data:
        builder.row(
            InlineKeyboardButton(text=item["label"], callback_data=item["detail_callback"])
        )
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به لیست", callback_data=f"card_back:{cache_key}"))
    return builder.as_markup()


def card_detail_keyboard(card_id: int, cache_key: str = None, safe_name: str = None,
                         back_short_id: str = None, linked_short_id: str = None,
                         debt_count: int = 0, recv_count: int = 0, payment_count: int = 0) -> InlineKeyboardMarkup:
    """Keyboard for individual card detail view with all actions."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 کپی کارت", callback_data=f"copy_card:{card_id}"),
        InlineKeyboardButton(text="📋 کپی شبا", callback_data=f"copy_sheba:{card_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📩 ارسال پیامک", callback_data=f"copy_sms:{card_id}"),
    )
    # Build context suffix for linked transaction callbacks
    ctx = f":{linked_short_id}" if linked_short_id else ""
    # Linked transaction buttons
    linked_buttons = []
    if debt_count > 0:
        linked_buttons.append(InlineKeyboardButton(text=f"📋 بدهی‌ها ({debt_count})", callback_data=f"card_linked_debt:{card_id}{ctx}"))
    if recv_count > 0:
        linked_buttons.append(InlineKeyboardButton(text=f"📌 طلب‌ها ({recv_count})", callback_data=f"card_linked_recv:{card_id}{ctx}"))
    if linked_buttons:
        builder.row(*linked_buttons)
    if payment_count > 0:
        builder.row(
            InlineKeyboardButton(text=f"💳 پرداخت‌ها ({payment_count})", callback_data=f"card_linked_pay:{card_id}{ctx}")
        )
    builder.row(
        InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"card_edit:{card_id}"),
        InlineKeyboardButton(text="🗑 حذف", callback_data=f"card_delete:{card_id}")
    )
    if back_short_id:
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"card_detail_back:{back_short_id}")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="card_group_back")
        )
    return builder.as_markup()


def card_name_choice_keyboard() -> ReplyKeyboardMarkup:
    """Choose how to enter the name: manual or from customers."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="✏️ ورود دستی نام"),
        KeyboardButton(text="👥 انتخاب از مشتریان")
    )
    builder.row(
        KeyboardButton(text="❌ انصراف"),
        KeyboardButton(text="🔙 بازگشت به منو")
    )
    return builder.as_markup(resize_keyboard=True)


def card_list_keyboard(card_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard for each card info item with copy and SMS options."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 کپی کارت", callback_data=f"copy_card:{card_id}"),
        InlineKeyboardButton(text="📋 کپی شبا", callback_data=f"copy_sheba:{card_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📩 ارسال پیامک", callback_data=f"copy_sms:{card_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"card_edit:{card_id}"),
        InlineKeyboardButton(text="🗑 حذف", callback_data=f"card_delete:{card_id}")
    )
    return builder.as_markup()


def card_copy_keyboard(card_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard with copy buttons for card and sheba."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 کپی شماره کارت", callback_data=f"copy_card:{card_id}"),
        InlineKeyboardButton(text="🏦 کپی شبا", callback_data=f"copy_sheba:{card_id}")
    )
    return builder.as_markup()


def card_edit_field_keyboard(card_id: int) -> InlineKeyboardMarkup:
    """Keyboard for selecting which field to edit in card info."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 نام", callback_data=f"card_edit_field:{card_id}:name"),
        InlineKeyboardButton(text="💳 شماره کارت", callback_data=f"card_edit_field:{card_id}:card")
    )
    builder.row(
        InlineKeyboardButton(text="🏦 شماره شبا", callback_data=f"card_edit_field:{card_id}:sheba"),
        InlineKeyboardButton(text="🏛 نام بانک", callback_data=f"card_edit_field:{card_id}:bank")
    )
    builder.row(
        InlineKeyboardButton(text="✅ تأیید و ذخیره", callback_data=f"card_edit_field:{card_id}:save")
    )
    return builder.as_markup()


def payment_select_keyboard(transactions: list, payments_data: dict) -> InlineKeyboardMarkup:
    """Keyboard for selecting a debt/receivable to pay.

    Args:
        transactions: list of Transaction objects
        payments_data: dict mapping txn_id -> remaining_amount
    """
    builder = InlineKeyboardBuilder()
    for txn in transactions:
        remaining = payments_data.get(txn["id"], txn["amount"])
        label = f"#{txn['id']} {txn['party_name'] or '-'} | {int(remaining):,} تومان"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"pay_select:{txn['id']}"))
    builder.row(InlineKeyboardButton(text="❌ انصراف", callback_data="pay_select:cancel"))
    return builder.as_markup()


def payment_type_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for choosing full or partial payment."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 پرداخت کامل", callback_data="pay_type:full"),
        InlineKeyboardButton(text="💰 پرداخت جزئی", callback_data="pay_type:partial")
    )
    builder.row(
        InlineKeyboardButton(text="❌ انصراف", callback_data="pay_type:cancel")
    )
    return builder.as_markup()


def payment_confirm_keyboard(txn_id: int = None, has_payment_info: bool = False) -> InlineKeyboardMarkup:
    """Yes/No confirmation for payment, with optional SMS copy button."""
    builder = InlineKeyboardBuilder()
    if has_payment_info and txn_id is not None:
        builder.row(
            InlineKeyboardButton(text="📩 پیامک", callback_data=f"pay_sms:{txn_id}")
        )
    builder.row(
        InlineKeyboardButton(text="✅ تأیید پرداخت", callback_data="pay_confirm_yes"),
        InlineKeyboardButton(text="❌ رد", callback_data="pay_confirm_no")
    )
    return builder.as_markup()


def debt_customer_keyboard(customers_data: list) -> InlineKeyboardMarkup:
    """Keyboard for selecting a customer to view their grouped debts."""
    builder = InlineKeyboardBuilder()
    for item in customers_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="debt_group_back"))
    return builder.as_markup()


def debt_customer_debts_keyboard(txns_data: list, back_callback: str = "debt_group_back") -> InlineKeyboardMarkup:
    """Keyboard showing individual debts of a customer with Details buttons."""
    builder = InlineKeyboardBuilder()
    for item in txns_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به مشتریان", callback_data=back_callback))
    return builder.as_markup()


def debt_detail_keyboard(txn_id: int, cache_key: str, safe_party: str,
                          has_photo: bool = False, remaining: float = None,
                          has_payment_info: bool = False,
                          has_payment_photo: bool = False,
                          back_callback: str = None) -> InlineKeyboardMarkup:
    """Keyboard for individual debt detail view with all actions."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if has_photo:
        buttons.append(InlineKeyboardButton(text="📸 عکس", callback_data=f"view_photo:{txn_id}"))
    if has_payment_photo:
        buttons.append(InlineKeyboardButton(text="📸 رسید پرداخت", callback_data=f"view_payment_photo:{txn_id}"))
    if has_payment_info:
        buttons.append(InlineKeyboardButton(text="📩 پیامک", callback_data=f"debt_sms:{txn_id}"))
    if remaining is not None and remaining > 0:
        buttons.append(InlineKeyboardButton(text="💳 پرداخت", callback_data=f"quick_pay_debt:{txn_id}"))
    if buttons:
        builder.row(*buttons)
    builder.row(
        InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit_debt:{txn_id}"),
        InlineKeyboardButton(text="🗑 حذف", callback_data=f"delete_debt:{txn_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📜 تاریخچه پرداخت", callback_data=f"debt_payment_history:{txn_id}")
    )
    if back_callback is None:
        back_callback = f"debt_detail_back:{cache_key}:{safe_party}"
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data=back_callback)
    )
    return builder.as_markup()


def debt_list_keyboard(txn_id: int, has_photo: bool = False, remaining: float = None, has_payment_info: bool = False) -> InlineKeyboardMarkup:
    """Inline keyboard for each debt item in the list."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if has_photo:
        buttons.append(InlineKeyboardButton(text="📸 عکس", callback_data=f"view_photo:{txn_id}"))
    if has_payment_info:
        buttons.append(InlineKeyboardButton(text="📩 پیامک", callback_data=f"debt_sms:{txn_id}"))
    if remaining is not None and remaining > 0:
        buttons.append(InlineKeyboardButton(text="💳 پرداخت", callback_data=f"quick_pay_debt:{txn_id}"))
    buttons.append(InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit_debt:{txn_id}"))
    buttons.append(InlineKeyboardButton(text="🗑 حذف", callback_data=f"delete_debt:{txn_id}"))
    builder.row(*buttons)
    return builder.as_markup()


def recv_detail_keyboard(txn_id: int, cache_key: str, safe_party: str,
                          has_photo: bool = False, remaining: float = None,
                          has_payment_info: bool = False,
                          has_payment_photo: bool = False,
                          back_callback: str = None) -> InlineKeyboardMarkup:
    """Keyboard for individual receivable detail view with all actions."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if has_photo:
        buttons.append(InlineKeyboardButton(text="📸 عکس", callback_data=f"view_photo:{txn_id}"))
    if has_payment_photo:
        buttons.append(InlineKeyboardButton(text="📸 رسید پرداخت", callback_data=f"view_payment_photo:{txn_id}"))
    if has_payment_info:
        buttons.append(InlineKeyboardButton(text="📩 پیامک", callback_data=f"recv_sms:{txn_id}"))
    if remaining is not None and remaining > 0:
        buttons.append(InlineKeyboardButton(text="💵 دریافت", callback_data=f"quick_pay_recv:{txn_id}"))
    if buttons:
        builder.row(*buttons)
    builder.row(
        InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit_receivable:{txn_id}"),
        InlineKeyboardButton(text="🗑 حذف", callback_data=f"delete_receivable:{txn_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📜 تاریخچه پرداخت", callback_data=f"receivable_payment_history:{txn_id}")
    )
    if back_callback is None:
        back_callback = f"recv_detail_back:{cache_key}:{safe_party}"
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data=back_callback)
    )
    return builder.as_markup()


def recv_customer_debts_keyboard(txns_data: list) -> InlineKeyboardMarkup:
    """Keyboard showing individual receivables of a customer with Details buttons."""
    builder = InlineKeyboardBuilder()
    for item in txns_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به مشتریان", callback_data="recv_group_back"))
    return builder.as_markup()


def recv_customer_keyboard(customers_data: list) -> InlineKeyboardMarkup:
    """Keyboard for selecting a customer to view their grouped receivables."""
    builder = InlineKeyboardBuilder()
    for item in customers_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="recv_group_back"))
    return builder.as_markup()


def receivable_list_keyboard(txn_id: int, has_photo: bool = False, remaining: float = None, has_payment_info: bool = False) -> InlineKeyboardMarkup:
    """Inline keyboard for each receivable item in the list."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if has_photo:
        buttons.append(InlineKeyboardButton(text="📸 عکس", callback_data=f"view_photo:{txn_id}"))
    if has_payment_info:
        buttons.append(InlineKeyboardButton(text="📩 پیامک", callback_data=f"recv_sms:{txn_id}"))
    if remaining is not None and remaining > 0:
        buttons.append(InlineKeyboardButton(text="💵 دریافت", callback_data=f"quick_pay_recv:{txn_id}"))
    buttons.append(InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit_receivable:{txn_id}"))
    buttons.append(InlineKeyboardButton(text="🗑 حذف", callback_data=f"delete_receivable:{txn_id}"))
    builder.row(*buttons)
    return builder.as_markup()


def customer_receivable_keyboard(customers_data: list) -> InlineKeyboardMarkup:
    """Keyboard for selecting a customer to view their grouped receivables.

    Args:
        customers_data: list of dicts with keys: label, callback_data
    """
    builder = InlineKeyboardBuilder()
    for item in customers_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="recv_group_back"))
    return builder.as_markup()


def customer_receivable_detail_keyboard(party_key: str, txn_ids: list) -> InlineKeyboardMarkup:
    """Keyboard for a customer's receivable detail view."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📩 پیامک همه", callback_data=f"recv_group_sms:{party_key}"),
        InlineKeyboardButton(text="💵 دریافت", callback_data=f"recv_group_pay:{party_key}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت به لیست", callback_data="recv_group_back")
    )
    return builder.as_markup()


def settled_recv_customer_keyboard(customers_data: list) -> InlineKeyboardMarkup:
    """Keyboard for selecting a customer in settled receivables hierarchy."""
    builder = InlineKeyboardBuilder()
    for item in customers_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="receivable_settled_cat"))
    return builder.as_markup()


def settled_recv_items_keyboard(items_data: list, cache_key: str) -> InlineKeyboardMarkup:
    """Keyboard showing settled receivables of a customer, each with a Details button."""
    builder = InlineKeyboardBuilder()
    for item in items_data:
        builder.row(
            InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]),
            InlineKeyboardButton(text="📋 جزئیات", callback_data=item["detail_callback"])
        )
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به مشتریان", callback_data=f"rs_bc:{cache_key}"))
    return builder.as_markup()


def settled_recv_detail_keyboard(txn_id: int, cache_key: str, safe_party: str, has_photo: bool = False, has_payment_photo: bool = False, back_callback: str = None) -> InlineKeyboardMarkup:
    """Keyboard for settled receivable detail view."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if has_photo:
        buttons.append(InlineKeyboardButton(text="📸 مشاهده عکس", callback_data=f"view_photo:{txn_id}"))
    if has_payment_photo:
        buttons.append(InlineKeyboardButton(text="📸 رسید پرداخت", callback_data=f"view_payment_photo:{txn_id}"))
    if buttons:
        builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="📜 تاریخچه پرداخت", callback_data=f"receivable_payment_history:{txn_id}"))
    if back_callback is None:
        back_callback = f"rs_bi:{cache_key}:{safe_party}"
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به لیست", callback_data=back_callback))
    return builder.as_markup()


def settled_debt_customer_keyboard(customers_data: list) -> InlineKeyboardMarkup:
    """Keyboard for selecting a customer in settled debts hierarchy."""
    builder = InlineKeyboardBuilder()
    for item in customers_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="debt_settled_cat"))
    return builder.as_markup()


def settled_debt_items_keyboard(items_data: list, cache_key: str) -> InlineKeyboardMarkup:
    """Keyboard showing settled debts of a customer, each with a Details button."""
    builder = InlineKeyboardBuilder()
    for item in items_data:
        builder.row(
            InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]),
            InlineKeyboardButton(text="📋 جزئیات", callback_data=item["detail_callback"])
        )
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به مشتریان", callback_data=f"ds_bc:{cache_key}"))
    return builder.as_markup()


def settled_debt_detail_keyboard(txn_id: int, cache_key: str, safe_party: str, has_photo: bool = False, has_payment_photo: bool = False, back_callback: str = None) -> InlineKeyboardMarkup:
    """Keyboard for settled debt detail view."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if has_photo:
        buttons.append(InlineKeyboardButton(text="📸 مشاهده عکس", callback_data=f"view_photo:{txn_id}"))
    if has_payment_photo:
        buttons.append(InlineKeyboardButton(text="📸 رسید پرداخت", callback_data=f"view_payment_photo:{txn_id}"))
    if buttons:
        builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="📜 تاریخچه پرداخت", callback_data=f"debt_payment_history:{txn_id}"))
    if back_callback is None:
        back_callback = f"ds_bi:{cache_key}:{safe_party}"
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به لیست", callback_data=back_callback))
    return builder.as_markup()


def settlement_submenu() -> InlineKeyboardMarkup:
    """Settlement submenu keyboard - combines debt and receivable settlements."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 تسویه بدهی‌ها", callback_data="settlement_debt"),
        InlineKeyboardButton(text="💵 تسویه طلب‌ها", callback_data="settlement_recv")
    )
    builder.row(
        InlineKeyboardButton(text="📊 گزارش تسویه‌ها", callback_data="settlement_reports")
    )
    return builder.as_markup()


def settlement_customer_keyboard(customers_data: list, back_callback: str = "settlement_back") -> InlineKeyboardMarkup:
    """Keyboard for selecting a customer in settlement hierarchy."""
    builder = InlineKeyboardBuilder()
    for item in customers_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=back_callback))
    return builder.as_markup()


def settlement_items_keyboard(items_data: list, cache_key: str, back_callback: str = "stl_bc") -> InlineKeyboardMarkup:
    """Keyboard showing settlement items of a customer."""
    builder = InlineKeyboardBuilder()
    for item in items_data:
        builder.row(
            InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]),
            InlineKeyboardButton(text="📋 جزئیات", callback_data=item["detail_callback"])
        )
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به مشتریان", callback_data=f"{back_callback}:{cache_key}"))
    return builder.as_markup()


def settlement_detail_keyboard(txn_id: int, cache_key: str, safe_party: str,
                                has_photo: bool = False, has_payment_photo: bool = False,
                                txn_type: str = "debt") -> InlineKeyboardMarkup:
    """Keyboard for settlement detail view with all actions."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if has_photo:
        buttons.append(InlineKeyboardButton(text="📸 مشاهده عکس", callback_data=f"view_photo:{txn_id}"))
    if has_payment_photo:
        buttons.append(InlineKeyboardButton(text="📸 رسید پرداخت", callback_data=f"view_payment_photo:{txn_id}"))
    if buttons:
        builder.row(*buttons)

    history_cb = f"debt_payment_history:{txn_id}" if txn_type == "debt" else f"receivable_payment_history:{txn_id}"
    builder.row(InlineKeyboardButton(text="📜 تاریخچه پرداخت", callback_data=history_cb))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به لیست", callback_data=f"stl_bi:{cache_key}:{safe_party}"))
    return builder.as_markup()


def debt_payments_customer_keyboard(customers_data: list) -> InlineKeyboardMarkup:
    """Keyboard for selecting a customer in debt payments view."""
    builder = InlineKeyboardBuilder()
    for item in customers_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به منوی بدهی‌ها", callback_data="debt_view_payments_back"))
    return builder.as_markup()


def debt_payments_detail_keyboard(txn_id: int, cache_key: str, safe_party: str,
                                   has_photo: bool = False,
                                   has_payment_photo: bool = False,
                                   has_payment_info: bool = False) -> InlineKeyboardMarkup:
    """Keyboard for payment detail view with all actions."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if has_photo:
        buttons.append(InlineKeyboardButton(text="📸 مشاهده عکس", callback_data=f"view_photo:{txn_id}"))
    if has_payment_photo:
        buttons.append(InlineKeyboardButton(text="📸 رسید پرداخت", callback_data=f"view_payment_photo:{txn_id}"))
    if has_payment_info:
        buttons.append(InlineKeyboardButton(text="📩 پیامک", callback_data=f"debt_sms:{txn_id}"))
    if buttons:
        builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit_debt:{txn_id}"))
    builder.row(InlineKeyboardButton(text="📜 تاریخچه پرداخت", callback_data=f"debt_payment_history:{txn_id}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به لیست", callback_data=f"dvp_bi:{cache_key}:{safe_party}"))
    return builder.as_markup()


def recv_payments_customer_keyboard(customers_data: list) -> InlineKeyboardMarkup:
    """Keyboard for selecting a customer in receivable collections view."""
    builder = InlineKeyboardBuilder()
    for item in customers_data:
        builder.row(InlineKeyboardButton(text=item["label"], callback_data=item["callback_data"]))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به منوی طلب‌ها", callback_data="recv_view_payments_back"))
    return builder.as_markup()


def recv_payments_detail_keyboard(txn_id: int, cache_key: str, safe_party: str,
                                   has_photo: bool = False,
                                   has_payment_photo: bool = False,
                                   has_payment_info: bool = False) -> InlineKeyboardMarkup:
    """Keyboard for receivable collection detail view with all actions."""
    builder = InlineKeyboardBuilder()
    buttons = []
    if has_photo:
        buttons.append(InlineKeyboardButton(text="📸 مشاهده عکس", callback_data=f"view_photo:{txn_id}"))
    if has_payment_photo:
        buttons.append(InlineKeyboardButton(text="📸 رسید دریافت", callback_data=f"view_payment_photo:{txn_id}"))
    if has_payment_info:
        buttons.append(InlineKeyboardButton(text="📩 پیامک", callback_data=f"recv_sms:{txn_id}"))
    if buttons:
        builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit_receivable:{txn_id}"))
    builder.row(InlineKeyboardButton(text="📜 تاریخچه دریافت", callback_data=f"receivable_payment_history:{txn_id}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت به لیست", callback_data=f"rvp_bi:{cache_key}:{safe_party}"))
    return builder.as_markup()
