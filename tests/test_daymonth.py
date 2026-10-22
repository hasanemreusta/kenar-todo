import unittest

from todo.daymonth import parse_day_month

TODAY = "2026-10-21"


class DayMonthTests(unittest.TestCase):
    def test_this_or_next_year(self):
        self.assertEqual(parse_day_month("25", "ekim", TODAY), "2026-10-25")
        self.assertEqual(parse_day_month("21", "ekim", TODAY), "2026-10-21")
        self.assertEqual(parse_day_month("5", "ocak", TODAY), "2027-01-05")

    def test_month_spellings(self):
        self.assertEqual(parse_day_month("1", "kas", TODAY), "2026-11-01")
        self.assertEqual(parse_day_month("3", "şubat", TODAY), "2027-02-03")
        self.assertEqual(parse_day_month("3", "Subat", TODAY), "2027-02-03")
        self.assertEqual(parse_day_month("9", "Ağustos", TODAY), "2027-08-09")
        self.assertEqual(parse_day_month("12", "aralık", TODAY), "2026-12-12")

    def test_invalid(self):
        self.assertIsNone(parse_day_month("30", "subat", TODAY))
        self.assertIsNone(parse_day_month("x", "ekim", TODAY))
        self.assertIsNone(parse_day_month("5", "kedi", TODAY))

    def test_leap_day(self):
        self.assertEqual(parse_day_month("29", "şubat", "2027-03-01"), "2028-02-29")


if __name__ == "__main__":
    unittest.main()
