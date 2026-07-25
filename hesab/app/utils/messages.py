"""Persian message strings for the bot."""

# Welcome messages
WELCOME = """🎉 به ربات حسابداری کسب‌وکار خوش آمدید!

این ربات به شما کمک می‌کند:
• مدیریت درآمدها و هزینه‌ها
• ثبت و پیگیری بدهی‌ها و طلب‌ها
• مدیریت مشتریان
• مشاهده گزارش‌های مالی
• خروجی Excel و PDF
• ثبت شماره کارت و شبا

برای راهنمایی از دستور /help استفاده کنید"""

HELP = """📖 راهنمای ربات حسابداری کسب‌وکار

دستورات موجود:
/start - شروع مجدد
/menu - نمایش منوی اصلی
/help - راهنما
/dashboard - مشاهده داشبورد مالی
/report - گزارش‌های مالی
/backup - پشتیبان‌گیری

از منوی اصلی می‌توانید به تمام بخش‌ها دسترسی داشته باشید."""

# Transaction messages
INCOME_AMOUNT = "💰 مبلغ درآمد را وارد کنید:\n(فقط عدد، به تومان)"
INCOME_DESC = "📝 توضیحات درآمد را وارد کنید:"
INCOME_CATEGORY = "🏷 دسته‌بندی درآمد را انتخاب کنید:"
INCOME_SAVED = "✅ درآمد با موفقیت ثبت شد!"

EXPENSE_AMOUNT = "💸 مبلغ هزینه را وارد کنید:\n(فقط عدد، به تومان)"
EXPENSE_DESC = "📝 توضیحات هزینه را وارد کنید:"
EXPENSE_CATEGORY = "🏷 دسته‌بندی هزینه را انتخاب کنید:"
EXPENSE_SAVED = "✅ هزینه با موفقیت ثبت شد!"

DEBT_AMOUNT = "📋 مبلغ بدهی را وارد کنید:\n(فقط عدد، به تومان)"
DEBT_PARTY = "👤 نام شخص یا شرکت بدهکار را وارد کنید:"
DEBT_DESC = "📝 توضیحات بدهی را وارد کنید:"
DEBT_DUE = "📅 تاریخ سررسید را وارد کنید:\n(مثال: ۱۴۰۵/۰۴/۰۴)"
DEBT_SAVED = "✅ بدهی با موفقیت ثبت شد!"
DEBT_CATEGORY_PROMPT = "🏷 دسته‌بندی بدهی را انتخاب کنید:"
DEBT_SUBCATEGORY_PROMPT = "📂 زیرمجموعه بدهی را انتخاب کنید:"

RECEIVABLE_AMOUNT = "📌 مبلغ طلب را وارد کنید:\n(فقط عدد، به تومان)"
RECEIVABLE_PARTY = "👤 نام مشتری یا شرکت بدهکار را وارد کنید:"
RECEIVABLE_DESC = "📝 توضیحات طلب را وارد کنید:"
RECEIVABLE_DUE = "📅 تاریخ سررسید را وارد کنید:\n(مثال: ۱۴۰۵/۰۴/۰۴)"
RECEIVABLE_SAVED = "✅ طلب با موفقیت ثبت شد!"
RECEIVABLE_CATEGORY_PROMPT = "🏷 دسته‌بندی طلب را انتخاب کنید:"
RECEIVABLE_SUBCATEGORY_PROMPT = "📂 زیرمجموعه طلب را انتخاب کنید:"

