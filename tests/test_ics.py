import unittest
from datetime import datetime, timezone

from todo.ics import description, task_to_event, tasks_to_ics
from todo.mailto import task_body, task_mailto
from todo.models import Task

NOW = datetime(2026, 10, 21, 12, 0, 0, tzinfo=timezone.utc)


def sample():
    return Task(id=3, title="Market, süt al", due="2026-10-25", priority="high", tags=["ev", "market"],
                note="Yagsiz; 2 litre", repeat="weekly",
                subtasks=[{"text": "Sut", "done": True}, {"text": "Ekmek", "done": False}])


class IcsTests(unittest.TestCase):
    def test_description(self):
        self.assertEqual(description(sample()), "Yagsiz; 2 litre\n\n[x] Sut\n[ ] Ekmek")
        self.assertEqual(description(Task(id=1, title="a")), "")

    def test_event_lines(self):
        lines = task_to_event(sample(), "20261021T120000Z")
        self.assertIn("UID:todo-3@todo-app", lines)
        self.assertIn("DTSTART;VALUE=DATE:20261025", lines)
        self.assertIn("DTEND;VALUE=DATE:20261026", lines)
        self.assertIn("SUMMARY:Market\\, süt al", lines)
        self.assertIn("CATEGORIES:ev,market", lines)
        self.assertIn("RRULE:FREQ=WEEKLY", lines)
        self.assertIn("PRIORITY:1", lines)
        self.assertTrue(any(l.startswith("DESCRIPTION:Yagsiz\\; 2 litre\\n\\n[x] Sut") for l in lines))

    def test_calendar_structure(self):
        done = Task(id=4, title="done", due="2026-10-26", done=True)
        undated = Task(id=5, title="no date")
        text = tasks_to_ics([sample(), done, undated], now=NOW)
        self.assertTrue(text.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"))
        self.assertTrue(text.endswith("END:VCALENDAR\r\n"))
        self.assertEqual(text.count("BEGIN:VEVENT"), 1)      # only the pending, dated task
        self.assertIn("DTSTAMP:20261021T120000Z", text)
        for physical in text.split("\r\n"):
            self.assertLessEqual(len(physical.encode("utf-8")), 75)

    def test_empty_calendar(self):
        self.assertEqual(tasks_to_ics([], now=NOW).count("BEGIN:VEVENT"), 0)


class MailtoTests(unittest.TestCase):
    def test_body(self):
        body = task_body(sample())
        self.assertIn("Yagsiz; 2 litre", body)
        self.assertIn("[x] Sut", body)
        self.assertIn("Son tarih: 2026-10-25", body)
        self.assertIn("#ev, #market", body)

    def test_url(self):
        url = task_mailto(sample())
        self.assertTrue(url.startswith("mailto:?subject=Market%2C%20s%C3%BCt%20al&body="))
        self.assertNotIn(" ", url)
        self.assertNotIn("\n", url)

    def test_long_body_is_cut(self):
        task = Task(id=1, title="x", note="a" * 5000)
        self.assertLess(len(task_mailto(task)), 2100)


if __name__ == "__main__":
    unittest.main()
