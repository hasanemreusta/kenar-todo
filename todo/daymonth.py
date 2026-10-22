"""'25 ekim' style dates: a day number plus a Turkish month name (full or 3 letters)."""
from datetime import date
from typing import Optional

MONTHS = ["ocak", "subat", "mart", "nisan", "mayis", "haziran", "temmuz", "agustos", "eylul", "ekim", "kasim",
          "aralik"]
ASCII = str.maketrans({"ş": "s", "ı": "i", "ğ": "g", "ü": "u", "ö": "o", "ç": "c"})


def month_number(name: str) -> Optional[int]:
    word = name.strip().lower().translate(ASCII)
    for i, month in enumerate(MONTHS, start=1):
        if word == month or word == month[:3]:
            return i
    return None


def parse_day_month(day: str, month: str, today: str) -> Optional[str]:
    """ISO date of that day/month this year, or next year if it has already passed; None if invalid."""
    if not day.strip().isdigit():
        return None
    number = month_number(month)
    if number is None:
        return None
    base = date.fromisoformat(today)
    for year in (base.year, base.year + 1):
        try:
            result = date(year, number, int(day))
        except ValueError:
            continue           # e.g. 29 subat in a non-leap year: try the next year
        if result >= base:
            return result.isoformat()
    return None
