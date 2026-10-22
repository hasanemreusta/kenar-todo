"""Line folding for iCalendar (RFC 5545): physical lines are at most 75 bytes."""

LIMIT = 75


def fold_line(line: str) -> str:
    """Fold one content line; continuation pieces start with a single space. Never splits a UTF-8 character."""
    if len(line.encode("utf-8")) <= LIMIT:
        return line
    pieces, current, size, limit = [], "", 0, LIMIT
    for char in line:
        width = len(char.encode("utf-8"))
        if size + width > limit:
            pieces.append(current)
            current, size, limit = "", 0, LIMIT - 1   # the leading space counts toward the 75
        current += char
        size += width
    pieces.append(current)
    return "\r\n ".join(pieces)
