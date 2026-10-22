"""Where 'add to calendar' and 'send as mail' go: the default apps, or Google / Outlook on the web.

The web providers are plain prefilled links (no sign-in or API keys here): the browser opens the
provider's own 'new event' or 'compose' page and the user confirms there.
"""
from datetime import date, timedelta
from typing import Optional
from urllib.parse import quote, urlencode

from todo.gcal import google_calendar_url
from todo.ics import description
from todo.mailto import task_body, task_mailto
from todo.models import Task

CALENDARS = {"default": "Varsayılan uygulama", "google": "Google Takvim", "outlook": "Outlook"}
MAILS = {"default": "Varsayılan uygulama", "gmail": "Gmail", "outlook": "Outlook"}
CALENDAR_BUTTON = {"default": "Takvime ekle", "google": "Google Takvim'e ekle", "outlook": "Outlook'a ekle"}
MAIL_BUTTON = {"default": "Mail ile gönder", "gmail": "Gmail ile gönder", "outlook": "Outlook ile gönder"}


def _query(params: dict) -> str:
    return urlencode(params, quote_via=quote)


def gmail_url(subject: str, body: str) -> str:
    return "https://mail.google.com/mail/?" + _query({"view": "cm", "fs": "1", "su": subject, "body": body})


def outlook_mail_url(subject: str, body: str) -> str:
    return "https://outlook.live.com/mail/0/deeplink/compose?" + _query({"subject": subject, "body": body})


def outlook_calendar_url(title: str, details: str, due: str) -> str:
    end = date.fromisoformat(due) + timedelta(days=1)
    return "https://outlook.live.com/calendar/0/deeplink/compose?" + _query({
        "path": "/calendar/action/compose", "rru": "addevent", "subject": title, "body": details,
        "startdt": due, "enddt": end.isoformat(), "allday": "true"})


def calendar_link(task: Task, provider: str) -> Optional[str]:
    """Web link for the provider, or None when the default app (an .ics file) should be used."""
    if not task.due:
        raise ValueError("task has no due date")
    if provider == "google":
        return google_calendar_url(task.title, description(task), task.due, task.repeat)
    if provider == "outlook":
        return outlook_calendar_url(task.title, description(task), task.due)
    return None


def mail_link(task: Task, provider: str) -> str:
    body = task_body(task)
    if provider == "gmail":
        return gmail_url(task.title, body)
    if provider == "outlook":
        return outlook_mail_url(task.title, body)
    return task_mailto(task)
