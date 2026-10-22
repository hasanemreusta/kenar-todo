"""Anti-aliased rounded shapes as plain pixel rows (tkinter canvas shapes are jagged).

rounded_rect_rows() returns rows of "#rrggbb" strings; gui.py turns them into PhotoImages.
Edge pixels are blended into the background colour, so a shape drawn on a keyed-out
(transparent) window colour gets a smooth, dark fringe instead of a stair-step edge.
"""
import math
from typing import List, Optional, Tuple

RGB = Tuple[int, int, int]


def _rgb(color: str) -> RGB:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def _mix(top: RGB, below: RGB, t: float) -> RGB:
    """t = how much of `top` shows over `below` (0..1)."""
    return tuple(round(below[i] + (top[i] - below[i]) * t) for i in range(3))


def _hex(c: RGB) -> str:
    return "#%02x%02x%02x" % c


def rounded_rect_rows(w: int, h: int, radius: float, fill: str, border: Optional[str] = None,
                      bg: str = "#000000", border_width: float = 1.0) -> List[List[str]]:
    """Pixel rows of a w x h rounded rectangle (radius >= min(w, h) / 2 gives a pill or circle)."""
    r = min(radius, w / 2, h / 2)
    fill_c, bg_c = _rgb(fill), _rgb(bg)
    border_c = _rgb(border) if border else None
    fill_hex, bg_hex = _hex(fill_c), _hex(bg_c)
    reach = r + border_width + 2          # farther than this from every edge: flat interior
    rows = []
    for y in range(h):
        py = y + 0.5
        row = []
        for x in range(w):
            px = x + 0.5
            if min(px, w - px, py, h - py) > reach:
                row.append(fill_hex)
                continue
            qx = abs(px - w / 2) - (w / 2 - r)
            qy = abs(py - h / 2) - (h / 2 - r)
            d = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r   # < 0 inside
            outer = min(1.0, max(0.0, 0.5 - d))
            if outer <= 0:
                row.append(bg_hex)
                continue
            color = fill_c
            if border_c:
                inner = min(1.0, max(0.0, 0.5 - (d + border_width)))
                color = _mix(fill_c, border_c, inner)
            row.append(_hex(_mix(color, bg_c, outer)))
        rows.append(row)
    return rows
