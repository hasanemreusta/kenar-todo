"""Text escaping for iCalendar (RFC 5545) TEXT values."""

BS = chr(92)   # a single backslash


def ics_escape(text: str) -> str:
    """Escape backslash (first), semicolon, comma and newlines."""
    text = text.replace(BS, BS + BS).replace(";", BS + ";").replace(",", BS + ",")
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", BS + "n")
