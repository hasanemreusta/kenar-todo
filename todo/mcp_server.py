import json
import os
import sys
from typing import Optional

from todo.mcp_tools import TOOLS, call_tool


def _ok(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle_request(req: dict, path: str) -> Optional[dict]:
    method = req.get("method", "")
    req_id = req.get("id")
    if method.startswith("notifications/"):
        return None
    if method == "initialize":
        return _ok(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "todo-app", "version": "0.1.0"},
        })
    if method == "ping":
        return _ok(req_id, {})
    if method == "tools/list":
        return _ok(req_id, {"tools": TOOLS})
    if method == "tools/call":
        params = req.get("params") or {}
        out = call_tool(params.get("name"), params.get("arguments") or {}, path)
        text = json.dumps(out["result"], ensure_ascii=False) if out["ok"] else out["error"]
        return _ok(req_id, {"content": [{"type": "text", "text": text}],
                            "isError": not out["ok"]})
    return _error(req_id, -32601, "Method not found")


def main():
    from todo.gui import DATA_PATH  # lazy: keeps tkinter out of module import
    path = os.environ.get("TODO_APP_DATA", DATA_PATH)
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.lstrip("\ufeff").strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            resp = _error(None, -32700, "Invalid JSON")
        else:
            resp = handle_request(req, path) if isinstance(req, dict) else _error(None, -32600, "Invalid Request")
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
