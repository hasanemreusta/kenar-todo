import unittest

from todo.edit import apply_update
from todo.models import Task


class ApplyUpdateTests(unittest.TestCase):
    def setUp(self):
        self.task = Task(id=1, title="old", due="2026-01-01", tags=["a"])

    def test_basic_fields(self):
        apply_update(self.task, {"title": "  new ", "note": " hello ", "priority": "high"})
        self.assertEqual((self.task.title, self.task.note, self.task.priority), ("new", "hello", "high"))

    def test_due_set_and_clear(self):
        apply_update(self.task, {"due": "2026-02-03"})
        self.assertEqual(self.task.due, "2026-02-03")
        apply_update(self.task, {"due": ""})
        self.assertIsNone(self.task.due)
        self.task.due = "2026-01-01"
        apply_update(self.task, {"due": None})
        self.assertIsNone(self.task.due)

    def test_tags_normalised(self):
        apply_update(self.task, {"tags": ["#Ev", "ev", " is ", ""]})
        self.assertEqual(self.task.tags, ["ev", "is"])

    def test_errors(self):
        for bad in ({"title": "  "}, {"priority": "urgent"}, {"due": "2026-13-45"},
                    {"due": "tomorrow"}, {"color": "red"}):
            with self.assertRaises(ValueError):
                apply_update(self.task, bad)

    def test_failed_update_changes_nothing(self):
        with self.assertRaises(ValueError):
            apply_update(self.task, {"title": "x", "priority": "bad"})
        self.assertEqual(self.task.title, "old")

    def test_subtasks_pinned_repeat(self):
        apply_update(self.task, {"subtasks": [{"text": " a ", "done": True}, "b", {"text": " "}],
                                 "pinned": 1, "repeat": "weekly"})
        self.assertEqual(self.task.subtasks, [{"text": "a", "done": True}, {"text": "b", "done": False}])
        self.assertIs(self.task.pinned, True)
        self.assertEqual(self.task.repeat, "weekly")
        apply_update(self.task, {"repeat": None})
        self.assertEqual(self.task.repeat, "")

    def test_invalid_repeat_and_subtask(self):
        with self.assertRaises(ValueError):
            apply_update(self.task, {"repeat": "hourly"})
        with self.assertRaises(ValueError):
            apply_update(self.task, {"subtasks": [5]})

    def test_updated_timestamp(self):
        apply_update(self.task, {"title": "x"})
        self.assertRegex(self.task.updated, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")


if __name__ == "__main__":
    unittest.main()
