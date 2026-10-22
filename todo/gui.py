"""Desktop todo widget: a soft dark pill docked to a screen edge that opens a rounded card.

tkinter, stdlib only. Closed: a slim vertical pill with a progress ring. Click it and the
task card slides out beside it; drag the card header to move it, it snaps to the nearest edge.
"""
import calendar
import json
import os
import tempfile
import tkinter as tk
import webbrowser
from datetime import date, datetime, timedelta
from tkinter import filedialog

from todo import service
from todo.aa import rounded_rect_rows
from todo.chips import due_chip
from todo.hotkey import HOTKEYS, GlobalHotkey
from todo.ics import tasks_to_ics
from todo.integrations import (CALENDAR_BUTTON, CALENDARS, MAIL_BUTTON, MAILS, calendar_link,
                                mail_link)
from todo.grouping import group_tasks, task_matches
from todo.nlp import due_label as nl_due_label, parse_natural
from todo.textparse import due_from_text, parse_tags

DATA_PATH = os.path.join(os.path.expanduser("~"), ".todo-app", "tasks.json")
UI_PATH = os.path.join(os.path.expanduser("~"), ".todo-app", "ui.json")

TRANSPARENT = "#010203"   # window colour keyed out by Windows, gives the rounded silhouette
CARD = "#0C0C0E"
ROW = "#161618"
ROW_HOVER = "#1F1F23"
FIELD = "#18181B"
BORDER = "#26262B"
TRACK = "#2A2A2F"
FG = "#F2F2F3"
MUTED = "#8E8E93"
GREEN = "#34D27B"
PRIORITY_COLORS = {"high": "#FF5C5C", "medium": "#FFB84D", "low": "#34D27B"}
CHIP_COLORS = {  # kind -> (background, foreground)
    "overdue": ("#3A1D21", "#FF7B7B"),
    "today": ("#3A2F14", "#FFC857"),
    "soon": ("#14303A", "#6FD3F0"),
    "later": ("#222226", "#9A9AA1"),
}
TAG_CHIP = ("#173324", "#4FD98A")

FONT = "Segoe UI"
FONT_LIGHT = "Segoe UI Light"
FONT_SEMI = "Segoe UI Semibold"
FONT_SYM = "Segoe UI Symbol"

SIDES = ("left", "right", "top", "bottom")
SIZES = {"S": (300, 520), "M": (360, 660), "L": (440, 780)}   # card sizes (width, height)
PILL_LONG = 372
PILL_SHORT = 84
GAP = 10          # between card and pill
EDGE = 10         # between window and screen edge
TASKBAR = 48      # keep clear of the Windows taskbar
CARD_RADIUS = 40
CARD_PAD = 26
SECTION_LABELS = {"pinned": "SABİTLENEN", "overdue": "GECIKM\u0130\u015e", "today": "BUG\u00dcN", "upcoming": "YAKLA\u015eAN",
                  "nodate": "TARS\u0130Z", "done": "TAMAMLANAN"}
SECTION_COLORS = {"pinned": GREEN, "overdue": "#FF7B7B", "today": "#FFC857", "upcoming": "#6FD3F0",
                  "nodate": MUTED, "done": MUTED}
REPEAT_LABELS = {"daily": "Her gün", "weekly": "Her hafta", "monthly": "Her ay"}
MONTHS_SHORT = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
WEEKDAYS_SHORT = ["Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pz"]
SHORT_PROVIDER = {"default": "Varsay\u0131lan", "google": "Google", "gmail": "Gmail", "outlook": "Outlook"}
HINT = "Yeni g\u00f6rev...  \u00f6r. rapor cuma !y\u00fcksek #i\u015f"
DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
          "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def _cache():
    """Per-Tk-root image cache (PhotoImages die with their root, so the cache lives on it)."""
    root = tk._default_root
    if not hasattr(root, "_aa_cache"):
        root._aa_cache = {}
    return root._aa_cache


def aa_image(w, h, radius, fill, border=None, bg=TRANSPARENT, border_width=1.0):
    """Cached anti-aliased rounded shape as a PhotoImage."""
    cache = _cache()
    key = (w, h, radius, fill, border, bg, border_width)
    if key not in cache:
        rows = rounded_rect_rows(w, h, radius, fill, border, bg, border_width)
        img = tk.PhotoImage(width=w, height=h)
        img.put(" ".join("{" + " ".join(row) + "}" for row in rows))
        cache[key] = img
    return cache[key]


def round_rect(canvas, x0, y0, x1, y1, r, **kw):
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
           x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return canvas.create_polygon(pts, smooth=True, **kw)


def corner_images(r):
    """The four anti-aliased corner quadrants of the card background (so resizing stays cheap)."""
    cache = _cache()
    key = ("corners", r)
    if key not in cache:
        rows = rounded_rect_rows(2 * r, 2 * r, r, CARD, BORDER, TRANSPARENT, 1.2)

        def make(part):
            img = tk.PhotoImage(width=r, height=r)
            img.put(" ".join("{" + " ".join(row) + "}" for row in part))
            return img
        cache[key] = (make([row[:r] for row in rows[:r]]), make([row[r:] for row in rows[:r]]),
                      make([row[:r] for row in rows[r:]]), make([row[r:] for row in rows[r:]]))
    return cache[key]