# Card/IBAN in debt/receivable registration
CARD_INFO_DEBT_PROMPT = "💳 شماره کارت را انتخاب کنید:\n\nاز لیست زیر انتخاب کنید، ورود دستی انجام دهید، یا رد کنید:"
CARD_INFO_RECV_PROMPT = "💳 شماره کارت را انتخاب کنید:\n\nاز لیست زیر انتخاب کنید، ورود دستی انجام دهید، یا رد کنید:"
CARD_INFO_MANUAL_CARD = "💳 شماره کارت را وارد کنید:\n(۱۶ رقم)\n\nبرای رد کردن، «⏭️ رد کردن» را بزنید."
CARD_INFO_MANUAL_SHEBA = "🏦 شماره شبا (IBAN) را وارد کنید:\n(فقط ۲۴ رقم، بدون حروف IR)\n\nبرای رد کردن، «⏭️ رد کردن» را بزنید."
SHEBA_SELECT_PROMPT = "🏦 شماره شبا (IBAN) را انتخاب کنید:\n\nاز لیست زیر انتخاب کنید، ورود دستی انجام دهید، یا رد کنید:"
SHEBA_MANUAL_PROMPT = "🏦 شماره شبا (IBAN) را وارد کنید:\n(فقط ۲۴ رقم، بدون حروف IR)\n\nبرای رد کردن، «⏭️ رد کردن» را بزنید."
BANK_NAME_SELECT_PROMPT = "🏛 نام بانک را انتخاب کنید:\n\nاز لیست زیر انتخاب کنید، ورود دستی انجام دهید، یا رد کنید:"
BANK_NAME_MANUAL_PROMPT = "🏛 نام بانک را وارد کنید:\n\nبرای رد کردن، «⏭️ رد کردن» را بزنید."

# Payment messages
PAY_DEBT_PROMPT = "💳 پرداخت بدهی\n\nیک بدهی فعال را برای پرداخت انتخاب کنید:"
PAY_DEBT_SELECT = "📋 بدهی مورد نظر را انتخاب کنید:"
PAY_DEBT_AMOUNT_PROMPT = "💰 مبلغ پرداخت را وارد کنید:\n(فقط عدد، به تومان)\n\nمبلغ باقی‌مانده: {remaining} تومان"
PAY_DEBT_FULL = "💰 پرداخت کامل"
PAY_DEBT_PARTIAL = "💰 پرداخت جزئی"
PAY_DEBT_SUCCESS = "✅ پرداخت بدهی با موفقیت ثبت شد!"
PAY_DEBT_SETTLED = "🎉 بدهی کاملاً تسویه شد!"
PAY_DEBT_NO_ACTIVE = "📭 هیچ بدهی فعالی برای پرداخت وجود ندارد."

RECEIVE_RECV_PROMPT = "💵 دریافت طلب\n\nیک طلب فعال را برای دریافت انتخاب کنید:"
RECEIVE_RECV_SELECT = "📋 طلب مورد نظر را انتخاب کنید:"
RECEIVE_RECV_AMOUNT_PROMPT = "💰 مبلغ دریافت را وارد کنید:\n(فقط عدد، به تومان)\n\nمبلغ باقی‌مانده: {remaining} تومان"
RECEIVE_RECV_FULL = "💰 دریافت کامل"
RECEIVE_RECV_PARTIAL = "💰 دریافت جزئی"
RECEIVE_RECV_SUCCESS = "✅ دریافت طلب با موفقیت ثبت شد!"
RECEIVE_RECV_SETTLED = "🎉 طلب کاملاً وصول شد!"
RECEIVE_RECV_NO_ACTIVE = "📭 هیچ طلب فعالی برای دریافت وجود ندارد."

PAYMENT_HISTORY_TITLE = "📊 تاریخچه پرداخت‌ها"
PAYMENT_HISTORY_EMPTY = "📭 هیچ پرداختی ثبت نشده است."
PAYMENT_INVALID_AMOUNT = "⚠️ مبلغ پرداخت باید بیشتر از صفر و حداکثر برابر مبلغ باقی‌مانده باشد."

# Debt submenu
DEBT_MENU_TITLE = "💳 بدهی‌ها\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
DEBT_ACTIVE = "🟡 بدهی‌های فعال"
DEBT_OVERDUE = "🔴 سررسید گذشته"
DEBT_SETTLED = "🟢 تسویه شده"
DEBT_DUE_TODAY = "⏰ سررسید امروز"
DEBT_DUE_WEEK = "📅 سررسید این هفته"
DEBT_ALL = "📋 همه بدهی‌ها"
DEBT_REPORTS = "📊 گزارش بدهی‌ها"

