"""Small parsers for the detail editor: tag lists and due-date shortcuts."""
import re
from datetime import date, timedelta
from typing import List, Optional

TODAY_WORDS = {"bugun", "bugün", "today"}
TOMORROW_WORDS = {"yarin", "yarın", "tomorrow"}
NEXT_WEEK_WORDS = {"haftaya", "nextweek"}


def parse_tags(text: str) -> List[str]:
    """'Ev, #Is  market' -> ['ev', 'is', 'market']"""
    tags = []
    for part in re.split(r"[,\s]+", text or ""):
        tag = part.strip().lstrip("#").lower()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def due_from_text(text: str, today: str) -> Optional[str]:
    """Turn a typed date ('yarin', '+3', '2026-03-05', '-') into an ISO date or None."""
    word = (text or "").strip().lower()
    base = date.fromisoformat(today)
    if word in ("", "-"):
        return None
    if word in TODAY_WORDS:
        return base.isoformat()
    if word in TOMORROW_WORDS:
        return (base + timedelta(days=1)).isoformat()
    if word in NEXT_WEEK_WORDS:
        return (base + timedelta(days=7)).isoformat()
    if word.startswith("+") and word[1:].isdigit() and int(word[1:]) > 0:
        return (base + timedelta(days=int(word[1:]))).isoformat()
    try:
        return date.fromisoformat(word).isoformat()
    except ValueError:
        raise ValueError("invalid date") from None
