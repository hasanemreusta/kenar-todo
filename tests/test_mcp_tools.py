import unittest
from tempfile import TemporaryDirectory
from todo.mcp_tools import TOOLS, call_tool

class TestMcpTools(unittest.TestCase):
    def test_tool_names(self):
        self.assertEqual(len(TOOLS), 5)
        names = [tool["name"] for tool in TOOLS]
        self.assertIn("list_tasks", names)
        self.assertIn("add_task", names)
        self.assertIn("complete_task", names)
        self.assertIn("delete_task", names)

    def test_add_then_list(self):
        with TemporaryDirectory() as temp_dir:
            path = temp_dir + "/tasks.json"
            result = call_tool("add_task", {"title": "Test Task"}, path)
            self.assertTrue(result["ok"])
            task_id = result["result"]["id"]
            result = call_tool("list_tasks", {}, path)
            self.assertTrue(result["ok"])
            tasks = result["result"]
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0]["id"], task_id)
            self.assertEqual(tasks[0]["title"], "Test Task")

    def test_add_with_invalid_priority(self):
        with TemporaryDirectory() as temp_dir:
            path = temp_dir + "/tasks.json"
            result = call_tool("add_task", {"title": "Test Task", "priority": "invalid"}, path)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "Invalid priority: invalid")

    def test_complete_then_list_with_pending_only(self):
        with TemporaryDirectory() as temp_dir:
            path = temp_dir + "/tasks.json"
            result = call_tool("add_task", {"title": "Test Task"}, path)
            self.assertTrue(result["ok"])
            task_id = result["result"]["id"]
            result = call_tool("complete_task", {"id": task_id}, path)
            self.assertTrue(result["ok"])
            result = call_tool("list_tasks", {"pending_only": True}, path)
            self.assertTrue(result["ok"])
            tasks = result["result"]
            self.assertEqual(len(tasks), 0)

    def test_delete_unknown_id(self):
        with TemporaryDirectory() as temp_dir:
            path = temp_dir + "/tasks.json"
            result = call_tool("delete_task", {"id": 12345}, path)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "task not found")

    def test_unknown_tool(self):
        with TemporaryDirectory() as temp_dir:
            path = temp_dir + "/tasks.json"
            result = call_tool("unknown_tool", {}, path)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "unknown tool")

    def test_missing_argument(self):
        with TemporaryDirectory() as temp_dir:
            result = call_tool("add_task", {}, temp_dir + "/tasks.json")
            self.assertEqual(result, {"ok": False, "error": "missing argument: title"})

    def test_update_task(self):
        with TemporaryDirectory() as temp_dir:
            path = temp_dir + "/tasks.json"
            call_tool("add_task", {"title": "Old"}, path)
            result = call_tool("update_task", {"id": 1, "title": "New", "note": "details", "priority": "high"}, path)
            self.assertTrue(result["ok"])
            self.assertEqual(result["result"]["title"], "New")
            self.assertEqual(result["result"]["note"], "details")
            bad = call_tool("update_task", {"id": 1, "priority": "nope"}, path)
            self.assertFalse(bad["ok"])
            missing = call_tool("update_task", {"id": 99, "title": "x"}, path)
            self.assertEqual(missing["error"], "task not found")

if __name__ == "__main__":
    unittest.main()
