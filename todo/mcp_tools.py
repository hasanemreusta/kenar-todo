from typing import List, Optional, Dict
from todo import service
from todo.storage import load_tasks
from todo.ops import filter_tasks
from tempfile import TemporaryDirectory

TOOLS = [
    {
        "name": "list_tasks",
        "description": "List todo tasks (sorted: pending first, by due date, then priority). Optionally only pending ones or by tag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pending_only": {"type": "boolean"},
                "tag": {"type": "string"}
            },
            "additionalProperties": False
        }
    },
    {
        "name": "add_task",
        "description": "Add a todo task. due is YYYY-MM-DD. note is an optional description.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "due": {"type": "string", "format": "date"},
                "tags": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title"],
            "additionalProperties": False
        }
    },
    {
        "name": "update_task",
        "description": "Edit a task: any of title, note (description), priority, due (YYYY-MM-DD, empty string clears), tags, subtasks (checklist, replaces the whole list), pinned, repeat (daily/weekly/monthly or empty).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "note": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "due": {"type": "string", "format": "date"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "subtasks": {"type": "array", "items": {"type": "object", "properties": {
                    "text": {"type": "string"}, "done": {"type": "boolean"}}, "required": ["text"]}},
                "pinned": {"type": "boolean"},
                "repeat": {"type": "string", "enum": ["", "daily", "weekly", "monthly"]}
            },
            "required": ["id"],
            "additionalProperties": False
        }
    },
    {
        "name": "complete_task",
        "description": "Mark the task with this id as done.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"}
            },
            "required": ["id"],
            "additionalProperties": False
        }
    },
    {
        "name": "delete_task",
        "description": "Delete the task with this id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"}
            },
            "required": ["id"],
            "additionalProperties": False
        }
    }
]

def call_tool(name: str, args: Dict, path: str) -> Dict:
    required = {t["name"]: t["inputSchema"].get("required", []) for t in TOOLS}
    for key in required.get(name, []):
        if key not in args:
            return {"ok": False, "error": f"missing argument: {key}"}
    try:
        if name == "list_tasks":
            pending_only = args.get("pending_only", False)
            tag = args.get("tag")
            tasks = filter_tasks(load_tasks(path), tag=tag, pending_only=pending_only)
            return {"ok": True, "result": [task.to_dict() for task in tasks]}
        elif name == "add_task":
            title = args["title"]
            priority = args.get("priority", "medium")
            due = args.get("due")
            tags = args.get("tags")
            task = service.create(path, title, priority, due, tags)
            return {"ok": True, "result": task.to_dict()}
        elif name == "update_task":
            changes = {k: v for k, v in args.items() if k != "id"}
            task = service.update(path, args["id"], changes)
            return {"ok": True, "result": task.to_dict()}
        elif name == "complete_task":
            task_id = args["id"]
            task = service.complete(path, task_id)
            return {"ok": True, "result": task.to_dict()}
        elif name == "delete_task":
            task_id = args["id"]
            task = service.delete(path, task_id)
            return {"ok": True, "result": task.to_dict()}
        else:
            return {"ok": False, "error": "unknown tool"}
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    except KeyError as e:
        return {"ok": False, "error": "task not found"}
    except TypeError as e:
        return {"ok": False, "error": str(e)}
