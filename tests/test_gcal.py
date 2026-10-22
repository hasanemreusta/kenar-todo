import unittest

from todo.gcal import google_calendar_url

BASE = "https://calendar.google.com/calendar/render"


class GoogleCalendarUrlTests(unittest.TestCase):
    def test_basic(self):
        url = google_calendar_url("Report", "note", "2026-10-25", "")
        self.assertEqual(url, BASE + "?action=TEMPLATE&text=Report&dates=20261025%2F20261026&details=note")

    def test_month_and_year_end(self):
        self.assertIn("dates=20261231%2F20270101", google_calendar_url("x", "", "2026-12-31", ""))

    def test_recurrence(self):
        self.assertNotIn("recur=", google_calendar_url("x", "", "2026-10-25", ""))
        self.assertIn("recur=RRULE%3AFREQ%3DWEEKLY", google_calendar_url("x", "", "2026-10-25", "weekly"))
        self.assertIn("recur=RRULE%3AFREQ%3DMONTHLY", google_calendar_url("x", "", "2026-10-25", "monthly"))
        self.assertNotIn("recur=", google_calendar_url("x", "", "2026-10-25", "yearly"))

    def test_encoding(self):
        url = google_calendar_url("Süt al", "a & b", "2026-10-25", "")
        self.assertIn("text=S%C3%BCt%20al", url)
        self.assertIn("details=a%20%26%20b", url)


if __name__ == "__main__":
    unittest.main()
