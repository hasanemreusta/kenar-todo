import unittest
from todo.models import Task
from todo.ops import add_task, mark_done, remove_task, filter_tasks


class AddTaskTests(unittest.TestCase):
    def test_ids_and_normalisation(self):
        tasks = []
        a = add_task(tasks, "  Buy milk ", "high", "2026-01-05", [" Home", "home", "Shop", ""])
        b = add_task(tasks, "Next")
        self.assertEqual((a.id, b.id), (1, 2))
        self.assertEqual(a.title, "Buy milk")
        self.assertEqual(a.tags, ["home", "shop"])
        self.assertEqual(b.priority, "medium")
        self.assertEqual(len(tasks), 2)

    def test_id_after_removal_uses_max(self):
        tasks = [Task(id=5, title="x")]
        self.assertEqual(add_task(tasks, "y").id, 6)

    def test_errors(self):
        tasks = []
        for kwargs in ({"title": "  "}, {"title": "a", "priority": "urgent"},
                       {"title": "a", "due": "2026-13-40"}, {"title": "a", "due": "tomorrow"}):
            with self.assertRaises(ValueError):
                add_task(tasks, **kwargs)
        self.assertEqual(tasks, [])


class DoneRemoveTests(unittest.TestCase):
    def test_mark_done_and_remove(self):
        tasks = [Task(id=1, title="a"), Task(id=2, title="b")]
        self.assertTrue(mark_done(tasks, 2).done)
        self.assertEqual(remove_task(tasks, 1).id, 1)
        self.assertEqual([t.id for t in tasks], [2])

    def test_missing_id(self):
        with self.assertRaises(KeyError):
            mark_done([], 1)
        with self.assertRaises(KeyError):
            remove_task([], 1)


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            Task(id=1, title="Buy Milk", priority="low", due="2026-01-10", tags=["home"]),
            Task(id=2, title="Report", priority="high", due="2026-01-10", tags=["work"]),
            Task(id=3, title="Old", priority="medium", due="2025-12-01", tags=["work"]),
            Task(id=4, title="No date", priority="high"),
            Task(id=5, title="Finished", done=True, due="2025-01-01"),
        ]

    def ids(self, **kw):
        return [t.id for t in filter_tasks(self.tasks, today="2026-01-05", **kw)]

    def test_sort_order(self):
        self.assertEqual(self.ids(), [3, 2, 1, 4, 5])

    def test_filters(self):
        self.assertEqual(self.ids(tag="WORK"), [3, 2])
        self.assertEqual(self.ids(priority="high"), [2, 4])
        self.assertEqual(self.ids(pending_only=True), [3, 2, 1, 4])
        self.assertEqual(self.ids(query="milk"), [1])

    def test_overdue(self):
        self.assertEqual(self.ids(overdue_only=True), [3])

    def test_returns_new_list(self):
        self.assertIsNot(filter_tasks(self.tasks), self.tasks)


if __name__ == "__main__":
    unittest.main()