# Receivable submenu
RECEIVABLE_MENU_TITLE = "💵 طلب‌ها\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
RECEIVABLE_ACTIVE = "🟡 طلب‌های فعال"
RECEIVABLE_OVERDUE = "🔴 سررسید گذشته"
RECEIVABLE_SETTLED = "🟢 تسویه شده"
RECEIVABLE_DUE_TODAY = "⏰ سررسید امروز"
RECEIVABLE_DUE_WEEK = "📅 سررسید این هفته"
RECEIVABLE_ALL = "📋 همه طلب‌ها"
RECEIVABLE_REPORTS = "📊 گزارش طلب‌ها"

# Empty list messages
DEBT_EMPTY = "📭 هیچ بدهی ثبت نشده است."
DEBT_ACTIVE_EMPTY = "📭 هیچ بدهی فعالی وجود ندارد."
DEBT_OVERDUE_EMPTY = "📭 هیچ بدهی سررسید گذشته‌ای وجود ندارد."
DEBT_SETTLED_EMPTY = "📭 هیچ بدهی تسویه شده‌ای وجود ندارد."
DEBT_DUE_TODAY_EMPTY = "📭 هیچ بدهی با سررسید امروز وجود ندارد."
DEBT_DUE_WEEK_EMPTY = "📭 هیچ بدهی با سررسید این هفته وجود ندارد."

RECEIVABLE_EMPTY = "📭 هیچ طلبی ثبت نشده است."
RECEIVABLE_ACTIVE_EMPTY = "📭 هیچ طلب فعالی وجود ندارد."
RECEIVABLE_OVERDUE_EMPTY = "📭 هیچ طلب سررسید گذشته‌ای وجود ندارد."
RECEIVABLE_SETTLED_EMPTY = "📭 هیچ طلب تسویه شده‌ای وجود ندارد."
RECEIVABLE_DUE_TODAY_EMPTY = "📭 هیچ طلب با سررسید امروز وجود ندارد."
RECEIVABLE_DUE_WEEK_EMPTY = "📭 هیچ طلب با سررسید این هفته وجود ندارد."

# Report titles for debt/receivable
DEBT_REPORT_TITLE = """📊 گزارش جامع بدهی‌ها
━━━━━━━━━━━━━━━━━━

📋 خلاصه کلی
├── تعداد کل: {total} مورد
└── مجموع مبلغ: {total_amount} تومان

⏳ بدهی‌های فعال
├── تعداد: {active} مورد
└── مبلغ: {active_amount} تومان

✅ تسویه شده
├── تعداد: {settled} مورد
└── مبلغ: {settled_amount} تومان

🔴 سررسید گذشته
├── تعداد: {overdue} مورد
└── مبلغ: {overdue_amount} تومان

⏰ سررسید امروز: {due_today} مورد

━━━━━━━━━━━━━━━━━━
📊 نسبت تسویه: {settlement_rate}%
📊 میانگین بدهی: {avg_debt} تومان
💰 مجموع پرداختی: {total_paid} تومان"""

DEBT_REPORT_ACTIVE = """⏳ گزارش بدهی‌های فعال
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد: {count} مورد
└── مجموع: {total_amount} تومان

{details}"""

DEBT_REPORT_SETTLED = """✅ گزارش بدهی‌های تسویه شده
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد: {count} مورد
└── مجموع: {total_amount} تومان

{details}"""

DEBT_REPORT_OVERDUE = """🔴 گزارش بدهی‌های سررسید گذشته
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد: {count} مورد
└── مجموع: {total_amount} تومان

{details}"""

DEBT_REPORT_DUE_TODAY = """⏰ گزارش بدهی‌های سررسید امروز
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد: {count} مورد
└── مجموع: {total_amount} تومان

{details}"""

DEBT_REPORT_DUE_WEEK = """📅 گزارش بدهی‌های سررسید این هفته
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد: {count} مورد
└── مجموع: {total_amount} تومان

{details}"""

DEBT_REPORT_BY_CUSTOMER = """👥 گزارش بدهی‌ها بر اساس مشتری
━━━━━━━━━━━━━━━━━━

👥 تعداد مشتریان: {customer_count}

{details}"""

