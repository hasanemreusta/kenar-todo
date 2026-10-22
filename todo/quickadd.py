from datetime import date, timedelta

PRIORITY_TOKENS = {"!high": "high", "!h": "high", "!medium": "medium", "!m": "medium",
                   "!low": "low", "!l": "low"}


def parse_quick(text: str, today: str) -> dict:
    """Parse 'Buy milk !high #home @tomorrow' into title/priority/due/tags."""
    today_date = date.fromisoformat(today)
    day_words = {"@today": today_date, "@bug\u00fcn": today_date,
                 "@tomorrow": today_date + timedelta(days=1),
                 "@yar\u0131n": today_date + timedelta(days=1)}
    priority, due, tags, words = "medium", None, [], []
    for token in text.split():
        low = token.lower()
        if low in PRIORITY_TOKENS:
            priority = PRIORITY_TOKENS[low]
        elif low.startswith("#") and len(low) > 1:
            if low[1:] not in tags:
                tags.append(low[1:])
        elif low in day_words:
            due = day_words[low].isoformat()
        elif low.startswith("@") and _is_iso(low[1:]):
            due = low[1:]
        else:
            words.append(token)
    return {"title": " ".join(words), "priority": priority, "due": due, "tags": tags}


def _is_iso(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False
