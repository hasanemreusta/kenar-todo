from typing import List, Optional

from todo.edit import apply_update
from datetime import date

from todo.models import Task, now_iso
from todo.ops import add_task, filter_tasks, remove_task
from todo.storage import load_tasks, save_tasks


def list_all(path: str) -> List[Task]:
    tasks = load_tasks(path)
    return filter_tasks(tasks)


def create(path: str, title: str, priority: str = "medium", due: Optional[str] = None,
           tags: Optional[List[str]] = None) -> Task:
    tasks = load_tasks(path)
    task = add_task(tasks, title, priority, due, tags)
    save_tasks(path, tasks)
    return task


def complete(path: str, task_id: int) -> Task:
    return set_done(path, task_id, True)


def delete(path: str, task_id: int) -> Task:
    tasks = load_tasks(path)
    task = remove_task(tasks, task_id)
    save_tasks(path, tasks)
    return task


def _find(tasks: List[Task], task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise KeyError(task_id)


def set_done(path: str, task_id: int, done: bool) -> Task:
    """Mark done/undone. A repeating task with a due date rolls forward instead of finishing."""
    from todo.recur import next_due
    tasks = load_tasks(path)
    task = _find(tasks, task_id)
    if done and task.repeat and task.due:
        today = date.today().isoformat()
        due = next_due(task.due, task.repeat)
        while due <= today:
            due = next_due(due, task.repeat)
        task.due = due
        task.done = False
        for item in task.subtasks:
            item["done"] = False
    else:
        task.done = done
    task.updated = now_iso()
    save_tasks(path, tasks)
    return task


def duplicate(path: str, task_id: int) -> Task:
    """Copy a task (not done, new id, same fields)."""
    tasks = load_tasks(path)
    source = _find(tasks, task_id)
    copy = Task.from_dict(source.to_dict())
    copy.id = max(t.id for t in tasks) + 1
    copy.done = False
    copy.created = copy.updated = now_iso()
    tasks.append(copy)
    save_tasks(path, tasks)
    return copy


def update(path: str, task_id: int, changes: dict) -> Task:
    """Apply a partial update (title, note, priority, due, tags); see todo.edit.apply_update."""
    tasks = load_tasks(path)
    task = apply_update(_find(tasks, task_id), changes)
    save_tasks(path, tasks)
    return task


def restore(path: str, task: Task) -> Task:
    """Put a deleted task back (keeps its id when free, e.g. for 'undo delete')."""
    tasks = load_tasks(path)
    if any(t.id == task.id for t in tasks):
        task.id = max(t.id for t in tasks) + 1
    tasks.append(task)
    save_tasks(path, tasks)
    return task