DEBT_REPORT_BY_CATEGORY = """🏷 گزارش بدهی‌ها بر اساس دسته‌بندی
━━━━━━━━━━━━━━━━━━

{details}"""

DEBT_REPORT_PAYMENTS = """💰 گزارش پرداخت‌های بدهی
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد پرداخت‌ها: {payment_count} مورد
└── مجموع پرداختی: {total_paid} تومان

{details}"""

DEBT_REPORT_REMAINING = """📊 گزارش مانده بدهی‌ها
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد بدهی‌های فعال: {active_count} مورد
├── مجموع مانده: {total_remaining} تومان
└── مجموع کل بدهی: {total_amount} تومان

{details}"""

DEBT_REPORT_EMPTY = "📭 هیچ بدهی‌ای در این دسته وجود ندارد."
DEBT_REPORTS_MENU = "📊 گزارش‌های بدهی\n\nلطفاً نوع گزارش را انتخاب کنید:"

DEBT_REPORT_DAILY = """📅 گزارش بدهی‌های روزانه
━━━━━━━━━━━━━━━━━━

🔄 بازه زمانی: {period}
├── از: {start}
└── تا: {end}

📋 خلاصه
├── تعداد بدهی‌ها: {count} مورد
└── مجموع مبلغ: {total_amount} تومان

⏳ بدهی‌های فعال: {active_count} مورد
✅ تسویه شده: {settled_count} مورد

{details}"""

DEBT_REPORT_WEEKLY = """📅 گزارش بدهی‌های هفتگی
━━━━━━━━━━━━━━━━━━

🔄 بازه زمانی: {period}
├── از: {start}
└── تا: {end}

📋 خلاصه
├── تعداد بدهی‌ها: {count} مورد
└── مجموع مبلغ: {total_amount} تومان

⏳ بدهی‌های فعال: {active_count} مورد
✅ تسویه شده: {settled_count} مورد

{details}"""

DEBT_REPORT_MONTHLY = """📅 گزارش بدهی‌های ماهانه
━━━━━━━━━━━━━━━━━━

🔄 بازه زمانی: {period}
├── از: {start}
└── تا: {end}

📋 خلاصه
├── تعداد بدهی‌ها: {count} مورد
└── مجموع مبلغ: {total_amount} تومان

⏳ بدهی‌های فعال: {active_count} مورد
✅ تسویه شده: {settled_count} مورد

{details}"""

DEBT_REPORT_YEARLY = """📅 گزارش بدهی‌های سالانه
━━━━━━━━━━━━━━━━━━

🔄 بازه زمانی: {period}
├── از: {start}
└── تا: {end}

📋 خلاصه
├── تعداد بدهی‌ها: {count} مورد
└── مجموع مبلغ: {total_amount} تومان

⏳ بدهی‌های فعال: {active_count} مورد
✅ تسویه شده: {settled_count} مورد

{details}"""

RECEIVABLE_REPORT_TITLE = """📊 گزارش جامع طلب‌ها
━━━━━━━━━━━━━━━━━━

📋 خلاصه کلی
├── تعداد کل: {total} مورد
└── مجموع مبلغ: {total_amount} تومان

⏳ طلب‌های فعال
├── تعداد: {active} مورد
└── مبلغ: {active_amount} تومان

✅ وصول شده
├── تعداد: {settled} مورد
└── مبلغ: {settled_amount} تومان

🔴 سررسید گذشته
├── تعداد: {overdue} مورد
└── مبلغ: {overdue_amount} تومان

⏰ سررسید امروز: {due_today} مورد

━━━━━━━━━━━━━━━━━━
📊 نسبت وصول: {collection_rate}%
📊 میانگین طلب: {avg_receivable} تومان
💰 مجموع دریافتی: {total_paid} تومان"""

RECV_REPORT_ACTIVE = """⏳ گزارش طلب‌های فعال
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد: {count} مورد
└── مجموع: {total_amount} تومان

{details}"""

