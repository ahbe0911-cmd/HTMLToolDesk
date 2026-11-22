"""Jalali calendar and Persian-digit regression checks."""
import unittest
from datetime import date

from html_tooldesk.jalali import format_jalali_date, persian_digits


class TestJalali(unittest.TestCase):
    def test_known_persian_new_year(self):
        # 2025-03-21 is 1404-01-01 in the Solar Hijri calendar.
        self.assertEqual(format_jalali_date(date(2025, 3, 21)), "جمعه ۱ فروردین ۱۴۰۴")

    def test_known_azar_date(self):
        self.assertEqual(format_jalali_date(date(2026, 11, 22)), "یکشنبه ۱ آذر ۱۴۰۵")

    def test_persian_digits(self):
        self.assertEqual(persian_digits("100%"), "۱۰۰%")
        self.assertEqual(persian_digits(250), "۲۵۰")


if __name__ == "__main__":
    unittest.main()
