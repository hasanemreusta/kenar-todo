import unittest
from urllib.parse import parse_qs, urlparse

from todo.integrations import (CALENDARS, MAILS, calendar_link, gmail_url, mail_link, outlook_calendar_url,
                               outlook_mail_url)
from todo.models import Task


def sample():
    return Task(id=1, title="Rapor, son", due="2026-12-31", note="Detay", repeat="weekly",
                subtasks=[{"text": "Taslak", "done": False}])


class IntegrationsTests(unittest.TestCase):
    def test_provider_lists_start_with_default(self):
        self.assertEqual(next(iter(CALENDARS)), "default")
        self.assertEqual(next(iter(MAILS)), "default")

    def test_gmail(self):
        url = gmail_url("Konu", "Govde\nikinci")
        parts = urlparse(url)
        self.assertEqual((parts.scheme, parts.netloc, parts.path), ("https", "mail.google.com", "/mail/"))
        q = parse_qs(parts.query)
        self.assertEqual((q["view"], q["su"], q["body"]), (["cm"], ["Konu"], ["Govde\nikinci"]))

    def test_outlook(self):
        q = parse_qs(urlparse(outlook_mail_url("A", "B")).query)
        self.assertEqual((q["subject"], q["body"]), (["A"], ["B"]))
        q = parse_qs(urlparse(outlook_calendar_url("T", "D", "2026-12-31")).query)
        self.assertEqual((q["startdt"], q["enddt"], q["allday"]), (["2026-12-31"], ["2027-01-01"], ["true"]))

    def test_calendar_link_by_provider(self):
        task = sample()
        google = calendar_link(task, "google")
        self.assertTrue(google.startswith("https://calendar.google.com/calendar/render?"))
        self.assertIn("RRULE%3AFREQ%3DWEEKLY", google)
        self.assertIn("20261231%2F20270101", google)
        self.assertIn("outlook.live.com/calendar", calendar_link(task, "outlook"))
        self.assertIsNone(calendar_link(task, "default"))
        with self.assertRaises(ValueError):
            calendar_link(Task(id=2, title="x"), "google")

    def test_mail_link_by_provider(self):
        task = sample()
        self.assertTrue(mail_link(task, "gmail").startswith("https://mail.google.com/mail/?"))
        self.assertTrue(mail_link(task, "outlook").startswith("https://outlook.live.com/mail/"))
        self.assertTrue(mail_link(task, "default").startswith("mailto:?subject="))


if __name__ == "__main__":
    unittest.main()