RECV_REPORT_SETTLED = """✅ گزارش طلب‌های وصول شده
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد: {count} مورد
└── مجموع: {total_amount} تومان

{details}"""

RECV_REPORT_OVERDUE = """🔴 گزارش طلب‌های سررسید گذشته
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد: {count} مورد
└── مجموع: {total_amount} تومان

{details}"""

RECV_REPORT_DUE_TODAY = """⏰ گزارش طلب‌های سررسید امروز
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد: {count} مورد
└── مجموع: {total_amount} تومان

{details}"""

RECV_REPORT_DUE_WEEK = """📅 گزارش طلب‌های سررسید این هفته
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد: {count} مورد
└── مجموع: {total_amount} تومان

{details}"""

RECV_REPORT_BY_CUSTOMER = """👥 گزارش طلب‌ها بر اساس مشتری
━━━━━━━━━━━━━━━━━━

👥 تعداد مشتریان: {customer_count}

{details}"""

RECV_REPORT_BY_CATEGORY = """🏷 گزارش طلب‌ها بر اساس دسته‌بندی
━━━━━━━━━━━━━━━━━━

{details}"""

RECV_REPORT_PAYMENTS = """💰 گزارش دریافت‌های طلب
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد دریافت‌ها: {payment_count} مورد
└── مجموع دریافتی: {total_paid} تومان

{details}"""

RECV_REPORT_REMAINING = """📊 گزارش مانده طلب‌ها
━━━━━━━━━━━━━━━━━━

📋 خلاصه
├── تعداد طلب‌های فعال: {active_count} مورد
├── مجموع مانده: {total_remaining} تومان
└── مجموع کل طلب: {total_amount} تومان

{details}"""

RECV_REPORT_EMPTY = "📭 هیچ طلبی در این دسته وجود ندارد."
RECV_REPORTS_MENU = "📊 گزارش‌های طلب‌ها\n\nلطفاً نوع گزارش را انتخاب کنید:"

RECV_REPORT_DAILY = """📅 گزارش طلب‌های روزانه
━━━━━━━━━━━━━━━━━━

🔄 بازه زمانی: {period}
├── از: {start}
└── تا: {end}

📋 خلاصه
├── تعداد طلب‌ها: {count} مورد
└── مجموع مبلغ: {total_amount} تومان

⏳ طلب‌های فعال: {active_count} مورد
✅ وصول شده: {settled_count} مورد

{details}"""

RECV_REPORT_WEEKLY = """📅 گزارش طلب‌های هفتگی
━━━━━━━━━━━━━━━━━━

🔄 بازه زمانی: {period}
├── از: {start}
└── تا: {end}

📋 خلاصه
├── تعداد طلب‌ها: {count} مورد
└── مجموع مبلغ: {total_amount} تومان

⏳ طلب‌های فعال: {active_count} مورد
✅ وصول شده: {settled_count} مورد

{details}"""

RECV_REPORT_MONTHLY = """📅 گزارش طلب‌های ماهانه
━━━━━━━━━━━━━━━━━━

🔄 بازه زمانی: {period}
├── از: {start}
└── تا: {end}

📋 خلاصه
├── تعداد طلب‌ها: {count} مورد
└── مجموع مبلغ: {total_amount} تومان

⏳ طلب‌های فعال: {active_count} مورد
✅ وصول شده: {settled_count} مورد

{details}"""

RECV_REPORT_YEARLY = """📅 گزارش طلب‌های سالانه
━━━━━━━━━━━━━━━━━━

🔄 بازه زمانی: {period}
├── از: {start}
└── تا: {end}

📋 خلاصه
├── تعداد طلب‌ها: {count} مورد
└── مجموع مبلغ: {total_amount} تومان

⏳ طلب‌های فعال: {active_count} مورد
✅ وصول شده: {settled_count} مورد

{details}"""

# Error messages
INVALID_AMOUNT = "⚠️ مبلغ وارد شده معتبر نیست. لطفاً فقط عدد وارد کنید."
INVALID_DATE = "⚠️ تاریخ وارد شده معتبر نیست. فرمت صحیح: ۱۴۰۵/۰۴/۰۴"
CANCELED = "❌ عملیات لغو شد."
ERROR_GENERAL = "⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید."
ACCESS_DENIED = "⛔ شما دسترسی به این بخش ندارید."

