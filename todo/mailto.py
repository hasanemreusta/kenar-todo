"""Turn a task into a ready-to-send mail (opens the default mail app through a mailto: link)."""
from urllib.parse import quote

from todo.models import Task

MAX_BODY = 1800   # mailto: links get unreliable beyond a couple of thousand characters


def task_body(task: Task) -> str:
    lines = []
    if task.note.strip():
        lines += [task.note.strip(), ""]
    for item in task.subtasks:
        lines.append(("[x] " if item["done"] else "[ ] ") + item["text"])
    if task.subtasks:
        lines.append("")
    if task.due:
        lines.append("Son tarih: " + task.due)
    if task.tags:
        lines.append("Etiketler: " + ", ".join("#" + t for t in task.tags))
    return "\n".join(lines).strip()


def task_mailto(task: Task, to: str = "") -> str:
    """mailto: URL with the task title as subject and note, subtasks and due date as body."""
    body = task_body(task)[:MAX_BODY]
    return f"mailto:{quote(to)}?subject={quote(task.title, safe='')}&body={quote(body, safe='')}"
