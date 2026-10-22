"""Validated partial updates of a task."""
from datetime import date
from typing import Any, Dict

from todo.models import PRIORITIES, REPEATS, Task, now_iso

FIELDS = ("title", "note", "priority", "due", "tags", "subtasks", "pinned", "repeat")


def _clean_tags(value) -> list:
    tags = []
    for tag in value:
        tag = str(tag).strip().lstrip("#").strip().lower()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _clean_subtasks(value) -> list:
    items = []
    for item in value:
        if isinstance(item, str):
            item = {"text": item}
        if not isinstance(item, dict):
            raise ValueError("invalid subtask")
        text = str(item.get("text", "")).strip()
        if text:
            items.append({"text": text, "done": bool(item.get("done", False))})
    return items


def apply_update(task: Task, changes: Dict[str, Any]) -> Task:
    """Validate every change first, then apply them all (a failed update leaves the task untouched)."""
    clean: Dict[str, Any] = {}
    for key, value in changes.items():
        if key not in FIELDS:
            raise ValueError(f"unknown field: {key}")
        if key == "title":
            value = (value or "").strip()
            if not value:
                raise ValueError("title is empty")
        elif key == "note":
            value = (value or "").strip()
        elif key == "priority":
            if value not in PRIORITIES:
                raise ValueError("invalid priority")
        elif key == "due":
            if value in (None, ""):
                value = None
            else:
                try:
                    date.fromisoformat(value)
                except (TypeError, ValueError):
                    raise ValueError("invalid due date") from None
        elif key == "tags":
            value = _clean_tags(value or [])
        elif key == "subtasks":
            value = _clean_subtasks(value or [])
        elif key == "pinned":
            value = bool(value)
        elif key == "repeat":
            value = value or ""
            if value not in REPEATS:
                raise ValueError("invalid repeat")
        clean[key] = value
    for key, value in clean.items():
        setattr(task, key, value)
    if clean:
        task.updated = now_iso()
    return task