# Dashboard
DASHBOARD_TITLE = "📊 وضعیت مالی"
DASHBOARD_INCOME = "💰 مجموع درآمد"
DASHBOARD_EXPENSE = "💸 مجموع هزینه"
DASHBOARD_DEBT = "📋 مجموع بدهی"
DASHBOARD_RECEIVABLE = "📌 مجموع طلب"
DASHBOARD_BALANCE = "✅ موجودی نهایی"
DASHBOARD_POSITIVE = "✅ حساب مثبت و سودده است 🟢"
DASHBOARD_NEGATIVE = "⚠️ حساب منفی و دارای زیان است 🔴"
DASHBOARD_ZERO = "⚪️ حساب صفر و تسویه شده است"

# Customer messages
CUSTOMER_NAME = "👤 نام کامل مشتری را وارد کنید:"
CUSTOMER_PHONE = "📞 شماره تلفن مشتری را وارد کنید:\n(اختیاری)"
CUSTOMER_ADDRESS = "📍 آدرس مشتری را وارد کنید:\n(اختیاری)"
CUSTOMER_NOTES = "📝 توضیحات اضافه را وارد کنید:\n(اختیاری)"
CUSTOMER_SAVED = "✅ مشتری با موفقیت ثبت شد!"
CUSTOMER_UPDATED = "✅ اطلاعات مشتری به‌روزرسانی شد!"
CUSTOMER_DELETED = "🗑 مشتری با موفقیت حذف شد!"
CUSTOMER_NOT_FOUND = "⚠️ مشتری مورد نظر یافت نشد."
CUSTOMER_SEARCH = "🔍 نام یا شماره تلفن مشتری را وارد کنید:"
CUSTOMER_EMPTY = "📭 هیچ مشتری ثبت نشده است."

# Customer info template
CUSTOMER_INFO = """👤 اطلاعات مشتری

نام: {name}
📞 تلفن: {phone}
📍 آدرس: {address}
📝 توضیحات: {notes}

💳 مجموع بدهی: {debt} تومان
💳 مجموع طلب: {receivable} تومان"""

# Report messages
REPORT_TITLE = """📈 گزارش مالی {period}
━━━━━━━━━━━━━━━━━━

🔄 بازه زمانی
├── از: {start}
└── تا: {end}

💰 درآمدها
└── مجموع: {income} تومان

💸 هزینه‌ها
└── مجموع: {expense} تومان

📋 بدهی‌ها
└── مجموع: {debt} تومان

📌 طلب‌ها
└── مجموع: {receivable} تومان

━━━━━━━━━━━━━━━━━━
{balance_line}

📊 وضعیت حساب: {status}

━━━━━━━━━━━━━━━━━━
📈 خلاصه عملکرد
├── تعداد تراکنش‌ها: {txn_count} مورد
├── میانگین درآمد روزانه: {avg_daily_income} تومان
└── میانگین هزینه روزانه: {avg_daily_expense} تومان"""

REPORT_PERIODS = {
    "daily": "روزانه",
    "weekly": "هفتگی",
    "monthly": "ماهانه",
    "yearly": "سالانه"
}

# Backup messages
BACKUP_CREATED = "✅ پشتیبان با موفقیت ایجاد شد!"
BACKUP_RESTORED = "✅ پشتیبان با موفقیت بازیابی شد!"
BACKUP_ERROR = "⚠️ خطا در عملیات پشتیبان‌گیری."
BACKUP_LIST_EMPTY = "📭 هیچ پشتیبان‌گیری انجام نشده است."
BACKUP_DELETED = "🗑 پشتیبان با موفقیت حذف شد."
BACKUP_CLEANUP_DONE = "🧹 پاکسازی پشتیبان‌های قدیمی انجام شد."
BACKUP_VERIFY_OK = "✅ فایل پشتیبان سالم و معتبر است."
BACKUP_VERIFY_FAIL = "❌ فایل پشتیبان دارای مشکل است."
BACKUP_RESTORE_CONFIRM = "⚠️ آیا از بازیابی پشتیبان اطمینان دارید؟\n\nاین عملیات تمام داده‌های فعلی را با داده‌های پشتیبان جایگزین می‌کند."
BACKUP_MENU_TITLE = "💾 پشتیبان‌گیری\n\nاز این بخش می‌توانید از دیتابیس خود پشتیبان تهیه کنید."

