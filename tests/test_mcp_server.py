import json
import os
import tempfile
import unittest

from todo.mcp_server import handle_request


class McpServerTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.td.name, "tasks.json")

    def tearDown(self):
        self.td.cleanup()

    def call(self, method, params=None, req_id=1):
        req = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            req["params"] = params
        return handle_request(req, self.path)

    def test_initialize(self):
        resp = self.call("initialize")
        self.assertEqual(resp["id"], 1)
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["result"]["serverInfo"]["name"], "todo-app")
        self.assertIn("protocolVersion", resp["result"])

    def test_tools_list(self):
        self.assertEqual(len(self.call("tools/list")["result"]["tools"]), 5)

    def test_add_then_list(self):
        self.call("tools/call", {"name": "add_task", "arguments": {"title": "Milk"}})
        resp = self.call("tools/call", {"name": "list_tasks", "arguments": {}}, req_id=2)
        self.assertEqual(resp["id"], 2)
        self.assertFalse(resp["result"]["isError"])
        tasks = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(tasks[0]["title"], "Milk")

    def test_unknown_tool(self):
        resp = self.call("tools/call", {"name": "nope"})
        self.assertTrue(resp["result"]["isError"])

    def test_notification_has_no_response(self):
        self.assertIsNone(handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"}, self.path))

    def test_unknown_method(self):
        resp = self.call("foo/bar")
        self.assertEqual(resp["error"]["code"], -32601)
        self.assertEqual(resp["id"], 1)


if __name__ == "__main__":
    unittest.main()
