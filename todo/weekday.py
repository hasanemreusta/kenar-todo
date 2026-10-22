from datetime import date, timedelta
from typing import Optional

def next_weekday(word: str, today: str) -> Optional[str]:
    weekdays = {
        "pazartesi": 0, "sali": 1, "sal\u0131": 1, "carsamba": 2, "\u00e7ar\u015famba": 2,
        "persembe": 3, "per\u015fembe": 3, "cuma": 4, "cumartesi": 5, "pazar": 6
    }
    word = word.strip().lower()
    if word not in weekdays:
        return None
    today_date = date.fromisoformat(today)
    target_weekday = weekdays[word]
    days_until = (target_weekday - today_date.weekday()) % 7
    if days_until == 0:
        days_until = 7
    return (today_date + timedelta(days=days_until)).isoformat()
