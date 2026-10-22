import urllib.parse
from datetime import date, timedelta

def google_calendar_url(title: str, details: str, due: str, repeat: str) -> str:
    base = "https://calendar.google.com/calendar/render"
    start = due.replace("-", "")
    end = (date.fromisoformat(due) + timedelta(days=1)).strftime("%Y%m%d")
    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start}/{end}",
        "details": details
    }
    if repeat in ["daily", "weekly", "monthly"]:
        params["recur"] = f"RRULE:FREQ={repeat.upper()}"
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"{base}?{query}"