class StickyApp:
    def __init__(self, root: tk.Tk, path: str = DATA_PATH, ui_path: str = UI_PATH, start_open: bool = True):
        self.root = root
        self.path = path
        self.ui_path = ui_path
        self.tasks = []
        self.is_open = False
        self._busy = False
        self._press = None
        self._grip = None
        self._pill_resize = None
        self.pill_scale = 1.0
        self.calendar_provider = "default"
        self.mail_provider = "default"
        self.hotkey_name = "ctrl_alt_n"
        self.hotkey = None
        self._hover = False
        self._menu = None
        self.page_id = None
        self.page_state = {}
        self._page_widgets = {}
        self._save_job = None
        self.query = ""
        self.view_filter = "all"
        self._undo_cb = None
        self._undo = None
        self._undo_job = None
        self.side, self.pos, self.cw, self.ch, self.alpha = self.load_ui()
        self.build_window()
        self.build_card()
        self.build_tab()
        self.refresh()
        self.watch()
        self.show_card(animate=False) if start_open else self.set_collapsed_geometry()
        self.root.after(400, self.warm_pill_images)

    def warm_pill_images(self):
        """Render the pill for both orientations ahead of time, so snapping to another edge is instant."""
        k = self.pill_scale
        long_side, short_side = round(PILL_LONG * k), round(PILL_SHORT * k)
        for w, h in ((long_side, short_side), (short_side, long_side)):
            for outline in (GREEN, BORDER):
                aa_image(w, h, min(w, h) / 2, CARD, outline, TRANSPARENT, 1.4)

    @property
    def collapsed(self):
        return not self.is_open

    @property
    def horizontal(self):
        return self.side in ("top", "bottom")

    # ---- persisted layout ------------------------------------------------------
    def screen(self):
        return self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def clamp_size(self, cw, ch):
        sw, sh = self.screen()
        return (max(280, min(int(cw), min(620, sw - 120))), max(380, min(int(ch), sh - 140)))

    def load_ui(self):
        try:
            with open(self.ui_path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        except (OSError, ValueError):
            data = {}
        side = data.get("side") if data.get("side") in SIDES else "right"
        try:
            pos = int(data.get("pos", data.get("y", 90)))
            cw, ch = self.clamp_size(data.get("cw", SIZES["M"][0]), data.get("ch", SIZES["M"][1]))
            alpha = min(1.0, max(0.5, float(data.get("alpha", 1.0))))
            self.pill_scale = min(1.6, max(0.6, float(data.get("pill", 1.0))))
            if data.get("calendar") in CALENDARS:
                self.calendar_provider = data["calendar"]
            if data.get("mail") in MAILS:
                self.mail_provider = data["mail"]
            if data.get("hotkey") in HOTKEYS:
                self.hotkey_name = data["hotkey"]
        except (TypeError, ValueError):
            pos, (cw, ch), alpha = 90, SIZES["M"], 1.0
        return side, pos, cw, ch, alpha

    def save_ui(self):
        try:
            os.makedirs(os.path.dirname(self.ui_path), exist_ok=True)
            with open(self.ui_path, "w", encoding="utf-8") as f:
                json.dump({"side": self.side, "pos": self.pos, "cw": self.cw, "ch": self.ch,
                           "alpha": self.alpha, "pill": self.pill_scale, "calendar": self.calendar_provider,
                           "mail": self.mail_provider, "hotkey": self.hotkey_name}, f)
        except OSError:
            pass

    # ---- window geometry --------------------------------------------------------
    def build_window(self):
        r = self.root
        r.title("Yapılacaklar")
        icon = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "packaging", "todo.png")
        if os.path.exists(icon):
            try:
                r.iconphoto(True, tk.PhotoImage(file=icon))
            except tk.TclError:
                pass
        r.overrideredirect(True)
        r.attributes("-topmost", True)
        r.attributes("-alpha", self.alpha)
        r.configure(bg=TRANSPARENT)
        try:
            r.attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            pass

    def pill_size(self):
        long_side, short_side = round(PILL_LONG * self.pill_scale), round(PILL_SHORT * self.pill_scale)
        return (long_side, short_side) if self.horizontal else (short_side, long_side)

    def open_size(self):
        pw, ph = self.pill_size()
        if self.horizontal:
            return max(self.cw, pw), self.ch + GAP + ph
        return self.cw + GAP + pw, max(self.ch, ph)

    def clamp_pos(self, pos, length):
        sw, sh = self.screen()
        limit = (sw if self.horizontal else sh - TASKBAR) - length - 8
        return max(8, min(pos, limit))

    def set_geo(self, w, h):
        sw, sh = self.screen()
        if self.horizontal:
            x = self.clamp_pos(self.pos, w)
            y = EDGE if self.side == "top" else sh - TASKBAR - EDGE - h
        else:
            y = self.clamp_pos(self.pos, h)
            x = EDGE if self.side == "left" else sw - EDGE - w
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def set_collapsed_geometry(self):
        self.is_open = False
        self.layout()
        self.set_geo(*self.pill_size())
        self.draw_tab()

    def layout(self):
        """Pill on the screen-edge side, card beside it (revealed from behind the pill)."""
        pw, ph = self.pill_size()
        self.tab.config(width=pw, height=ph)
        # place() keeps options from the previous call (e.g. relx=1 from the right edge), so start clean:
        # otherwise after moving to another edge the pill sits outside the window until the next relayout
        self.tab.place_forget()
        self.card.place_forget()
        if self.side == "right":
            self.tab.place(relx=1, y=0, anchor="ne")
            self.card.place(relx=1, x=-(pw + GAP), y=0, anchor="ne")
        elif self.side == "left":
            self.tab.place(x=0, y=0, anchor="nw")
            self.card.place(x=pw + GAP, y=0, anchor="nw")
        elif self.side == "top":
            self.tab.place(x=0, y=0, anchor="nw")
            self.card.place(x=0, y=ph + GAP, anchor="nw")
        else:
            self.tab.place(x=0, rely=1, anchor="sw")
            self.card.place(x=0, rely=1, y=-(ph + GAP), anchor="sw")
        if not self.is_open:
            self.card.place_forget()
        tk.Misc.lift(self.tab)

    def ease(self, t):
        return 1 - (1 - t) ** 3

    def animate(self, steps, frame, done=None, delay=13):
        self._busy = True

        def tick(i=1):
            frame(self.ease(i / steps))
            if i < steps:
                self.root.after(delay, tick, i + 1)
            else:
                self._busy = False
                if done:
                    done()
        tick()

    # ---- open / close ---------------------------------------------------------------
    def toggle_collapse(self, animate=True):
        if self._busy:
            return
        self.close_menu()
        if self.is_open:
            self.hide_card(animate)
        else:
            self.show_card(animate)

    def show_card(self, animate=True):
        self.is_open = True
        self.layout()
        self.refresh()
        pw, ph = self.pill_size()
        w1, h1 = self.open_size()
        if not animate:
            self.set_geo(w1, h1)
            return
        self.set_geo(pw, ph)
        self.animate(11, lambda p: self.set_geo(round(pw + (w1 - pw) * p), round(ph + (h1 - ph) * p)),
                     self.after_open)

    def after_open(self):
        self.draw_tab()
        if getattr(self, "_focus_entry", False):
            self._focus_entry = False
            self.entry.focus_force()

    def hide_card(self, animate=True):
        self.save_ui()
        pw, ph = self.pill_size()
        w0, h0 = self.open_size()
        if not animate:
            self.set_collapsed_geometry()
            return
        self.animate(10, lambda p: self.set_geo(round(w0 + (pw - w0) * p), round(h0 + (ph - h0) * p)),
                     self.set_collapsed_geometry)

    # ---- dragging and docking -------------------------------------------------------------
    def start_drag(self, event):
        self._press = (event.x_root, event.y_root, self.root.winfo_x(), self.root.winfo_y(), False)

    def do_drag(self, event, free=None):
        if not self._press or self._busy:
            return
        px, py, wx, wy, moved = self._press
        dx, dy = event.x_root - px, event.y_root - py
        if not moved and abs(dx) + abs(dy) < 4:
            return
        self._press = (px, py, wx, wy, True)
        self.root.geometry(f"+{wx + dx}+{wy + dy}")

    def end_drag(self, event, free=None, click_toggles=False):
        press, self._press = self._press, None
        if not press:
            return
        if not press[4]:
            if click_toggles:
                self.toggle_collapse()
            return
        # where the window was dropped, from the pointer (winfo_x/y can lag one motion event behind)
        x = press[2] + event.x_root - press[0]
        y = press[3] + event.y_root - press[1]
        self.redock(self.nearest_edge(x, y), from_drag=True, at=(x, y))

    def nearest_edge(self, x=None, y=None):
        sw, sh = self.screen()
        r = self.root
        x = r.winfo_x() if x is None else x
        y = r.winfo_y() if y is None else y
        w, h = r.winfo_width(), r.winfo_height()
        # gap between each window edge and the matching screen edge; the closest edge wins, but the
        # current edge is kept when it is about as close, so sliding along an edge never flips sides
        distance = {"left": x, "right": sw - (x + w), "top": y, "bottom": sh - TASKBAR - (y + h)}
        distance = {k: max(0, v) for k, v in distance.items()}   # pushed past an edge counts as touching it
        best = min(distance, key=distance.get)
        return self.side if distance[self.side] <= distance[best] + 60 else best

    def redock(self, side, keep_pos=True, from_drag=False, at=None):
        """Snap the window to a screen edge. After a drag it stays where it was dropped along that edge
        (slide up/down on the side edges, left/right on the top/bottom edges)."""
        x, y = at if at else (self.root.winfo_x(), self.root.winfo_y())
        was_horizontal = self.horizontal
        self.side = side
        self.layout()
        w, h = self.open_size() if self.is_open else self.pill_size()
        if from_drag or was_horizontal != self.horizontal:
            along = x if self.horizontal else y
        else:
            along = self.pos
        if not keep_pos:
            sw, sh = self.screen()
            along = (sw - w) // 2 if self.horizontal else (sh - TASKBAR - h) // 2
        self.pos = self.clamp_pos(along, w if self.horizontal else h)
        self.set_geo(w, h)
        self.draw_card_bg()
        self.draw_tab()
        self.save_ui()

    # ---- resizing -----------------------------------------------------------------------------
    def set_size(self, cw, ch, live=False):
        self.cw, self.ch = self.clamp_size(cw, ch)
        pad = CARD_PAD
        self.card.config(width=self.cw, height=self.ch)
        self.card.itemconfigure(self._inner_win, width=self.cw - 2 * pad, height=self.ch - 2 * pad)
        self.draw_card_bg()
        self.layout()
        if self.is_open:
            self.set_geo(*self.open_size())
        if not live:
            self.refresh()
            self.save_ui()

    def build_grip(self):
        self.grip = tk.Canvas(self.card, width=18, height=18, bg=CARD, highlightthickness=0, bd=0)
        self._grip_win = self.card.create_window(0, 0, window=self.grip, anchor="center")
        self.grip.bind("<Button-1>", self.grip_press)
        self.grip.bind("<B1-Motion>", self.grip_move)
        self.grip.bind("<ButtonRelease-1>", self.grip_release)

    def place_grip(self):
        """Grip sits on the card corner farthest from the screen edge, so dragging grows the card."""
        w, h, off = self.cw, self.ch, 22
        at_bottom = self.side != "bottom"
        at_right = self.side in ("left", "top", "bottom")
        gx = w - off if at_right else off
        gy = h - off if at_bottom else off
        self.card.coords(self._grip_win, gx, gy)
        self.grip.delete("all")
        sx, sy = (1 if at_right else -1), (1 if at_bottom else -1)
        for i in range(3):
            for j in range(3 - i):
                x, y = 9 + sx * (4 - 4 * i), 9 + sy * (4 - 4 * j)
                self.grip.create_oval(x - 1, y - 1, x + 1.5, y + 1.5, fill=MUTED, outline="")
        diagonal = at_right == at_bottom
        self.grip.config(cursor="size_nw_se" if diagonal else "size_ne_sw")
        tk.Misc.lift(self.grip)

    def grip_press(self, event):
        self._grip = (event.x_root, event.y_root, self.cw, self.ch)

    def grip_move(self, event):
        if not self._grip:
            return
        x0, y0, cw0, ch0 = self._grip
        dx, dy = event.x_root - x0, event.y_root - y0
        cw = cw0 - dx if self.side == "right" else cw0 + dx
        ch = ch0 - dy if self.side == "bottom" else ch0 + dy
        self.set_size(cw, ch, live=True)

    def grip_release(self, event):
        if self._grip:
            self._grip = None
            self.set_size(self.cw, self.ch)

    # ---- docked pill --------------------------------------------------------------------
    def build_tab(self):
        self.tab = tk.Canvas(self.root, bg=TRANSPARENT, width=PILL_SHORT, height=PILL_LONG,
                             highlightthickness=0, bd=0, cursor="hand2")
        self.tab.bind("<Button-1>", self.tab_press)
        self.tab.bind("<B1-Motion>", self.tab_motion)
        self.tab.bind("<ButtonRelease-1>", self.tab_release)
        self.tab.bind("<Motion>", self.tab_cursor)
        self.tab.bind("<Enter>", lambda e: self.set_hover(True))
        self.tab.bind("<Leave>", lambda e: self.set_hover(False))
        self.tab.bind("<MouseWheel>", self.tab_wheel)

    # -- the pill can be resized: drag the dotted grip at its far end, scroll over it, or use the menu
    def in_pill_grip(self, event):
        pw, ph = self.pill_size()
        along, length = (event.x, pw) if self.horizontal else (event.y, ph)
        return along > length - 30

    def tab_cursor(self, event):
        if self._pill_resize is None:
            self.tab.config(cursor=("size_we" if self.horizontal else "size_ns") if self.in_pill_grip(event)
                            else "hand2")

    def tab_press(self, event):
        if self.in_pill_grip(event):
            self._pill_resize = (event.x_root if self.horizontal else event.y_root, self.pill_scale)
        else:
            self.start_drag(event)

    def tab_motion(self, event):
        if self._pill_resize is None:
            self.do_drag(event)
            return
        start, scale0 = self._pill_resize
        delta = (event.x_root if self.horizontal else event.y_root) - start
        self.set_pill_scale(scale0 + delta / PILL_LONG, save=False)

    def tab_wheel(self, event):
        if self.is_open or self._busy:
            return
        self.set_pill_scale(self.pill_scale + (0.05 if event.delta > 0 else -0.05))

    def set_pill_scale(self, scale, save=True):
        sw, sh = self.screen()
        limit = (sw if self.horizontal else sh - TASKBAR) - 40
        self.pill_scale = round(max(0.6, min(1.6, scale, limit / PILL_LONG)), 2)
        self.layout()
        self.set_geo(*(self.open_size() if self.is_open else self.pill_size()))
        self.draw_tab()
        if save:
            self.save_ui()

    def tab_release(self, event):
        if self._pill_resize is not None:
            self._pill_resize = None
            self.save_ui()
            return
        # a click on the "+" circle opens the card with the cursor in the entry;
        # a click on a counter (Bug\u00fcn / \u00d6nemli / Toplam) opens that smart list
        along = event.x if self.horizontal else event.y
        k = self.pill_scale
        self._focus_entry = along < 96 * k
        if self._press and not self._press[4] and not self.is_open:
            for i, key in enumerate(("today", "important", "all")):
                center = (160 + i * 80) * k if self.horizontal else (146 + i * 76) * k
                if abs(along - center) < 38 * k:
                    self.view_filter = key
        self.end_drag(event, click_toggles=True)

    def set_hover(self, on):
        self._hover = on
        self.draw_tab()

    def pending_counts(self):
        today = date.today().isoformat()
        pending = [t for t in self.tasks if not t.done]
        return (sum(1 for t in pending if t.due and t.due <= today),
                sum(1 for t in pending if t.priority == "high"),
                len(pending))

    def draw_tab(self):
        c = self.tab
        c.delete("all")
        k = self.pill_scale
        pw, ph = self.pill_size()
        r = round(20 * k)
        c.create_image(0, 0, anchor="nw", image=aa_image(
            pw, ph, min(pw, ph) / 2, CARD, GREEN if self._hover else BORDER, TRANSPARENT, 1.4))
        today, high, pending = self.pending_counts()
        counters = (("BUGÜN", "#FFC857", today), ("ÖNEMLİ", "#FF7B7B", high),
                    ("TOPLAM", "#E8E8EA", pending))
        num_font, label_font = (FONT_SEMI, max(8, round(14 * k))), (FONT_SEMI, max(6, round(7 * k)))
        plus_r = round(21 * k)

        def counter(cx, cy, label, color, value):
            c.create_image(cx - r, cy - r, anchor="nw",
                           image=aa_image(2 * r, 2 * r, r, CARD, color if value else TRACK, CARD, 2.2 * k))
            c.create_text(cx, cy, text=str(value), fill=FG if value else MUTED, font=num_font)
            c.create_text(cx, cy + 32 * k, text=label, fill=color if value else MUTED, font=label_font)

        if self.horizontal:
            cy0 = ph / 2
            c.create_image(42 * k - plus_r, cy0 - plus_r, anchor="nw",
                           image=aa_image(2 * plus_r, 2 * plus_r, plus_r, GREEN, None, CARD))
            c.create_text(42 * k, cy0 - k, text="+", fill="#06150C", font=(FONT, max(12, round(24 * k))))
            c.create_line(96 * k, 24 * k, 96 * k, ph - 24 * k, fill=BORDER)
            for i, (label, color, value) in enumerate(counters):
                counter((160 + i * 80) * k, 34 * k, label, color, value)
            for i in range(3):   # resize grip at the right end
                c.create_oval(pw - 15, ph / 2 - 9 + i * 9, pw - 12, ph / 2 - 6 + i * 9, fill=TRACK, outline="")
            return
        cx = pw / 2
        c.create_image(cx - plus_r, 51 * k - plus_r, anchor="nw",
                       image=aa_image(2 * plus_r, 2 * plus_r, plus_r, GREEN, None, CARD))
        c.create_text(cx, 51 * k, text="+", fill="#06150C", font=(FONT, max(12, round(24 * k))))
        c.create_line(24 * k, 100 * k, pw - 24 * k, 100 * k, fill=BORDER)
        for i, (label, color, value) in enumerate(counters):
            counter(cx, (146 + i * 76) * k, label, color, value)
        for i in range(3):       # resize grip at the bottom end
            c.create_oval(cx - 9 + i * 9, ph - 15, cx - 6 + i * 9, ph - 12, fill=TRACK, outline="")

    # ---- card -----------------------------------------------------------------------------
    def button(self, parent, text, command, fg=MUTED, size=12):
        lbl = tk.Label(parent, text=text, bg=parent["bg"], fg=fg, font=(FONT, size), cursor="hand2")
        lbl.bind("<Button-1>", lambda e: command())
        lbl.bind("<Enter>", lambda e: lbl.config(fg=FG))
        lbl.bind("<Leave>", lambda e: lbl.config(fg=fg))
        return lbl

    def draw_card_bg(self):
        """Rounded dark card: straight edges from rectangles, anti-aliased corners from images."""
        c, w, h, r = self.card, self.cw, self.ch, CARD_RADIUS
        c.delete("bgshape")

        def rect(x0, y0, x1, y1, color):
            c.create_rectangle(x0, y0, x1, y1, fill=color, outline="", tags="bgshape")
        rect(r, 1, w - r, h - 1, CARD)
        rect(1, r, r, h - r, CARD)
        rect(w - r, r, w - 1, h - r, CARD)
        rect(r, 0, w - r, 1, BORDER)
        rect(r, h - 1, w - r, h, BORDER)
        rect(0, r, 1, h - r, BORDER)
        rect(w - 1, r, w, h - r, BORDER)
        tl, tr, bl, br = corner_images(r)
        for img, (x, y) in ((tl, (0, 0)), (tr, (w - r, 0)), (bl, (0, h - r)), (br, (w - r, h - r))):
            c.create_image(x, y, anchor="nw", image=img, tags="bgshape")
        c.tag_lower("bgshape")
        self.place_grip()

    def build_card(self):
        pad = CARD_PAD
        self.card = tk.Canvas(self.root, bg=TRANSPARENT, width=self.cw, height=self.ch,
                              highlightthickness=0, bd=0)
        inner = tk.Frame(self.card, bg=CARD)
        self._inner_win = self.card.create_window(pad, pad, window=inner, anchor="nw",
                                                  width=self.cw - 2 * pad, height=self.ch - 2 * pad)
        self.build_grip()
        self.draw_card_bg()

        head = tk.Frame(inner, bg=CARD)
        head.pack(fill="x", pady=(2, 0))
        self.inner = inner
        self.title = tk.Label(head, text="Yap\u0131lacaklar", bg=CARD, fg=FG, font=(FONT_SEMI, 20))
        self.title.pack(side="left")
        self.back_btn = tk.Label(head, text="\u2039  Geri", bg=CARD, fg=GREEN, font=(FONT_SEMI, 13),
                                 cursor="hand2")
        self.back_btn.bind("<Button-1>", lambda e: self.close_page())
        self.button(head, "\u2715", self.root.destroy, size=10).pack(side="right")
        self.button(head, "\u2013", self.toggle_collapse, size=13).pack(side="right", padx=10)
        self.menu_btn = self.button(head, "\u22ef", lambda: self.open_menu(self.menu_btn), size=15)
        self.menu_btn.pack(side="right")
        self.search_btn = self.button(head, "\u2315", self.toggle_search, size=14)
        self.search_btn.pack(side="right")
        view = tk.Frame(inner, bg=CARD)
        view.pack(fill="both", expand=True)
        self.list_view = view
        self.date_label = tk.Label(view, text="", bg=CARD, fg=MUTED, font=(FONT, 10), anchor="w")
        self.date_label.pack(fill="x", pady=(0, 16))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(view, textvariable=self.search_var, bg=FIELD, fg=FG, relief="flat",
                                     font=(FONT, 10), insertbackground=FG, highlightthickness=1,
                                     highlightbackground=BORDER, highlightcolor=GREEN)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        self.search_entry.bind("<Escape>", lambda e: self.toggle_search())
        for w in (head, self.title, self.date_label):
            w.bind("<Button-1>", self.start_drag)
            w.bind("<B1-Motion>", lambda e: self.do_drag(e, free=True))
            w.bind("<ButtonRelease-1>", lambda e: self.end_drag(e, free=True))

        self.entry = tk.Entry(view, bg=FIELD, fg=MUTED, relief="flat", font=(FONT, 10),
                              insertbackground=FG, highlightthickness=1,
                              highlightbackground=BORDER, highlightcolor=GREEN)
        self.entry.pack(fill="x", ipady=9, pady=(0, 8))
        self.entry.insert(0, HINT)
        self.entry.bind("<FocusIn>", self.on_entry_focus)
        self.entry.bind("<FocusOut>", self.on_entry_blur)
        self.entry.bind("<Return>", self.add_from_entry)
        self.entry.bind("<Escape>", lambda e: self.toggle_collapse())
        self.entry.bind("<KeyRelease>", self.update_preview)
        self.preview = tk.Frame(view, bg=CARD)      # shown only while the text has dates/tags/... in it
        self.tabs = tk.Frame(view, bg=CARD)
        self.tabs.pack(fill="x", pady=(0, 6))

        holder = tk.Frame(view, bg=CARD)
        holder.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(holder, bg=CARD, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.list_frame = tk.Frame(self.canvas, bg=CARD)
        self._window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.list_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._window, width=e.width))
        self.root.bind_all("<MouseWheel>", self.on_wheel)
        self.root.bind_all("<Control-n>", lambda e: self.focus_entry())
        self.root.bind_all("<Control-f>", lambda e: self.toggle_search(True))
        self.toast = tk.Frame(inner, bg=ROW_HOVER, highlightthickness=1, highlightbackground=BORDER)
        self.toast_label = tk.Label(self.toast, text="", bg=ROW_HOVER, fg=FG, font=(FONT, 9), padx=12, pady=6)
        self.toast_label.pack(side="left")
        undo = tk.Label(self.toast, text="Geri al", bg=ROW_HOVER, fg=GREEN, font=(FONT_SEMI, 9),
                        padx=12, pady=6, cursor="hand2")
        undo.pack(side="left")
        undo.bind("<Button-1>", lambda e: self.run_undo())
        self.toast_undo = undo

    def on_wheel(self, event):
        if not self.is_open or self._menu is not None:
            return
        canvas, frame = ((self.page_canvas, self.page_body) if self.page_id is not None
                         else (self.canvas, self.list_frame))
        if frame.winfo_reqheight() > canvas.winfo_height():
            canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def on_entry_focus(self, event=None):
        if self.entry.get() == HINT:
            self.entry.delete(0, "end")
            self.entry.config(fg=FG)

    def on_entry_blur(self, event=None):
        if not self.entry.get().strip():
            self.entry.delete(0, "end")
            self.entry.insert(0, HINT)
            self.entry.config(fg=MUTED)

    # ---- data -----------------------------------------------------------------------------
    def add_from_entry(self, event=None):
        text = self.entry.get().strip()
        if not text or text == HINT:
            return
        parsed = parse_natural(text, date.today().isoformat())
        if not parsed["title"]:
            return
        try:
            task = service.create(self.path, parsed["title"], parsed["priority"], parsed["due"], parsed["tags"])
            if parsed["repeat"]:
                service.update(self.path, task.id, {"repeat": parsed["repeat"]})
        except Exception as e:  # keep the widget alive on bad input
            print(f"Error creating task: {e}")
        self.entry.delete(0, "end")
        self.update_preview()
        self.refresh()

    def update_preview(self, event=None):
        """Show, as chips under the entry, what the quick-add text will set (date, repeat, priority, tags)."""
        for w in self.preview.winfo_children():
            w.destroy()
        text = self.entry.get().strip()
        found = [] if not text or text == HINT else parse_natural(text, date.today().isoformat())["found"]
        if not found:
            self.preview.pack_forget()
            return
        style = {"due": ("▦ ", CHIP_COLORS["soon"]), "repeat": ("↻ ", CHIP_COLORS["later"]),
                 "tag": ("", TAG_CHIP)}
        for kind, label in found:
            if kind == "priority":
                prefix, colors = "! ", CHIP_COLORS["overdue"] if label.startswith("Y") else CHIP_COLORS["later"]
            else:
                prefix, colors = style[kind]
            self.chip(self.preview, prefix + label, colors).pack(side="left", padx=(0, 5))
        tk.Label(self.preview, text="Enter ↵", bg=CARD, fg=MUTED, font=(FONT, 8)).pack(side="right")
        if not self.preview.winfo_ismapped():
            self.preview.pack(fill="x", pady=(0, 8), before=self.tabs)

    def passes_filter(self, task):
        today = date.today().isoformat()
        if self.view_filter == "today":
            return not task.done and bool(task.due) and task.due <= today
        if self.view_filter == "important":
            return not task.done and task.priority == "high"
        return True

    def set_filter(self, key):
        self.view_filter = key
        self.refresh()

    def draw_filter_tabs(self):
        for w in self.tabs.winfo_children():
            w.destroy()
        today, high, _ = self.pending_counts()
        for key, label, count in (("all", "Tümü", len(self.tasks)), ("today", "Bugün", today),
                                  ("important", "Önemli", high)):
            self.pill(self.tabs, f"{label}  {count}", lambda k=key: self.set_filter(k),
                      active=self.view_filter == key).pack(side="left", padx=(0, 6))

    def refresh(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.tasks = service.list_all(self.path)
        shown = [t for t in self.tasks if task_matches(t, self.query) and self.passes_filter(t)]
        for key, items in group_tasks(shown, date.today().isoformat()):
            self.add_section(key, len(items))
            for task in items:
                self.add_row(task)
        if not shown:
            empty = {"today": "Bug\u00fcn i\u00e7in bir \u015fey yok, keyfine bak",
                     "important": "\u00d6nemli bekleyen g\u00f6rev yok"}
            icon, text = (("\u2315", "Sonu\u00e7 yok") if self.query
                          else ("\u2713", empty.get(self.view_filter, "Her \u015fey tamam")))
            tk.Label(self.list_frame, text=icon, bg=CARD, fg=GREEN if not self.query else MUTED,
                     font=(FONT_LIGHT, 34)).pack(pady=(30, 0))
            tk.Label(self.list_frame, text=text, bg=CARD, fg=MUTED, font=(FONT, 10)).pack()
        self.update_stats()

    def add_section(self, key, count):
        head = tk.Frame(self.list_frame, bg=CARD)
        head.pack(fill="x", pady=(12, 2))
        tk.Label(head, text=SECTION_LABELS[key], bg=CARD, fg=SECTION_COLORS[key],
                 font=(FONT_SEMI, 8)).pack(side="left")
        tk.Label(head, text=str(count), bg=CARD, fg=MUTED, font=(FONT, 8)).pack(side="left", padx=6)
        if key == "done":
            self.button(head, "Temizle", self.clear_done, size=8).pack(side="right")

    def clear_done(self):
        for task in [t for t in self.tasks if t.done]:
            service.delete(self.path, task.id)
        self.refresh()

    def update_stats(self):
        today = date.today()
        text = f"{DAYS[today.weekday()]}, {today.day} {MONTHS[today.month - 1]}"
        pending = sum(1 for t in self.tasks if not t.done)
        self.date_label.config(text=f"{text}  \u00b7  {pending} bekliyor" if pending else text)
        self.draw_filter_tabs()
        self.draw_tab()

    def chip(self, parent, text, colors):
        return tk.Label(parent, text=text, bg=colors[0], fg=colors[1], font=(FONT, 8), padx=8, pady=1)

    def add_row(self, task):
        """One soft rounded row; clicking it opens the detail page."""
        today = date.today().isoformat()
        row = tk.Canvas(self.list_frame, bg=CARD, highlightthickness=0, bd=0)
        row.pack(fill="x", pady=4)
        body = tk.Frame(row, bg=ROW)
        win = row.create_window(0, 0, window=body, anchor="nw")
        line = tk.Frame(body, bg=ROW)
        line.pack(fill="x")

        check = tk.Canvas(line, width=24, height=24, bg=ROW, highlightthickness=0, bd=0, cursor="hand2")
        if task.done:
            check.create_image(0, 0, anchor="nw", image=aa_image(24, 24, 12, GREEN, None, ROW))
            check.create_text(12, 12, text="✓", fill="#06150C", font=(FONT_SEMI, 9))
        else:
            check.create_image(0, 0, anchor="nw", image=aa_image(
                24, 24, 12, ROW, PRIORITY_COLORS[task.priority], ROW, 2.2))
        check.bind("<Button-1>", lambda e, i=task.id, d=task.done, c=check: self.on_toggle(i, d, c))
        check.pack(side="left", padx=(12, 8), pady=12, anchor="n")

        delete = self.button(line, "✕", lambda i=task.id: self.on_delete(i), size=9)
        delete.pack(side="right", padx=(4, 12), anchor="n", pady=12)

        center = tk.Frame(line, bg=ROW)
        center.pack(side="left", fill="x", expand=True, pady=10)
        font = (FONT, 10, "overstrike") if task.done else (FONT_SEMI, 10)
        label = tk.Label(center, text=("★  " if task.pinned else "") + task.title, bg=ROW,
                         fg=MUTED if task.done else FG, font=font, anchor="w", justify="left",
                         wraplength=self.cw - 150)
        label.pack(fill="x")
        chips = tk.Frame(center, bg=ROW)
        due = due_chip(task.due, today)
        if due:
            colors = CHIP_COLORS["later"] if task.done else CHIP_COLORS[due[1]]
            self.chip(chips, due[0], colors).pack(side="left", padx=(0, 5), pady=(5, 0))
        if task.repeat:
            self.chip(chips, "↻ " + REPEAT_LABELS[task.repeat], CHIP_COLORS["later"]).pack(
                side="left", padx=(0, 5), pady=(5, 0))
        if task.subtasks:
            finished = sum(1 for s in task.subtasks if s["done"])
            self.chip(chips, f"☑ {finished}/{len(task.subtasks)}", CHIP_COLORS["later"]).pack(
                side="left", padx=(0, 5), pady=(5, 0))
        for tag in task.tags[:2]:
            self.chip(chips, "#" + tag, TAG_CHIP).pack(side="left", padx=(0, 5), pady=(5, 0))
        if len(task.tags) > 2:
            self.chip(chips, f"+{len(task.tags) - 2}", CHIP_COLORS["later"]).pack(
                side="left", padx=(0, 5), pady=(5, 0))
        if task.note.strip():
            self.chip(chips, "≡ not", CHIP_COLORS["later"]).pack(side="left", padx=(0, 5), pady=(5, 0))
        clickable = [line, center, label]
        if chips.winfo_children():
            chips.pack(fill="x")
            clickable.append(chips)
            clickable.extend(chips.winfo_children())
        for w in clickable:
            w.bind("<Button-1>", lambda e, i=task.id: self.open_page(i), add="+")

        def fit(event=None):
            body.update_idletasks()
            w, h = max(row.winfo_width(), 50), body.winfo_reqheight()
            row.config(height=h)
            row.itemconfigure(win, width=w, height=h)
            row.delete("bg")
            row.create_image(0, 0, anchor="nw", image=aa_image(w, h, 18, ROW, None, CARD), tags="bg")
            row.tag_lower("bg")
            row._size = (w, h)
        row.bind("<Configure>", fit)

        def tint(color):
            w, h = getattr(row, "_size", (0, 0))
            if w:
                row.itemconfigure("bg", image=aa_image(w, h, 18, color, None, CARD))
            stack = [body]
            while stack:
                widget = stack.pop()
                if widget.cget("bg") in (ROW, ROW_HOVER):
                    widget.config(bg=color)
                stack.extend(widget.winfo_children())
        for w in (row, body, line, center, chips):
            w.bind("<Enter>", lambda e: tint(ROW_HOVER), add="+")
            w.bind("<Leave>", lambda e: tint(ROW), add="+")

    def pill(self, parent, text, command, active=False, color=GREEN, fg=None, bg=None):
        lbl = tk.Label(parent, text=text, bg=color if active else (bg or FIELD),
                       fg="#06150C" if active else (fg or MUTED), font=(FONT_SEMI, 8), padx=11, pady=4,
                       cursor="hand2")
        lbl.bind("<Button-1>", lambda e: command())
        return lbl

    def soft_panel(self, parent, fill=ROW, radius=18, pady=(0, 10)):
        """A rounded, anti-aliased panel; returns the frame to put content in."""
        c = tk.Canvas(parent, bg=CARD, highlightthickness=0, bd=0)
        c.pack(fill="x", pady=pady)
        f = tk.Frame(c, bg=fill)
        win = c.create_window(0, 0, window=f, anchor="nw")

        def fit(event=None):
            f.update_idletasks()
            w, h = max(c.winfo_width(), 50), f.winfo_reqheight()
            if (w, h) == getattr(c, "_size", None):
                return
            c._size = (w, h)
            c.config(height=h)
            c.itemconfigure(win, width=w, height=h)
            c.delete("bg")
            c.create_image(0, 0, anchor="nw", image=aa_image(w, h, radius, fill, None, CARD), tags="bg")
            c.tag_lower("bg")
        c.bind("<Configure>", fit)
        f.bind("<Configure>", fit)
        return f

    # ---- detail page ---------------------------------------------------------------------------
    def fmt_stamp(self, iso):
        try:
            d = datetime.fromisoformat(iso)
        except (TypeError, ValueError):
            return ""
        return f"{d.day} {MONTHS_SHORT[d.month - 1]} {d.hour:02d}:{d.minute:02d}"

    def meta_text(self):
        st = self.page_state
        parts = []
        if st.get("created"):
            parts.append("Oluşturuldu " + self.fmt_stamp(st["created"]))
        if st.get("updated") and st["updated"] != st.get("created"):
            parts.append("Düzenlendi " + self.fmt_stamp(st["updated"]))
        return "  ·  ".join(parts)

    def open_page(self, task_id, focus_title=False):
        if self.page_id is not None:
            self.flush_save()
        task = next((t for t in service.list_all(self.path) if t.id == task_id), None)
        if task is None:
            return
        self.close_menu()
        if self.search_entry.winfo_ismapped():
            self.search_entry.pack_forget()
        self.page_id = task_id
        base = date.fromisoformat(task.due) if task.due else date.today()
        self.page_state = {
            "title": task.title, "note": task.note, "priority": task.priority, "due": task.due,
            "repeat": task.repeat, "tags": list(task.tags), "subtasks": [dict(s) for s in task.subtasks],
            "pinned": task.pinned, "done": task.done, "created": task.created, "updated": task.updated,
            "cal_open": False, "cal_month": (base.year, base.month)}
        self.list_view.pack_forget()
        self.title.pack_forget()
        self.search_btn.pack_forget()
        self.menu_btn.pack_forget()
        self.back_btn.pack(side="left")
        self.page_outer = tk.Frame(self.inner, bg=CARD)
        self.page_outer.pack(fill="both", expand=True)
        self.page_canvas = tk.Canvas(self.page_outer, bg=CARD, highlightthickness=0, bd=0)
        self.page_canvas.pack(fill="both", expand=True)
        self.page_body = tk.Frame(self.page_canvas, bg=CARD)
        win = self.page_canvas.create_window((0, 0), window=self.page_body, anchor="nw")
        self.page_body.bind("<Configure>", lambda e: self.page_canvas.configure(
            scrollregion=self.page_canvas.bbox("all")))
        self.page_canvas.bind("<Configure>", lambda e: self.page_canvas.itemconfigure(win, width=e.width))
        self.fill_page()
        if focus_title:
            self.page_title.focus_set()
            self.page_title.tag_add("sel", "1.0", "end-1c")

    def close_page(self):
        if self.page_id is None:
            return
        self.flush_save()
        self.page_id = None
        self.page_outer.destroy()
        self.close_page_chrome()
        self.refresh()

    def fill_page(self, focus=None):
        """(Re)build the page from self.page_state, keeping the scroll position."""
        st = self.page_state
        body = self.page_body
        scroll = self.page_canvas.yview()[0]
        for w in body.winfo_children():
            w.destroy()
        self._page_widgets = {}

        # --- title row
        top = tk.Frame(body, bg=CARD)
        top.pack(fill="x", pady=(4, 0))
        ring = tk.Canvas(top, width=30, height=30, bg=CARD, highlightthickness=0, bd=0, cursor="hand2")
        if st["done"]:
            ring.create_image(0, 0, anchor="nw", image=aa_image(30, 30, 15, GREEN, None, CARD))
            ring.create_text(15, 15, text="✓", fill="#06150C", font=(FONT_SEMI, 11))
        else:
            ring.create_image(0, 0, anchor="nw", image=aa_image(
                30, 30, 15, CARD, PRIORITY_COLORS[st["priority"]], CARD, 2.6))
        ring.bind("<Button-1>", lambda e: self.page_toggle_done())
        ring.pack(side="left")
        title = tk.Text(top, bg=CARD, fg=MUTED if st["done"] else FG, font=(FONT_SEMI, 16), relief="flat",
                        insertbackground=FG, highlightthickness=0, bd=0, wrap="word", height=1, padx=0, pady=2)
        title.insert("1.0", st["title"])
        title.pack(side="left", fill="x", expand=True, padx=(12, 0))
        self.fit_title(title)
        title.bind("<KeyRelease>", lambda e: (self.fit_title(title), self.page_text_changed()))
        title.bind("<Return>", lambda e: (self._page_widgets["note"].focus_set(), "break")[1])
        title.bind("<Escape>", lambda e: self.close_page())
        self.page_title = self._page_widgets["title"] = title
        line = tk.Frame(body, bg=BORDER, height=1)
        line.pack(fill="x", pady=(6, 0))
        title.bind("<FocusIn>", lambda e: line.config(bg=GREEN))
        title.bind("<FocusOut>", lambda e: line.config(bg=BORDER))
        meta = tk.Frame(body, bg=CARD)
        meta.pack(fill="x", pady=(6, 12))
        self.page_meta = tk.Label(meta, text=self.meta_text(), bg=CARD, fg=MUTED, font=(FONT, 8))
        self.page_meta.pack(side="left")
        self.page_status = tk.Label(meta, text="", bg=CARD, fg=GREEN, font=(FONT, 8))
        self.page_status.pack(side="right")

        # --- properties
        props = self.soft_panel(body)
        pad = dict(padx=14)

        def prop(label, pady=(12, 0)):
            row = tk.Frame(props, bg=ROW)
            row.pack(fill="x", pady=pady, **pad)
            tk.Label(row, text=label, bg=ROW, fg=MUTED, font=(FONT_SEMI, 7), anchor="w").pack(fill="x", pady=(0, 5))
            box = tk.Frame(row, bg=ROW)
            box.pack(fill="x")
            return box

        box = prop("ÖNCELİK")
        for key, label in (("low", "Düşük"), ("medium", "Orta"), ("high", "Yüksek")):
            self.pill(box, label, lambda k=key: self.page_set(priority=k), active=st["priority"] == key,
                      color=PRIORITY_COLORS[key]).pack(side="left", padx=(0, 6))

        box = prop("TARİH")
        top_row = tk.Frame(box, bg=ROW)
        top_row.pack(fill="x")
        self.pill(top_row, "▦  " + self.due_label(st["due"]), self.toggle_calendar,
                  active=bool(st["due"])).pack(side="left", padx=(0, 6))
        if st["due"]:
            self.pill(top_row, "Kaldır", lambda: self.page_set(due=None, repeat=""),
                      fg="#FF7B7B").pack(side="left")
        quick = tk.Frame(box, bg=ROW)
        quick.pack(fill="x", pady=(6, 0))
        for label, text in (("Bugün", "bugun"), ("Yarın", "yarin"), ("Haftaya", "haftaya")):
            self.pill(quick, label, lambda t=text: self.page_set(
                due=due_from_text(t, date.today().isoformat()))).pack(side="left", padx=(0, 6))
        if st["cal_open"]:
            self.build_calendar(box)

        box = prop("TEKRAR")
        for key, label in (("", "Yok"), ("daily", "Günlük"), ("weekly", "Haftalık"),
                           ("monthly", "Aylık")):
            self.pill(box, label, lambda k=key: self.page_set(repeat=k), active=st["repeat"] == key).pack(
                side="left", padx=(0, 6))

        box = prop("ETEKİTLER".replace("ETEK","ETİK"), pady=(12, 14))
        self.build_tags(box)

        # --- calendar and mail: pick the provider right here, then use the button
        integ = self.soft_panel(body)
        tk.Label(integ, text="TAKVİM VE MAİL", bg=ROW, fg=MUTED, font=(FONT_SEMI, 7), anchor="w").pack(
            fill="x", padx=14, pady=(12, 0))
        for kind, key, providers, current, labels, action in (
                ("Takvim", "calendar", CALENDARS, self.calendar_provider, CALENDAR_BUTTON, self.page_to_calendar),
                ("Mail", "mail", MAILS, self.mail_provider, MAIL_BUTTON, self.page_mail)):
            tk.Label(integ, text=kind, bg=ROW, fg=FG, font=(FONT_SEMI, 9), anchor="w").pack(
                fill="x", padx=14, pady=(10, 4))
            choices = tk.Frame(integ, bg=ROW)
            choices.pack(fill="x", padx=14)
            for name in providers:
                self.pill(choices, SHORT_PROVIDER[name], lambda n=name, k=key: self.set_provider(k, n),
                          active=name == current).pack(side="left", padx=(0, 6))
            go = self.pill(integ, ("▦  " if key == "calendar" else "✉  ") + labels[current], action,
                           color=GREEN, fg=GREEN, bg=FIELD)
            go.pack(anchor="w", padx=14, pady=(8, 0))
        tk.Frame(integ, bg=ROW, height=14).pack()

        # --- note
        note_panel = self.soft_panel(body)
        tk.Label(note_panel, text="AÇIKLAMA", bg=ROW, fg=MUTED, font=(FONT_SEMI, 7), anchor="w").pack(
            fill="x", padx=14, pady=(12, 6))
        note = tk.Text(note_panel, height=7, wrap="word", bg=FIELD, fg=FG, relief="flat", font=(FONT, 10),
                       insertbackground=FG, highlightthickness=1, highlightbackground=BORDER,
                       highlightcolor=GREEN, padx=10, pady=8, undo=True)
        note.insert("1.0", st["note"])
        note.pack(fill="x", padx=14, pady=(0, 14))
        note.bind("<KeyRelease>", lambda e: self.page_text_changed())
        note.bind("<Escape>", lambda e: self.close_page())
        self._page_widgets["note"] = note

        # --- subtasks
        sub = self.soft_panel(body)
        header = tk.Frame(sub, bg=ROW)
        header.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(header, text="ALT GÖREVLER", bg=ROW, fg=MUTED, font=(FONT_SEMI, 7)).pack(side="left")
        total = len(st["subtasks"])
        finished = sum(1 for s in st["subtasks"] if s["done"])
        if total:
            tk.Label(header, text=f"{finished} / {total}", bg=ROW, fg=GREEN, font=(FONT_SEMI, 8)).pack(side="right")
            bar = tk.Canvas(sub, height=4, bg=ROW, highlightthickness=0, bd=0)
            bar.pack(fill="x", padx=14, pady=(0, 8))
            bar.bind("<Configure>", lambda e, b=bar: self.draw_mini_bar(b, finished, total))
        for i, item in enumerate(st["subtasks"]):
            self.build_subtask(sub, i, item)
        add = tk.Entry(sub, bg=ROW, fg=MUTED, relief="flat", font=(FONT, 10), insertbackground=FG,
                       highlightthickness=0, bd=0)
        add.insert(0, "+  Alt görev ekle")
        add.pack(fill="x", padx=14, pady=(2, 14), ipady=4)
        add.bind("<FocusIn>", lambda e: self.placeholder_focus(add, "+  "))
        add.bind("<FocusOut>", lambda e: self.placeholder_blur(add, "+  Alt görev ekle"))
        add.bind("<Return>", lambda e: self.page_add_subtask(add.get()))
        add.bind("<Escape>", lambda e: self.close_page())
        self._page_widgets["sub_add"] = add

        # --- actions
        actions = self.soft_panel(body, pady=(0, 16))
        row = tk.Frame(actions, bg=ROW)
        row.pack(fill="x", padx=14, pady=14)
        self.pill(row, "Sabiti kaldır" if st["pinned"] else "★  Sabitle",
                  lambda: self.page_set(pinned=not st["pinned"]), active=st["pinned"],
                  color="#FFC857").pack(side="left", padx=(0, 6))
        self.pill(row, "Kopyala", self.page_copy).pack(side="left", padx=(0, 6))
        self.pill(row, "Çoğalt", self.page_duplicate).pack(side="left", padx=(0, 6))
        self.pill(row, "Sil", self.page_delete, fg="#FF7B7B").pack(side="right")
        self.page_body.update_idletasks()
        self.page_canvas.yview_moveto(scroll)
        if focus and focus in self._page_widgets:
            self._page_widgets[focus].focus_set()

    def fit_title(self, widget):
        """Grow the wrapping title box to its text (1 to 4 lines)."""
        text = widget.get("1.0", "end-1c")
        widget.config(height=max(1, min(4, -(-len(text) // max(10, (self.cw - 2 * CARD_PAD - 60) // 12)))))

    def draw_mini_bar(self, bar, finished, total):
        bar.delete("all")
        w = max(bar.winfo_width(), 10)
        bar.create_image(0, 0, anchor="nw", image=aa_image(w, 4, 2, TRACK, None, ROW))
        if finished:
            bar.create_image(0, 0, anchor="nw", image=aa_image(max(6, round(w * finished / total)), 4, 2,
                                                              GREEN, None, ROW))

    def due_label(self, due):
        if not due:
            return "Tarih seç"
        chip = due_chip(due, date.today().isoformat())
        d = date.fromisoformat(due)
        return f"{chip[0]}  ·  {d.day} {MONTHS_SHORT[d.month - 1]}"

    def build_calendar(self, parent):
        st = self.page_state
        year, month = st["cal_month"]
        cal = tk.Frame(parent, bg=ROW)
        cal.pack(fill="x", pady=(10, 2))
        nav = tk.Frame(cal, bg=ROW)
        nav.pack(fill="x")
        self.button(nav, "‹", lambda: self.cal_shift(-1), size=14).pack(side="left", padx=6)
        self.button(nav, "›", lambda: self.cal_shift(1), size=14).pack(side="right", padx=6)
        tk.Label(nav, text=f"{MONTHS[month - 1]} {year}", bg=ROW, fg=FG, font=(FONT_SEMI, 10)).pack()
        grid = tk.Frame(cal, bg=ROW)
        grid.pack(fill="x", pady=(6, 0))
        for c in range(7):
            grid.columnconfigure(c, weight=1, uniform="day")
            tk.Label(grid, text=WEEKDAYS_SHORT[c], bg=ROW, fg=MUTED, font=(FONT, 8)).grid(row=0, column=c, pady=2)
        today = date.today()
        for r, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for c, day in enumerate(week):
                if not day:
                    continue
                iso = date(year, month, day).isoformat()
                selected = iso == st["due"]
                is_today = iso == today.isoformat()
                cell = tk.Label(grid, text=str(day), bg=GREEN if selected else (FIELD if is_today else ROW),
                                fg="#06150C" if selected else (GREEN if is_today else FG),
                                font=(FONT_SEMI if selected or is_today else FONT, 9), pady=4, cursor="hand2")
                cell.grid(row=r, column=c, sticky="ew", padx=1, pady=1)
                cell.bind("<Button-1>", lambda e, v=iso: self.page_set(due=v, cal_open=False))

    def cal_shift(self, delta):
        year, month = self.page_state["cal_month"]
        month += delta
        if month < 1:
            year, month = year - 1, 12
        elif month > 12:
            year, month = year + 1, 1
        self.page_state["cal_month"] = (year, month)
        self.fill_page()

    def toggle_calendar(self):
        self.sync_page_text()
        self.page_state["cal_open"] = not self.page_state["cal_open"]
        self.fill_page()

    def build_tags(self, box):
        st = self.page_state
        chips = [(tag, True) for tag in st["tags"]]
        known = sorted({t for task in self.tasks for t in task.tags} - set(st["tags"]))
        chips += [(tag, False) for tag in known[:6]]
        limit = max(120, self.cw - 2 * CARD_PAD - 28 - 110)
        row, used = None, 0
        for tag, mine in chips:
            width = len(tag) * 7 + (46 if mine else 28)
            if row is None or used + width > limit:
                row = tk.Frame(box, bg=ROW)
                row.pack(fill="x", pady=(0, 4))
                used = 0
            used += width + 6
            if mine:
                chip = tk.Frame(row, bg=TAG_CHIP[0])
                tk.Label(chip, text="#" + tag, bg=TAG_CHIP[0], fg=TAG_CHIP[1], font=(FONT, 8),
                         padx=8, pady=2).pack(side="left")
                x = tk.Label(chip, text="✕", bg=TAG_CHIP[0], fg=TAG_CHIP[1], font=(FONT, 7),
                             padx=5, cursor="hand2")
                x.pack(side="left")
                x.bind("<Button-1>", lambda e, t=tag: self.page_set(tags=[v for v in st["tags"] if v != t]))
            else:
                chip = tk.Label(row, text="+ #" + tag, bg=FIELD, fg=MUTED, font=(FONT, 8), padx=8, pady=2,
                                cursor="hand2")
                chip.bind("<Button-1>", lambda e, t=tag: self.page_set(tags=st["tags"] + [t]))
            chip.pack(side="left", padx=(0, 6))
        entry = tk.Entry(box, bg=FIELD, fg=MUTED, relief="flat", font=(FONT, 9), insertbackground=FG,
                         highlightthickness=1, highlightbackground=BORDER, highlightcolor=GREEN, width=16)
        entry.insert(0, "+ etiket ekle")
        entry.pack(anchor="w", ipady=3)
        entry.bind("<FocusIn>", lambda e: self.placeholder_focus(entry, "+ "))
        entry.bind("<FocusOut>", lambda e: self.placeholder_blur(entry, "+ etiket ekle"))
        entry.bind("<Return>", lambda e: self.page_add_tags(entry.get()))
        entry.bind("<Escape>", lambda e: self.close_page())
        self._page_widgets["tag_add"] = entry

    def build_subtask(self, parent, index, item):
        row = tk.Frame(parent, bg=ROW)
        row.pack(fill="x", padx=14, pady=1)
        mark = tk.Canvas(row, width=20, height=20, bg=ROW, highlightthickness=0, bd=0, cursor="hand2")
        if item["done"]:
            mark.create_image(0, 0, anchor="nw", image=aa_image(20, 20, 10, GREEN, None, ROW))
            mark.create_text(10, 10, text="✓", fill="#06150C", font=(FONT_SEMI, 8))
        else:
            mark.create_image(0, 0, anchor="nw", image=aa_image(20, 20, 10, ROW, MUTED, ROW, 1.8))
        mark.bind("<Button-1>", lambda e, i=index: self.page_toggle_subtask(i))
        mark.pack(side="left")
        entry = tk.Entry(row, bg=ROW, fg=MUTED if item["done"] else FG, relief="flat",
                         font=(FONT, 10, "overstrike") if item["done"] else (FONT, 10),
                         insertbackground=FG, highlightthickness=0, bd=0)
        entry.insert(0, item["text"])
        entry.pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=4)
        entry.bind("<KeyRelease>", lambda e, i=index, w=entry: self.page_subtask_text(i, w.get()))
        entry.bind("<Return>", lambda e: self._page_widgets["sub_add"].focus_set())
        entry.bind("<Escape>", lambda e: self.close_page())
        self.button(row, "✕", lambda i=index: self.page_remove_subtask(i), size=8).pack(side="right", padx=4)

    # ---- page state changes ----------------------------------------------------------------------
    def placeholder_focus(self, entry, prefix):
        if entry.get().startswith(prefix):
            entry.delete(0, "end")
            entry.config(fg=FG)

    def placeholder_blur(self, entry, text):
        if not entry.get().strip():
            entry.delete(0, "end")
            entry.insert(0, text)
            entry.config(fg=MUTED)

    def sync_page_text(self):
        w = self._page_widgets
        if "title" in w:
            self.page_state["title"] = w["title"].get("1.0", "end-1c").replace("\n", " ")
            self.page_state["note"] = w["note"].get("1.0", "end").strip()

    def page_text_changed(self):
        self.sync_page_text()
        self.schedule_save()

    def page_set(self, **kw):
        self.sync_page_text()
        st = self.page_state
        st.update(kw)
        if kw.get("repeat") and not st["due"]:
            st["due"] = date.today().isoformat()
        if "due" in kw and kw["due"]:
            y, m = map(int, kw["due"].split("-")[:2])
            st["cal_month"] = (y, m)
        if kw.get("cal_open") is None and "due" in kw:
            st["cal_open"] = False
        self.schedule_save()
        self.fill_page()

    def page_add_tags(self, text):
        if text.startswith("+ "):
            return
        tags = self.page_state["tags"]
        new = [t for t in parse_tags(text) if t not in tags]
        self.page_set(tags=tags + new)
        self._page_widgets["tag_add"].focus_set()

    def page_add_subtask(self, text):
        text = text.strip()
        if not text or text.startswith("+  "):
            return
        self.sync_page_text()
        self.page_state["subtasks"].append({"text": text, "done": False})
        self.schedule_save()
        self.fill_page(focus="sub_add")

    def page_toggle_subtask(self, index):
        self.sync_page_text()
        item = self.page_state["subtasks"][index]
        item["done"] = not item["done"]
        self.schedule_save()
        self.fill_page()

    def page_subtask_text(self, index, text):
        self.page_state["subtasks"][index]["text"] = text
        self.schedule_save()

    def page_remove_subtask(self, index):
        self.sync_page_text()
        del self.page_state["subtasks"][index]
        self.schedule_save()
        self.fill_page()

    def page_toggle_done(self):
        self.sync_page_text()
        self.flush_save()
        task = service.set_done(self.path, self.page_id, not self.page_state["done"])
        st = self.page_state
        st.update(done=task.done, due=task.due, subtasks=[dict(s) for s in task.subtasks],
                  updated=task.updated)
        self.fill_page()
        if task.repeat and not task.done and task.due:
            self.page_status.config(text=f"Sonraki: {self.due_label(task.due)}")

    def page_copy(self):
        self.sync_page_text()
        st = self.page_state
        lines = [st["title"], ""] if st["note"] else [st["title"]]
        if st["note"]:
            lines += [st["note"]]
        lines += [("[x] " if s["done"] else "[ ] ") + s["text"] for s in st["subtasks"]]
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(lines))
        self.page_status.config(text="Kopyalandı ✓")

    def page_duplicate(self):
        self.flush_save()
        copy = service.duplicate(self.path, self.page_id)
        self.page_id = None
        self.page_outer.destroy()
        self.open_page(copy.id, focus_title=True)

    def open_external(self, target):
        """Hand a file or mailto: link to the default app."""
        try:
            os.startfile(target)
        except (AttributeError, OSError):
            webbrowser.open(target)

    def current_page_task(self):
        self.sync_page_text()
        self.flush_save()
        return next((t for t in service.list_all(self.path) if t.id == self.page_id), None)

    def page_to_calendar(self):
        task = self.current_page_task()
        if task is None:
            return
        if not task.due or task.done:
            self.page_status.config(text="Takvim için tarihli, bekleyen görev gerekir", fg="#FF7B7B")
            return
        link = calendar_link(task, self.calendar_provider)
        if link:
            webbrowser.open(link)
            self.page_status.config(text=CALENDARS[self.calendar_provider] + " tarayıcıda açılıyor...",
                                    fg=GREEN)
            return
        path = os.path.join(tempfile.gettempdir(), f"gorev-{task.id}.ics")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(tasks_to_ics([task]))
        self.open_external(path)
        self.page_status.config(text="Takvim uygulamasında açılıyor...", fg=GREEN)

    def page_mail(self):
        task = self.current_page_task()
        if task is None:
            return
        link = mail_link(task, self.mail_provider)
        if self.mail_provider == "default":
            self.open_external(link)
            self.page_status.config(text="Mail uygulamasında açılıyor...", fg=GREEN)
        else:
            webbrowser.open(link)
            self.page_status.config(text=MAILS[self.mail_provider] + " tarayıcıda açılıyor...", fg=GREEN)

    def set_provider(self, kind, value):
        if kind == "calendar":
            self.calendar_provider = value
        else:
            self.mail_provider = value
        self.save_ui()
        if self.page_id is not None:
            self.sync_page_text()
            self.fill_page()

    def export_all_ics(self):
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Takvim dosyasını kaydet", defaultextension=".ics",
            initialfile="yapilacaklar.ics", filetypes=[("Takvim dosyası", "*.ics")])
        if not path:
            return
        tasks = service.list_all(self.path)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(tasks_to_ics(tasks))
        count = sum(1 for t in tasks if t.due and not t.done)
        self.notify(f"{count} görev takvim dosyasına kaydedildi")

    def page_delete(self):
        task_id = self.page_id
        self.sync_page_text()
        deleted = next((t for t in service.list_all(self.path) if t.id == task_id), None)
        if self._save_job:
            self.root.after_cancel(self._save_job)
            self._save_job = None
        try:
            service.delete(self.path, task_id)
        except KeyError:
            pass
        self.page_id = None
        self.page_outer.destroy()
        self.close_page_chrome()
        self.refresh()
        if deleted:
            self.show_toast(deleted)

    def close_page_chrome(self):
        self.back_btn.pack_forget()
        self.title.pack(side="left")
        self.menu_btn.pack(side="right")
        self.search_btn.pack(side="right")
        self.list_view.pack(fill="both", expand=True)

    # ---- autosave ------------------------------------------------------------------------------------
    def collect_page(self):
        st = self.page_state
        changes = {"note": st["note"], "priority": st["priority"], "due": st["due"] or "", "tags": st["tags"],
                   "subtasks": st["subtasks"], "pinned": st["pinned"], "repeat": st["repeat"]}
        if st["title"].strip():
            changes["title"] = st["title"]
        return changes

    def schedule_save(self):
        if self._save_job:
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(500, self.flush_save)
        status = getattr(self, "page_status", None)
        if status is not None and status.winfo_exists():
            status.config(text="Kaydediliyor...", fg=MUTED)

    def flush_save(self):
        if self._save_job:
            self.root.after_cancel(self._save_job)
            self._save_job = None
        if self.page_id is None:
            return
        try:
            task = service.update(self.path, self.page_id, self.collect_page())
        except (ValueError, KeyError):
            return
        self.page_state["updated"] = task.updated
        status = getattr(self, "page_status", None)
        if status is not None and status.winfo_exists():
            status.config(text="Kaydedildi ✓", fg=GREEN)
            self.page_meta.config(text=self.meta_text())

    def on_toggle(self, task_id, done=False, canvas=None):
        before = next((t for t in self.tasks if t.id == task_id), None)

        def finish():
            task = service.set_done(self.path, task_id, not done)
            self.refresh()
            if done or before is None:
                return
            if task.done:
                self.show_undo(f"“{self.short(task.title)}” tamamlandı",
                               lambda: self.revert_task(before))
            else:   # a repeating task moved to its next date
                self.show_undo(f"“{self.short(task.title)}” → {nl_due_label(task.due, date.today())}",
                               lambda: self.revert_task(before))

        if canvas is not None and not done:
            bg = canvas.cget("bg")
            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=aa_image(24, 24, 12, GREEN, None, bg))
            canvas.create_text(12, 12, text="✓", fill="#06150C", font=(FONT_SEMI, 9))
            self.root.after(260, finish)
        else:
            finish()

    def revert_task(self, before):
        service.update(self.path, before.id, {"due": before.due or "", "subtasks": before.subtasks})
        service.set_done(self.path, before.id, before.done)

    def short(self, title):
        return title if len(title) < 24 else title[:22] + "…"

    def on_delete(self, task_id):
        deleted = next((t for t in self.tasks if t.id == task_id), None)
        try:
            service.delete(self.path, task_id)
        except KeyError:
            pass
        self.refresh()
        if deleted:
            self.show_toast(deleted)

    def notify(self, text):
        """A short message in the toast (no undo link)."""
        self._undo_cb = None
        self.toast_undo.pack_forget()
        self.toast_label.config(text=text)
        self.toast.place(relx=0.5, rely=1.0, anchor="s", y=-4)
        tk.Misc.lift(self.toast)
        if self._undo_job:
            self.root.after_cancel(self._undo_job)
        self._undo_job = self.root.after(3500, self.hide_toast)

    def show_undo(self, text, callback):
        """Toast with an undo link that runs `callback`."""
        self._undo_cb = callback
        self.toast_undo.pack(side="left")
        self.toast_label.config(text=text)
        self.toast.place(relx=0.5, rely=1.0, anchor="s", y=-4)
        tk.Misc.lift(self.toast)
        if self._undo_job:
            self.root.after_cancel(self._undo_job)
        self._undo_job = self.root.after(5000, self.hide_toast)

    def show_toast(self, task):
        self.show_undo(f"“{self.short(task.title)}” silindi", lambda: service.restore(self.path, task))

    def hide_toast(self):
        self._undo_cb = None
        self._undo_job = None
        self.toast.place_forget()

    def run_undo(self):
        callback = self._undo_cb
        self.hide_toast()
        if callback:
            callback()
        self.refresh()

    undo_delete = run_undo

    # ---- quick add from anywhere -------------------------------------------------------------
    def apply_hotkey(self, name=None):
        """(Re)register the quick-add shortcut; tell the user when another program already uses it."""
        if name is not None:
            self.hotkey_name = name
            self.save_ui()
        if self.hotkey is not None:
            self.hotkey.stop()
        self.hotkey = GlobalHotkey(self.hotkey_name)
        if self.hotkey_name != "off" and not self.hotkey.start():
            self.notify(f"{self.hotkey.label} başka bir uygulamada kullanılıyor: ⋯ menüden değiştir")
        elif name is not None:
            self.notify("Her yerden ekleme: " + self.hotkey.label if self.hotkey_name != "off"
                        else "Her yerden ekleme kapatıldı")
        if not getattr(self, "_polling", False):
            self._polling = True
            self.poll_hotkey()

    def poll_hotkey(self):
        if self.hotkey is not None and self.hotkey.pressed():
            self.quick_add_anywhere()
        self.root.after(150, self.poll_hotkey)

    def quick_add_anywhere(self):
        if self.page_id is not None:
            self.close_page()
        if not self.is_open:
            self.show_card(animate=False)
        self.root.lift()
        self.root.focus_force()
        self.on_entry_focus()
        self.entry.focus_force()

    # ---- search / shortcuts ---------------------------------------------------------------
    def toggle_search(self, force_open=False):
        if self.page_id is not None:
            self.close_page()
        if self.search_entry.winfo_ismapped() and not force_open:
            self.search_entry.pack_forget()
            self.search_var.set("")
            self.on_search()
            return
        if not self.is_open:
            self.show_card(animate=False)
        if not self.search_entry.winfo_ismapped():
            self.search_entry.pack(fill="x", ipady=7, pady=(0, 12), before=self.entry)
        self.search_entry.focus_set()

    def on_search(self, event=None):
        query = self.search_var.get()
        if query != self.query:
            self.query = query
            self.refresh()

    def focus_entry(self):
        if self.page_id is not None:
            self.close_page()
        if not self.is_open:
            self.show_card(animate=False)
        self.entry.focus_force()

    # ---- menu ---------------------------------------------------------------------------------
    def close_menu(self):
        if self._menu is not None:
            try:
                self._menu.destroy()
            except tk.TclError:
                pass
            self._menu = None

    def open_menu(self, anchor):
        if self._menu is not None:
            self.close_menu()
            return
        menu = tk.Toplevel(self.root)
        menu.overrideredirect(True)
        menu.attributes("-topmost", True)
        menu.configure(bg=BORDER)
        holder = tk.Canvas(menu, bg=CARD, highlightthickness=0, bd=0)
        holder.pack(padx=1, pady=1)
        box = tk.Frame(holder, bg=CARD)
        holder.create_window(0, 0, window=box, anchor="nw")
        self._menu = menu

        def section(text):
            tk.Label(box, text=text, bg=CARD, fg=MUTED, font=(FONT_SEMI, 7), anchor="w").pack(
                fill="x", padx=18, pady=(16, 6))

        def pills(options, current, command):
            row = tk.Frame(box, bg=CARD)
            row.pack(fill="x", padx=16)
            for key, label in options:
                on = key == current
                lbl = tk.Label(row, text=label, bg=GREEN if on else FIELD, fg="#06150C" if on else FG,
                               font=(FONT_SEMI, 9), padx=12, pady=6, cursor="hand2")
                lbl.pack(side="left", padx=2)
                lbl.bind("<Button-1>", lambda e, k=key: (self.close_menu(), command(k)))

        tk.Label(box, text="Görünüm", bg=CARD, fg=FG, font=(FONT_SEMI, 13)).pack(
            anchor="w", padx=18, pady=(16, 0))
        section("YERLEŞİM")
        pills((("left", "Sol"), ("top", "Üst"), ("bottom", "Alt"), ("right", "Sağ")),
              self.side, lambda s: self.redock(s, keep_pos=False))
        section("BOYUT")
        current = next((k for k, v in SIZES.items() if v == (self.cw, self.ch)), None)
        pills((("S", "Küçük"), ("M", "Orta"), ("L", "Büyük")), current,
              lambda k: self.set_size(*SIZES[k]))
        tk.Label(box, text="Kartın köşesindeki noktalardan tutup da boylandırabilirsin",
                 bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w", padx=18, pady=(6, 0))
        section("SEKME BOYUTU")
        scale = self.pill_scale
        pills(((0.8, "K\u00fc\u00e7\u00fck"), (1.0, "Orta"), (1.25, "B\u00fcy\u00fck")),
              next((v for v in (0.8, 1.0, 1.25) if abs(v - scale) < 0.03), None), self.set_pill_scale)
        tk.Label(box, text="Sekmeyi ucundaki noktalardan tutup ya da \u00fczerinde tekerle\u011fi \u00e7evirerek de ayarlayabilirsin",
                 bg=CARD, fg=MUTED, font=(FONT, 8), wraplength=300, justify="left").pack(anchor="w", padx=18, pady=(6, 0))
        section("SAYDAMLIK")
        pills(((1.0, "%100"), (0.9, "%90"), (0.75, "%75")), self.alpha, self.set_alpha)
        section("BAŞLANGIÇ")
        from todo import autostart
        if autostart.is_packaged():     # Store install: Windows owns the startup switch
            tk.Label(box, text="Ayarlar \u2192 Uygulamalar \u2192 Ba\u015flang\u0131\u00e7 b\u00f6l\u00fcm\u00fcnden a\u00e7abilirsin",
                     bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=18)
        else:
            pills(((True, "Windows ile ba\u015flat"), (False, "Elle a\u00e7")), autostart.is_enabled(),
                  self.set_autostart)
        section("TAKVİM")
        pills(tuple(CALENDARS.items()), self.calendar_provider, lambda k: self.set_provider("calendar", k))
        section("MAİL")
        pills(tuple(MAILS.items()), self.mail_provider, lambda k: self.set_provider("mail", k))
        tk.Label(box, text="Google ve Outlook tarayıcıda, kendi hesabında önceden doldurulmuş açılır; onayın olmadan bir şey eklenmez ya da gönderilmez",
                 bg=CARD, fg=MUTED, font=(FONT, 8), wraplength=300, justify="left").pack(anchor="w", padx=18, pady=(6, 0))
        pills((("ics", "Tüm görevleri takvim dosyası (.ics) yap"),), None,
              lambda k: self.root.after(50, self.export_all_ics))
        section("HER YERDEN EKLE")
        pills(tuple((k, v[2]) for k, v in HOTKEYS.items()), self.hotkey_name, self.apply_hotkey)
        section("KISAYOLLAR")
        for line in ("Ctrl+N   yeni g\u00f6rev", "Ctrl+F   ara", "Esc        kapat / daralt",
                     "Çift tık   başlığı düzenle"):
            tk.Label(box, text=line, bg=CARD, fg=MUTED, font=("Consolas", 9), anchor="w").pack(
                fill="x", padx=18)
        tk.Label(box, text="Yapay zekâ için MCP: python -m todo.mcp_server", bg=CARD, fg=MUTED,
                 font=(FONT, 8)).pack(anchor="w", padx=18, pady=(14, 16))

        box.update_idletasks()
        bw, bh = box.winfo_reqwidth(), box.winfo_reqheight()
        sw, sh = self.screen()
        visible = min(bh, sh - TASKBAR - 40)
        holder.configure(width=bw, height=visible, scrollregion=(0, 0, bw, bh))
        if bh > visible:   # small screen: let the menu scroll
            menu.bind("<MouseWheel>", lambda e: holder.yview_scroll(-1 if e.delta > 0 else 1, "units"))
        mw, mh = bw + 2, visible + 2
        x = anchor.winfo_rootx() + anchor.winfo_width() - mw
        y = anchor.winfo_rooty() + anchor.winfo_height() + 8
        menu.geometry(f"+{max(8, min(x, sw - mw - 8))}+{max(8, min(y, sh - mh - TASKBAR))}")
        menu.focus_force()
        menu.bind("<Escape>", lambda e: self.close_menu())
        menu.bind("<FocusOut>", lambda e: self.root.after(120, self.menu_focus_check))

    def menu_focus_check(self):
        if self._menu is not None and self._menu.focus_displayof() is None:
            self.close_menu()

    def set_alpha(self, value):
        self.alpha = value
        self.root.attributes("-alpha", value)
        self.save_ui()

    def set_autostart(self, on):
        from todo import autostart
        autostart.set_enabled(bool(on))

    def watch(self):
        current_mtime = os.path.getmtime(self.path) if os.path.exists(self.path) else 0
        if current_mtime != getattr(self, "_last_mtime", None):
            if getattr(self, "_last_mtime", None) is not None and self.page_id is None:
                self.refresh()
            self._last_mtime = current_mtime
        self.root.after(1500, self.watch)


def enable_dpi_awareness():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def main():
    from todo.single import acquire
    if not acquire():       # already running: leave the existing widget alone
        return
    from todo.welcome import seed_welcome
    seed_welcome(DATA_PATH)
    enable_dpi_awareness()
    root = tk.Tk()
    app = StickyApp(root)
    app.apply_hotkey()
    root.mainloop()


if __name__ == "__main__":
    main()
