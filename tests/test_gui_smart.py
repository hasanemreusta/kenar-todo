import os
import tempfile
import tkinter as tk
import unittest
from datetime import date, timedelta

from todo import service
from todo.gui import StickyApp
from todo.welcome import seed_welcome


def rows(app):
    return [w for w in app.list_frame.winfo_children() if isinstance(w, tk.Canvas)]


class SmartFeaturesTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.td.name, "tasks.json")
        self.root = tk.Tk()

    def tearDown(self):
        self.root.destroy()
        self.td.cleanup()

    def app(self):
        app = StickyApp(self.root, self.path, ui_path=os.path.join(self.td.name, "ui.json"))
        self.root.update()
        return app

    def test_welcome_tasks_only_on_first_run(self):
        self.assertTrue(seed_welcome(self.path))
        self.assertEqual(len(service.list_all(self.path)), 5)
        self.assertFalse(seed_welcome(self.path))
        self.assertTrue(any(t.pinned for t in service.list_all(self.path)))

    def test_natural_quick_add_with_preview(self):
        app = self.app()
        app.on_entry_focus()
        app.entry.insert(0, "spor yarın her hafta !yüksek #sağlık")
        app.update_preview()
        self.root.update()
        self.assertTrue(app.preview.winfo_ismapped())
        self.assertGreaterEqual(len(app.preview.winfo_children()), 4)
        app.add_from_entry()
        task = service.list_all(self.path)[0]
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        self.assertEqual((task.title, task.due, task.repeat, task.priority, task.tags),
                         ("spor", tomorrow, "weekly", "high", ["sağlık"]))
        self.root.update()
        self.assertFalse(app.preview.winfo_ismapped())

    def test_smart_lists_and_counter_click(self):
        today = date.today().isoformat()
        service.create(self.path, "today", due=today)
        service.create(self.path, "urgent", priority="high")
        service.create(self.path, "later")
        app = self.app()
        self.assertEqual(len(rows(app)), 3)
        app.set_filter("today")
        self.assertEqual(len(rows(app)), 1)
        app.set_filter("important")
        self.assertEqual(len(rows(app)), 1)
        app.set_filter("all")
        app.toggle_collapse(animate=False)
        k = app.pill_scale
        x, y = 40, round(146 * k)             # the "Bugün" counter on the vertical pill
        app._press = (0, 0, 0, 0, False)
        app.tab_release(type("E", (), {"x": x, "y": y, "x_root": 0, "y_root": 0})())
        self.root.update()
        self.assertTrue(app.is_open)
        self.assertEqual(app.view_filter, "today")

    def test_complete_with_undo(self):
        service.create(self.path, "A")
        app = self.app()
        app.on_toggle(1, False)
        self.assertTrue(service.list_all(self.path)[0].done)
        self.assertIsNotNone(app._undo_cb)
        app.run_undo()
        self.assertFalse(service.list_all(self.path)[0].done)

    def test_quick_add_anywhere_opens_and_focuses(self):
        app = self.app()
        app.toggle_collapse(animate=False)
        app.quick_add_anywhere()
        self.root.update()
        self.assertTrue(app.is_open)

    def test_hotkey_choice_is_saved_and_released(self):
        import json
        import sys
        import time
        from todo.hotkey import GlobalHotkey
        app = self.app()
        app.apply_hotkey("off")
        self.assertFalse(app.hotkey.registered.is_set())
        with open(os.path.join(self.td.name, "ui.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["hotkey"], "off")
        if sys.platform == "win32":
            first = GlobalHotkey("ctrl_shift_space")
            if first.start():                     # skip quietly if another program owns it
                self.assertFalse(GlobalHotkey("ctrl_shift_space").start())
                first.stop()
                time.sleep(0.2)
                again = GlobalHotkey("ctrl_shift_space")
                self.assertTrue(again.start())
                again.stop()

    def test_menu_content_is_visible_even_when_it_must_scroll(self):
        app = self.app()
        app.screen = lambda: (1366, 600)            # a short screen forces the scrolling path
        app.open_menu(app.menu_btn)
        self.root.update()
        holder = app._menu.winfo_children()[0]
        box = holder.winfo_children()[0]
        self.assertIsInstance(holder, tk.Canvas)
        self.assertIs(box.master, holder)           # content inside the canvas, not hidden behind it
        self.assertTrue(box.winfo_ismapped())
        self.assertLessEqual(app._menu.winfo_height(), 600)
        app.close_menu()

    def test_dragging_along_an_edge_keeps_the_new_position(self):
        E = type("E", (), {})

        def ev(xr, yr):
            e = E()
            e.x_root, e.y_root, e.x, e.y = xr, yr, 10, 10
            return e

        app = self.app()
        app.set_size(300, 400)
        for side, (dx, dy) in (("right", (0, 100)), ("left", (0, -90)), ("top", (220, 0)), ("bottom", (-160, 0))):
            app.redock(side, keep_pos=False)
            self.root.update()
            x0, y0 = self.root.winfo_x(), self.root.winfo_y()
            app.start_drag(ev(x0 + 20, y0 + 20))
            for step in range(1, 6):
                app.do_drag(ev(x0 + 20 + dx * step // 5, y0 + 20 + dy * step // 5))
            app.end_drag(ev(x0 + 20 + dx, y0 + 20 + dy))
            self.root.update()
            self.assertEqual(app.side, side)
            moved = (self.root.winfo_x() - x0) if side in ("top", "bottom") else (self.root.winfo_y() - y0)
            self.assertEqual(moved, dx if side in ("top", "bottom") else dy, side)


if __name__ == "__main__":
    unittest.main()