# Reminder messages
REMINDER_DEBT = """🔔 یادآوری بدهی

مهلت پرداخت بدهی به {party}
به مبلغ {amount} تومان
تا تاریخ {date} فرصت دارید."""

REMINDER_RECEIVABLE = """🔔 یادآوری دریافت طلب

زمان دریافت طلب از {party}
به مبلغ {amount} تومان
فرصت باقی‌مانده."""

# Search messages
SEARCH_PROMPT = "🔍 چه چیزی می‌خواهید جستجو کنید؟\nمی‌توانید بر اساس نام، مبلغ، تاریخ یا دسته‌بندی جستجو کنید."
SEARCH_EMPTY = "📭 هیچ نتیجه‌ای یافت نشد."

# Photo messages
PHOTO_PROMPT = "📷 در صورت تمایل، عکس فاکتور یا رسید را ارسال کنید:\n(ارسال عکس اختیاری است)"
PHOTO_SKIP = "⏭️ بدون عکس"
PHOTO_RECEIVED = "✅ عکس با موفقیت دریافت و ذخیره شد!"
PHOTO_ERROR = "⚠️ خطا در ذخیره عکس. لطفاً دوباره تلاش کنید یا «بدون عکس» را بزنید."

# Card & Sheba messages
CARD_INFO_MENU = "💳 ثبت شماره کارت و شبا\n\nاز این بخش می‌توانید شماره کارت و شماره شبا (IBAN) خود را ثبت، ویرایش و مدیریت کنید."
CARD_REGISTER_TITLE = "💳 ثبت شماره کارت و شبا"
CARD_MENU = """💳 منوی شماره کارت و شبا

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"""
CARD_ADD_NEW = "➕ ثبت جدید"
CARD_LIST = "📋 لیست شماره کارت‌ها"
CARD_EDIT = "✏️ ویرایش"
CARD_DELETE = "🗑 حذف"
CARD_SEARCH = "🔍 جستجو"

CARD_ENTER_NAME = "👤 لطفاً نام را وارد کنید:\n\n(می‌توانید نام را دستی وارد کنید یا از لیست مشتریان انتخاب نمایید)"
CARD_NAME_CHOICE = "👤 نام مربوط به این شماره کارت و شبا را چگونه وارد می‌کنید؟"
CARD_NAME_MANUAL = "✏️ ورود دستی نام"
CARD_NAME_CUSTOMER = "👥 انتخاب از مشتریان"
CARD_ENTER_NAME_MANUAL = "✏️ نام را وارد کنید:"
CARD_SELECT_CUSTOMER = "👥 یکی از مشتریان را انتخاب کنید:"
CARD_ENTER_CARD = "💳 شماره کارت را وارد کنید:\n(۱۶ رقم)\n\nبرای رد کردن و خالی گذاشتن، «⏭️ رد کردن» را بزنید."
CARD_ENTER_SHEBA = "🏦 شماره شبا (IBAN) را وارد کنید:\n(فقط ۲۴ رقم، بدون حروف IR)\n\nبرای رد کردن و خالی گذاشتن، «⏭️ رد کردن» را بزنید."
CARD_SAVED = "✅ اطلاعات شماره کارت و شبا با موفقیت ثبت شد!"
CARD_UPDATED = "✅ اطلاعات شماره کارت و شبا با موفقیت به‌روزرسانی شد!"
CARD_DELETED = "🗑 شماره کارت و شبا با موفقیت حذف شد!"
CARD_NOT_FOUND = "⚠️ موردی یافت نشد."
CARD_EMPTY = "📭 هنوز هیچ شماره کارت و شبا ثبت نشده است."
CARD_CONFIRM_DELETE = "⚠️ آیا از حذف این مورد اطمینان دارید؟\n\n{info}"
CARD_COPIED = "✅ کپی شد"
CARD_COPY_SMS_CARD = "📱 ارسال (کارت+نام)"
CARD_COPY_SMS_SHEBA = "📱 ارسال (شبا+نام)"
CARD_DISPLAY = """💳 {name}

💳 شماره کارت: <code>{card}</code>
🏦 شماره شبا: <code>{sheba}</code>

📌 برای کپی، روی هر کدام کلیک کنید."""

