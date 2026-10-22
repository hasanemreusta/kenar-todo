"""Task model."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional

PRIORITIES = ("low", "medium", "high")
REPEATS = ("", "daily", "weekly", "monthly")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="minutes")


@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    priority: str = "medium"  # one of PRIORITIES
    due: Optional[str] = None  # ISO date "YYYY-MM-DD" or None
    tags: List[str] = field(default_factory=list)
    note: str = ""  # free-text description
    subtasks: List[dict] = field(default_factory=list)  # [{"text": str, "done": bool}]
    pinned: bool = False
    repeat: str = ""  # one of REPEATS; a repeating task rolls its due date forward when completed
    created: str = ""  # ISO "YYYY-MM-DDTHH:MM"
    updated: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)
