"""Persian (Jalali/Shamsi) date formatting based on the local system calendar.

The conversion is delegated to jdatetime instead of a handwritten calendar
algorithm; no network or device-location permission is needed.
"""
from __future__ import annotations

from datetime import date

import jdatetime

PERSIAN_MONTHS = (
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
)
# datetime.date.weekday(): Monday = 0, Sunday = 6.
PERSIAN_WEEKDAYS = (
    "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه",
    "جمعه", "شنبه", "یکشنبه",
)
TRANSLATE_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def persian_digits(text: str | int) -> str:
    return str(text).translate(TRANSLATE_DIGITS)


def format_jalali_date(today: date | None = None) -> str:
    """Example: یکشنبه ۱ آذر ۱۴۰۵."""
    today = today or date.today()
    jalali = jdatetime.date.fromgregorian(date=today)
    weekday = PERSIAN_WEEKDAYS[today.weekday()]
    month = PERSIAN_MONTHS[jalali.month - 1]
    return f"{weekday} {persian_digits(jalali.day)} {month} {persian_digits(jalali.year)}"
