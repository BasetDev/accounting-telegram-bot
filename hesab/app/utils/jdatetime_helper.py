"""Jalali (Persian) date and time utilities."""

import jdatetime
from pytz import timezone
from datetime import datetime as dt

from app.config import settings

IRAN_TZ = timezone(settings.TIMEZONE)

# Persian month names
MONTHS_FA = [
    "فروردین", "اردیبهشت", "خرداد",
    "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر",
    "دی", "بهمن", "اسفند"
]

# Persian day names
DAYS_FA = [
    "شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
    "چهارشنبه", "پنجشنبه", "جمعه"
]


def get_now_jalali() -> jdatetime.datetime:
    """Get current time in Iran timezone as Jalali datetime."""
    utc_now = dt.utcnow()
    iran_now = utc_now.replace(tzinfo=timezone("UTC")).astimezone(IRAN_TZ)
    return jdatetime.datetime.fromgregorian(
        year=iran_now.year,
        month=iran_now.month,
        day=iran_now.day,
        hour=iran_now.hour,
        minute=iran_now.minute,
        second=iran_now.second
    )


def get_jalali_date() -> str:
    """Get current Jalali date as string: ۱۴۰۵/۰۴/۰۴"""
    now = get_now_jalali()
    return now.strftime("%Y/%m/%d")


def get_jalali_time() -> str:
    """Get current Iran time as string: ۱۴:۳۰:۲۵"""
    now = get_now_jalali()
    return now.strftime("%H:%M:%S")


def get_jalali_full() -> str:
    """Get full Jalali datetime: ۱۴۰۵/۰۴/۰۴ - ۱۴:۳۰:۲۵"""
    return f"{get_jalali_date()} - {get_jalali_time()}"


def convert_to_jalali(year: int, month: int, day: int,
                      hour: int = 0, minute: int = 0, second: int = 0) -> str:
    """Convert Gregorian date to Jalali date string."""
    j_date = jdatetime.date.fromgregorian(year=year, month=month, day=day)
    return j_date.strftime("%Y/%m/%d")


def get_month_name(month_number: int) -> str:
    """Get Persian month name from number (1-12)."""
    if 1 <= month_number <= 12:
        return MONTHS_FA[month_number - 1]
    return ""


def get_day_name(jalali_date: str) -> str:
    """Get Persian day name for a Jalali date string."""
    try:
        parts = jalali_date.split("/")
        j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
        return DAYS_FA[j_date.weekday()]
    except (ValueError, IndexError):
        return ""


def format_amount(amount: float) -> str:
    """Format amount with Persian digits and commas."""
    formatted = f"{amount:,.0f}"
    # Convert to Persian digits
    persian_digits = {
        "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
        "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹"
    }
    for eng, per in persian_digits.items():
        formatted = formatted.replace(eng, per)
    return formatted


def format_amount_for_sms(amount: float) -> str:
    """Format amount for SMS/copy with English digits and thousand separators.

    Uses English digits (0-9) with comma thousand separators.
    Wraps with LRI/PDI (Left-to-Right Isolate / Pop Directional Isolate)
    to ensure correct LTR display in RTL context.
    """
    formatted = f"{amount:,.0f}"
    # Use LRI (U+2066) + PDI (U+2069) isolate controls
    # This isolates the number from surrounding RTL text
    return "\u2066" + formatted + "\u2069"


def get_days_until(jalali_date_str: str) -> int:
    """Calculate days from now until given Jalali date."""
    try:
        parts = jalali_date_str.split("/")
        target = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
        now = get_now_jalali().date()
        delta = target - now
        return delta.days
    except (ValueError, IndexError):
        return 0


def is_date_in_range(date_str: str, start: str, end: str) -> bool:
    """Check if a Jalali date string is within a range (inclusive)."""
    return start <= date_str <= end


def get_date_parts(jalali_date: str) -> tuple:
    """Get year, month, day from Jalali date string."""
    parts = jalali_date.split("/")
    if len(parts) == 3:
        return int(parts[0]), int(parts[1]), int(parts[2])
    return 0, 0, 0


def get_current_jalali_period(period: str) -> tuple:
    """
    Get start and end Jalali date strings for a period.
    period: 'daily', 'weekly', 'monthly', 'yearly'
    """
    now = get_now_jalali()
    today = now.date()
    
    if period == "daily":
        return today.strftime("%Y/%m/%d"), today.strftime("%Y/%m/%d")
    
    elif period == "weekly":
        # Last 7 days
        start = today - jdatetime.timedelta(days=6)
        return start.strftime("%Y/%m/%d"), today.strftime("%Y/%m/%d")
    
    elif period == "monthly":
        start = jdatetime.date(today.year, today.month, 1)
        return start.strftime("%Y/%m/%d"), today.strftime("%Y/%m/%d")
    
    elif period == "yearly":
        start = jdatetime.date(today.year, 1, 1)
        return start.strftime("%Y/%m/%d"), today.strftime("%Y/%m/%d")
    
    return "", ""


