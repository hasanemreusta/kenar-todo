"""Pure task operations (no I/O). All functions take and return lists of Task."""
from datetime import date
from typing import List, Optional
from todo.models import Task, PRIORITIES, now_iso


def add_task(tasks: List[Task], title: str, priority: str = "medium",
             due: Optional[str] = None, tags: Optional[List[str]] = None) -> Task:
    title = (title or "").strip()
    if not title:
        raise ValueError("Title cannot be empty")
    if priority not in PRIORITIES:
        raise ValueError(f"Invalid priority: {priority}")
    if due is not None:
        date.fromisoformat(due)  # raises ValueError on bad input
    clean = []
    for tag in tags or []:
        tag = tag.strip().lower()
        if tag and tag not in clean:
            clean.append(tag)
    task = Task(id=max((t.id for t in tasks), default=0) + 1, title=title,
                priority=priority, due=due, tags=clean,
                created=now_iso(), updated=now_iso())
    tasks.append(task)
    return task


def _find(tasks: List[Task], task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise KeyError(task_id)


def mark_done(tasks: List[Task], task_id: int) -> Task:
    task = _find(tasks, task_id)
    task.done = True
    return task


def remove_task(tasks: List[Task], task_id: int) -> Task:
    task = _find(tasks, task_id)
    tasks.remove(task)
    return task


def filter_tasks(tasks: List[Task], tag: Optional[str] = None,
                 priority: Optional[str] = None, pending_only: bool = False,
                 query: Optional[str] = None, today: Optional[str] = None,
                 overdue_only: bool = False) -> List[Task]:
    today = today or date.today().isoformat()
    result = []
    for t in tasks:
        if tag is not None and tag.strip().lower() not in t.tags:
            continue
        if priority is not None and t.priority != priority:
            continue
        if pending_only and t.done:
            continue
        if query is not None and query.lower() not in t.title.lower():
            continue
        if overdue_only and (t.done or t.due is None or t.due >= today):
            continue
        result.append(t)
    rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(result, key=lambda t: (t.done, t.due is None, t.due or "",
                                         rank[t.priority], t.id))
