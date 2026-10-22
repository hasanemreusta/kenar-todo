import unittest
from tempfile import TemporaryDirectory
from todo import service
from todo.service import list_all, create, complete, delete
from todo.models import Task

class TestService(unittest.TestCase):
    def test_create(self):
        with TemporaryDirectory() as td:
            path = td + "/tasks.json"
            task1 = create(path, "Task 1")
            task2 = create(path, "Task 2")
            self.assertEqual(len(list_all(path)), 2)
            self.assertEqual(task1.title, "Task 1")
            self.assertEqual(task2.title, "Task 2")

    def test_complete(self):
        with TemporaryDirectory() as td:
            path = td + "/tasks.json"
            task = create(path, "Task 1")
            completed_task = complete(path, task.id)
            self.assertTrue(completed_task.done)

    def test_delete(self):
        with TemporaryDirectory() as td:
            path = td + "/tasks.json"
            task = create(path, "Task 1")
            deleted_task = delete(path, task.id)
            self.assertEqual(len(list_all(path)), 0)

    def test_delete_unknown_id(self):
        with TemporaryDirectory() as td:
            path = td + "/tasks.json"
            with self.assertRaises(KeyError):
                delete(path, 12345)

    def test_repeating_task_rolls_forward(self):
        from datetime import date, timedelta
        with TemporaryDirectory() as td:
            path = td + "/tasks.json"
            task = create(path, "Water plants", due=(date.today() - timedelta(days=3)).isoformat())
            service.update(path, task.id, {"repeat": "weekly", "subtasks": [{"text": "a", "done": True}]})
            done = service.complete(path, task.id)
            self.assertFalse(done.done)
            self.assertGreater(done.due, date.today().isoformat())
            self.assertFalse(done.subtasks[0]["done"])

    def test_set_done_toggle_and_duplicate(self):
        with TemporaryDirectory() as td:
            path = td + "/tasks.json"
            task = create(path, "A")
            self.assertTrue(service.set_done(path, task.id, True).done)
            self.assertFalse(service.set_done(path, task.id, False).done)
            copy = service.duplicate(path, task.id)
            self.assertNotEqual(copy.id, task.id)
            self.assertEqual(len(list_all(path)), 2)

if __name__ == "__main__":
    unittest.main()
