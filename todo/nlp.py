"""Turkish natural-language quick add: 'rapor cuma !yüksek #iş', 'spor her gün', 'doktor 25 ekim'.

parse_natural() returns the task fields plus `found`, a list of (kind, label) pairs the widget shows
as a live preview while the user types, so it is always visible what was understood.
"""
import re
from datetime import date, timedelta
from typing import Optional

from todo.daymonth import parse_day_month
from todo.quickadd import PRIORITY_TOKENS
from todo.weekday import next_weekday

TR_PRIORITY = {"!yüksek": "high", "!yuksek": "high", "!orta": "medium", "!düşük": "low",
               "!dusuk": "low", "!!": "high"}
PRIORITY_LABEL = {"high": "Yüksek", "medium": "Orta", "low": "Düşük"}
RELATIVE = {"bugün": 0, "bugun": 0, "today": 0, "yarın": 1, "yarin": 1, "tomorrow": 1,
            "haftaya": 7}
REPEAT_WORDS = {"gün": "daily", "gun": "daily", "hafta": "weekly", "ay": "monthly"}
REPEAT_LABEL = {"daily": "Her gün", "weekly": "Her hafta", "monthly": "Her ay"}
MONTHS_SHORT = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
NUMERIC_DATE = re.compile(r"^(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?$")


def _strip_at(word: str) -> str:
    return word[1:] if word.startswith("@") else word


def _numeric_date(word: str, today: date) -> Optional[str]:
    m = NUMERIC_DATE.match(word)
    if not m:
        return None
    day, month = int(m.group(1)), int(m.group(2))
    year = int(m.group(3)) if m.group(3) else today.year
    try:
        result = date(year, month, day)
    except ValueError:
        return None
    if not m.group(3) and result < today:
        try:
            result = date(year + 1, month, day)
        except ValueError:
            return None
    return result.isoformat()


def due_label(iso: str, today: date) -> str:
    d = date.fromisoformat(iso)
    delta = (d - today).days
    names = {0: "Bugün", 1: "Yarın"}
    prefix = names.get(delta)
    text = f"{d.day} {MONTHS_SHORT[d.month - 1]}"
    return f"{prefix} · {text}" if prefix else text


def parse_natural(text: str, today: str) -> dict:
    base = date.fromisoformat(today)
    words = text.split()
    title, tags, found = [], [], []
    priority, due, repeat = "medium", None, ""
    i = 0
    while i < len(words):
        word = words[i]
        low = word.lower()
        nxt = words[i + 1].lower() if i + 1 < len(words) else ""
        # two-word forms first
        if low == "her" and nxt:
            if nxt in REPEAT_WORDS:
                repeat = REPEAT_WORDS[nxt]
                i += 2
                continue
            weekday = next_weekday(nxt, base.isoformat())
            if weekday:
                repeat, due = "weekly", weekday
                i += 2
                continue
        if low in ("öbür", "obur") and nxt in ("gün", "gun"):
            due = (base + timedelta(days=2)).isoformat()
            i += 2
            continue
        if low.isdigit() and nxt:
            day_month = parse_day_month(low, nxt, base.isoformat())
            if day_month:
                due = day_month
                i += 2
                continue
        # single words
        plain = _strip_at(low)
        if low in PRIORITY_TOKENS or low in TR_PRIORITY:
            priority = PRIORITY_TOKENS.get(low) or TR_PRIORITY[low]
        elif low.startswith("#") and len(low) > 1:
            if low[1:] not in tags:
                tags.append(low[1:])
        elif plain in RELATIVE:
            due = (base + timedelta(days=RELATIVE[plain])).isoformat()
        elif i > 0 and next_weekday(plain, base.isoformat()):   # 'pazar alışverişi' stays a title
            due = next_weekday(plain, base.isoformat())
        elif _numeric_date(plain, base):
            due = _numeric_date(plain, base)
        elif low.startswith("@") and _iso(plain):
            due = plain
        else:
            title.append(word)
        i += 1
    if repeat and not due:
        due = base.isoformat()
    if due:
        found.append(("due", due_label(due, base)))
    if repeat:
        found.append(("repeat", REPEAT_LABEL[repeat]))
    if priority != "medium":
        found.append(("priority", PRIORITY_LABEL[priority]))
    found += [("tag", "#" + t) for t in tags]
    return {"title": " ".join(title), "priority": priority, "due": due, "tags": tags, "repeat": repeat,
            "found": found}


def _iso(word: str) -> bool:
    try:
        date.fromisoformat(word)
        return True
    except ValueError:
        return False
