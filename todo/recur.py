from datetime import datetime, timedelta
import calendar

def next_due(due: str, repeat: str) -> str:
    due_date = datetime.strptime(due, "%Y-%m-%d")
    if repeat == "daily":
        return (due_date + timedelta(days=1)).strftime("%Y-%m-%d")
    elif repeat == "weekly":
        return (due_date + timedelta(days=7)).strftime("%Y-%m-%d")
    elif repeat == "monthly":
        year, month, day = due_date.year, due_date.month, due_date.day
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        _, last_day = calendar.monthrange(next_year, next_month)
        if day > last_day:
            day = last_day
        return datetime(next_year, next_month, day).strftime("%Y-%m-%d")
    else:
        raise ValueError("invalid repeat")
