"""Split a task list into the sections the widget shows."""
from typing import List, Tuple

from todo.models import Task

SECTION_ORDER = ("pinned", "overdue", "today", "upcoming", "nodate", "done")


def section_of(task: Task, today: str) -> str:
    if task.done:
        return "done"
    if task.pinned:
        return "pinned"
    if task.due is None:
        return "nodate"
    if task.due < today:
        return "overdue"
    if task.due == today:
        return "today"
    return "upcoming"


def group_tasks(tasks: List[Task], today: str) -> List[Tuple[str, List[Task]]]:
    """Return [(section, tasks)] in display order, skipping empty sections; task order is kept."""
    buckets = {key: [] for key in SECTION_ORDER}
    for task in tasks:
        buckets[section_of(task, today)].append(task)
    return [(key, buckets[key]) for key in SECTION_ORDER if buckets[key]]


def task_matches(task: Task, query: str) -> bool:
    """Case-insensitive search over title, note and tags; an empty query matches everything."""
    q = query.strip().lower().lstrip("#")
    if not q:
        return True
    return (q in task.title.lower() or q in task.note.lower()
            or any(q in tag for tag in task.tags))
