import unittest

from todo.recur import next_due


class NextDueTests(unittest.TestCase):
    def test_daily_and_weekly(self):
        self.assertEqual(next_due("2026-01-31", "daily"), "2026-02-01")
        self.assertEqual(next_due("2026-12-28", "weekly"), "2027-01-04")

    def test_monthly(self):
        self.assertEqual(next_due("2026-03-15", "monthly"), "2026-04-15")
        self.assertEqual(next_due("2026-01-31", "monthly"), "2026-02-28")
        self.assertEqual(next_due("2028-01-31", "monthly"), "2028-02-29")
        self.assertEqual(next_due("2026-12-31", "monthly"), "2027-01-31")
        self.assertEqual(next_due("2026-03-31", "monthly"), "2026-04-30")

    def test_invalid_repeat(self):
        with self.assertRaises(ValueError):
            next_due("2026-01-01", "hourly")


if __name__ == "__main__":
    unittest.main()
