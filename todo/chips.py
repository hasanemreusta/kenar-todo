from datetime import date
from typing import Optional

def due_chip(due: Optional[str], today: str) -> Optional[tuple]:
    if due is None:
        return None
    due_date = date.fromisoformat(due)
    today_date = date.fromisoformat(today)
    d = (due_date - today_date).days
    if d < 0:
        kind = "overdue"
        text = f"{-d} g\u00fcn ge\u00e7ti" if d != -1 else "D\u00fcn"
    elif d == 0:
        kind = "today"
        text = "Bug\u00fcn"
    elif d == 1:
        kind = "soon"
        text = "Yar\u0131n"
    elif 2 <= d <= 6:
        kind = "soon"
        text = f"{d} g\u00fcn kald\u0131"
    else:
        kind = "later"
        months = ["Oca", "\u015eub", "Mar", "Nis", "May", "Haz", "Tem", "A\u011fu", "Eyl", "Eki", "Kas", "Ara"]
        text = f"{due_date.day} {months[due_date.month - 1]}"
    return (text, kind)
