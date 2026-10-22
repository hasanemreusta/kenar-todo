import unittest
from todo.storage import load_tasks, save_tasks
from todo.models import Task
import tempfile
import os


class TestStorage(unittest.TestCase):
    def test_load_tasks_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "tasks.json")
            self.assertEqual(load_tasks(path), [])

    def test_save_load_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "tasks.json")
            tasks = [
                Task(id=1, title="Task 1"),
                Task(id=2, title="Task 2", done=True),
                Task(id=3, title="Task 3", priority="high"),
            ]
            save_tasks(path, tasks)
            loaded_tasks = load_tasks(path)
            self.assertEqual(tasks, loaded_tasks)

    def test_invalid_json_raises_value_error(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "tasks.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("invalid json")
            with self.assertRaises(ValueError):
                load_tasks(path)

    def test_unicode_title_survives(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "tasks.json")
            task = Task(id=1, title="Task with unicode: ğŸŒ")
            save_tasks(path, [task])
            loaded_task = load_tasks(path)[0]
            self.assertEqual(task.title, loaded_task.title)


    def test_overwrite_and_nested_dir(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "sub", "tasks.json")
            save_tasks(path, [Task(id=1, title="a")])
            save_tasks(path, [Task(id=2, title="b")])
            self.assertEqual([t.id for t in load_tasks(path)], [2])
            self.assertFalse(os.path.exists(path + ".tmp"))


if __name__ == "__main__":
    unittest.main()