CARD_VALID_ERROR_16 = "⚠️ شماره کارت باید دقیقاً ۱۶ رقم باشد."
CARD_VALID_ERROR_SHEBA = "⚠️ شماره شبا باید دقیقاً ۲۴ رقم باشد.\nلطفاً تنها ارقام (بدون IR و فاصله) وارد کنید."
CARD_VALID_ERROR_SHEBA_FORMAT = "⚠️ فرمت شماره شبا نامعتبر است.\nفرمت صحیح: IR به همراه ۲۴ رقم (مجموعاً ۲۶ کاراکتر)"
CARD_VALID_ERROR_EMPTY = "⚠️ حداقل یکی از فیلدهای شماره کارت یا شماره شبا باید وارد شود."
CARD_VALID_ERROR_DUPLICATE = "⚠️ این شماره کارت یا شبا قبلاً ثبت شده است."
CARD_NAME_REQUIRED = "⚠️ لطفاً یک نام وارد کنید."

# Card/Skips
CARD_SKIP = "⏭️ رد کردن"

# General
MENU_TEXT = "📊 حسابداری کسب‌وکار\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
BACK_TEXT = "🔙 به منوی اصلی بازگشتید."
UNKNOWN_COMMAND = "⚠️ دستور نامعتبر. از منوی اصلی استفاده کنید."

# Grouped debt view
DEBT_SELECT_CUSTOMER = "👤 مشتری مورد نظر را انتخاب کنید:"
DEBT_SELECT_DEBT = "📋 بدهی مورد نظر را انتخاب کنید:"
DEBT_PAYMENT_HISTORY_TITLE = "📊 تاریخچه پرداخت‌ها"
DEBT_PAYMENT_HISTORY_EMPTY = "📭 هیچ پرداختی ثبت نشده است."

# Grouped receivable view
RECEIVABLE_SELECT_RECV = "📋 طلب مورد نظر را انتخاب کنید:"

# Debt payment view messages
DEBT_VIEW_PAYMENTS_TITLE = "📜 پرداخت‌های انجام شده"
DEBT_VIEW_PAYMENTS_EMPTY = "📭 هیچ پرداختی ثبت نشده است.\n\nپس از اولین پرداخت بدهی، در این بخش نمایش داده می‌شود."

# Settlement section messages
SETTLEMENT_DEBT_TITLE = "📊 تسویه بدهی‌ها"
SETTLEMENT_RECV_TITLE = "📊 تسویه طلب‌ها"
SETTLEMENT_EMPTY = "📭 هیچ تسویه‌ای ثبت نشده است.\n\nتراکنش‌هایی که حداقل یک پرداخت داشته باشند در این بخش نمایش داده می‌شوند."
SETTLEMENT_DEBT_EMPTY = "📭 هیچ بدهی با پرداخت ثبت نشده است.\n\nپس از اولین پرداخت بدهی، در این بخش نمایش داده می‌شود."
SETTLEMENT_RECV_EMPTY = "📭 هیچ طلب با دریافت ثبت نشده است.\n\nپس از اولین دریافت طلب، در این بخش نمایش داده می‌شود."

# Receivable collection view messages
RECV_VIEW_PAYMENTS_TITLE = "📜 دریافت‌های انجام شده"
RECV_VIEW_PAYMENTS_EMPTY = "📭 هیچ دریافتی ثبت نشده است.\n\nپس از اولین دریافت طلب، در این بخش نمایش داده می‌شود."