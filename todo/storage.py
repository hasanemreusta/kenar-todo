"""Persistence: JSON file storage."""
from typing import List
from todo.models import Task
import json
import os


def load_tasks(path: str) -> List[Task]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Task.from_dict(item) for item in data]
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON format") from e


def save_tasks(path: str, tasks: List[Task]) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in tasks], f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)