def get_week_end_jalali() -> str:
    """Get Jalali date string for 6 days from today (end of this week)."""
    now = get_now_jalali()
    end = now.date() + jdatetime.timedelta(days=6)
    return end.strftime("%Y/%m/%d")


def get_days_between(start_date: str, end_date: str) -> int:
    """Calculate the number of days between two Jalali date strings."""
    try:
        parts_start = start_date.split("/")
        parts_end = end_date.split("/")
        start = jdatetime.date(int(parts_start[0]), int(parts_start[1]), int(parts_start[2]))
        end = jdatetime.date(int(parts_end[0]), int(parts_end[1]), int(parts_end[2]))
        delta = end - start
        return max(1, delta.days + 1)  # +1 to include both start and end days
    except (ValueError, IndexError):
        return 1


def normalize_bank_name(name: str) -> str:
    """Normalize a bank name by stripping redundant prefixes.

    If the name already starts with 'بانک', strip it so that
    the caller can add a consistent 'بانک: ' prefix during display.

    Examples:
        'بانک ملت'  -> 'ملت'
        'ملت'       -> 'ملت'
        'انک ملت'   -> 'ملت'
        'بانک ملی'  -> 'ملی'
        None        -> None
    """
    if not name:
        return name
    name = name.strip()
    # Remove 'بانک ' or 'انک ' prefix
    for prefix in ("بانک ", "بانک", "انک "):
        if name.startswith(prefix):
            name = name[len(prefix):].strip()
            break
    return name


# ==============================
# Persian Number to Words
# ==============================

_ONES = [
    "", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه",
    "ده", "یازده", "دوازده", "سیزده", "چهارده", "پانزده", "شانزده",
    "هفده", "هجده", "نوزده"
]

_TENS = [
    "", "", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود"
]

_HUNDREDS = [
    "", "صد", "دویست", "سیصد", "چهارصد", "پانصد", "ششصد", "هفتصد", "هشتصد", "نهصد"
]


def _chunk_to_words(n: int) -> str:
    """Convert a number 0-999 to Persian words."""
    if n == 0:
        return ""
    parts = []
    if n >= 100:
        parts.append(_HUNDREDS[n // 100])
        n %= 100
    if n >= 20:
        parts.append(_TENS[n // 10])
        n %= 10
    if n >= 1:
        if 1 <= n <= 19:
            parts.append(_ONES[n])
    return " و ".join(parts)


def amount_to_persian_words(amount: float) -> str:
    """Convert a numeric amount to Persian words with 'تومان' suffix.

    Examples:
        1200000 -> "یک میلیون و دویست هزار تومان"
        50000   -> "پنجاه هزار تومان"
        0       -> "صفر تومان"
    """
    n = int(amount)
    if n == 0:
        return "صفر تومان"

    # Negative amounts
    prefix = ""
    if n < 0:
        prefix = "منفی "
        n = abs(n)

    # Units: [میلیارد, میلیون, هزار, یکان]
    scales = [
        (1_000_000_000, "میلیارد"),
        (1_000_000, "میلیون"),
        (1_000, "هزار"),
    ]

    parts = []
    for value, label in scales:
        if n >= value:
            chunk = n // value
            words = _chunk_to_words(chunk)
            if words:
                parts.append(f"{words} {label}")
            n %= value

    if n > 0:
        words = _chunk_to_words(n)
        if words:
            parts.append(words)

    result = " و ".join(parts)
    return f"{prefix}{result} تومان"


# ==============================
# English Number to Words
# ==============================

_EN_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen"
]

_EN_TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
]


def _en_chunk_to_words(n: int) -> str:
    """Convert a number 0-999 to English words."""
    if n == 0:
        return ""
    parts = []
    if n >= 100:
        parts.append(f"{_EN_ONES[n // 100]} Hundred")
        n %= 100
    if n >= 20:
        tens = _EN_TENS[n // 10]
        n %= 10
        if n > 0:
            parts.append(f"{tens}-{_EN_ONES[n]}")
        else:
            parts.append(tens)
    elif n >= 1:
        parts.append(_EN_ONES[n])
    return " ".join(parts)


def amount_to_english_words(amount: float) -> str:
    """Convert a numeric amount to English words with 'Toman' suffix.

    Examples:
        1200000 -> "One Million Two Hundred Thousand Toman"
        50000   -> "Fifty Thousand Toman"
        0       -> "Zero Toman"
    """
    n = int(amount)
    if n == 0:
        return "Zero Toman"

    prefix = ""
    if n < 0:
        prefix = "Negative "
        n = abs(n)

    scales = [
        (1_000_000_000, "Billion"),
        (1_000_000, "Million"),
        (1_000, "Thousand"),
    ]

    parts = []
    for value, label in scales:
        if n >= value:
            chunk = n // value
            words = _en_chunk_to_words(chunk)
            if words:
                parts.append(f"{words} {label}")
            n %= value

    if n > 0:
        words = _en_chunk_to_words(n)
        if words:
            parts.append(words)

    result = " ".join(parts)
    return f"{prefix}{result} Toman"