import unittest

from todo.grouping import group_tasks, section_of, task_matches
from todo.models import Task

TODAY = "2026-01-10"


class GroupingTests(unittest.TestCase):
    def test_section_of(self):
        self.assertEqual(section_of(Task(id=1, title="a", due="2026-01-09"), TODAY), "overdue")
        self.assertEqual(section_of(Task(id=1, title="a", due=TODAY), TODAY), "today")
        self.assertEqual(section_of(Task(id=1, title="a", due="2026-01-11"), TODAY), "upcoming")
        self.assertEqual(section_of(Task(id=1, title="a"), TODAY), "nodate")
        self.assertEqual(section_of(Task(id=1, title="a", due="2020-01-01", done=True), TODAY), "done")

    def test_group_order_and_skips_empty(self):
        tasks = [Task(id=1, title="n"), Task(id=2, title="o", due="2026-01-01"),
                 Task(id=3, title="d", done=True), Task(id=4, title="n2")]
        groups = group_tasks(tasks, TODAY)
        self.assertEqual([k for k, _ in groups], ["overdue", "nodate", "done"])
        self.assertEqual([t.id for t in groups[1][1]], [1, 4])

    def test_pinned_goes_first_unless_done(self):
        pinned = Task(id=1, title="p", due="2026-01-01", pinned=True)
        done = Task(id=2, title="d", pinned=True, done=True)
        self.assertEqual(section_of(pinned, TODAY), "pinned")
        self.assertEqual(section_of(done, TODAY), "done")
        groups = group_tasks([Task(id=3, title="x"), pinned], TODAY)
        self.assertEqual([k for k, _ in groups], ["pinned", "nodate"])

    def test_empty(self):
        self.assertEqual(group_tasks([], TODAY), [])

    def test_task_matches(self):
        t = Task(id=1, title="Buy Milk", note="from the Market", tags=["home"])
        for q in ("", "milk", "MARKET", "#home", "ho"):
            self.assertTrue(task_matches(t, q), q)
        self.assertFalse(task_matches(t, "work"))


if __name__ == "__main__":
    unittest.main()
