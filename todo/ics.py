"""Export tasks as an iCalendar (.ics) file: every pending task with a due date becomes an all-day event."""
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, List, Optional

from todo.icsfold import fold_line
from todo.icstext import ics_escape
from todo.models import Task

PRODID = "-//todo-app//EN"
PRIORITY = {"high": 1, "medium": 5, "low": 9}
RRULE = {"daily": "FREQ=DAILY", "weekly": "FREQ=WEEKLY", "monthly": "FREQ=MONTHLY"}


def description(task: Task) -> str:
    parts = []
    if task.note.strip():
        parts.append(task.note.strip())
    if task.subtasks:
        parts.append("\n".join(("[x] " if s["done"] else "[ ] ") + s["text"] for s in task.subtasks))
    return "\n\n".join(parts)


def task_to_event(task: Task, stamp: str) -> List[str]:
    """Content lines (unfolded) of one all-day VEVENT; the task must have a due date."""
    due = date.fromisoformat(task.due)
    lines = [
        "BEGIN:VEVENT",
        f"UID:todo-{task.id}@todo-app",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{due:%Y%m%d}",
        f"DTEND;VALUE=DATE:{due + timedelta(days=1):%Y%m%d}",
        "SUMMARY:" + ics_escape(task.title),
    ]
    text = description(task)
    if text:
        lines.append("DESCRIPTION:" + ics_escape(text))
    if task.tags:
        lines.append("CATEGORIES:" + ",".join(ics_escape(tag) for tag in task.tags))
    if task.repeat in RRULE:
        lines.append("RRULE:" + RRULE[task.repeat])
    lines.append(f"PRIORITY:{PRIORITY.get(task.priority, 5)}")
    lines.append("END:VEVENT")
    return lines


def tasks_to_ics(tasks: Iterable[Task], now: Optional[datetime] = None) -> str:
    """A complete VCALENDAR (CRLF line endings, folded lines) for the pending tasks that have a due date."""
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:" + PRODID, "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", "X-WR-CALNAME:Yapılacaklar"]
    for task in tasks:
        if task.due and not task.done:
            lines += task_to_event(task, stamp)
    lines.append("END:VCALENDAR")
    return "".join(fold_line(line) + "\r\n" for line in lines)
