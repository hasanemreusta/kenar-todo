import json
import os
import tempfile
import tkinter as tk
import unittest

from todo import service
from todo.gui import StickyApp


class GuiTest(unittest.TestCase):
    def test_rows_and_actions(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "tasks.json")
            service.create(path, "Süt al", priority="high")
            service.create(path, "Rapor yaz")
            root = tk.Tk()
            try:
                app = StickyApp(root, path, ui_path=os.path.join(td, "ui.json"))
                root.update()
                self.assertEqual(len([w for w in app.list_frame.winfo_children() if isinstance(w, tk.Canvas)]), 2)
                app.entry.insert(0, "Yeni görev")
                app.add_from_entry()
                self.assertEqual(len([w for w in app.list_frame.winfo_children() if isinstance(w, tk.Canvas)]), 3)
                app.on_toggle(1)
                self.assertTrue(service.list_all(path)[-1].done)
                app.on_delete(2)
                self.assertEqual(len([w for w in app.list_frame.winfo_children() if isinstance(w, tk.Canvas)]), 2)
                app.toggle_collapse(animate=False)
                self.assertTrue(app.collapsed)
                root.update()
                app.toggle_collapse(animate=False)
                self.assertFalse(app.collapsed)
                root.update()
            finally:
                root.destroy()

    def test_detail_page_autosave_undo_and_search(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "tasks.json")
            service.create(path, "Alpha")
            service.create(path, "Beta", tags=["work"])
            root = tk.Tk()
            try:
                app = StickyApp(root, path, ui_path=os.path.join(td, "ui.json"))
                root.update()
                app.open_page(1)
                root.update()
                self.assertEqual(app.page_id, 1)
                w = app._page_widgets
                w["title"].delete("1.0", "end")
                w["title"].insert("1.0", "Alpha 2")
                w["note"].insert("1.0", "remember this")
                app.page_text_changed()
                app.page_set(priority="high")
                app.page_set(due="2030-01-15")
                app.page_set(repeat="weekly")
                app.page_add_tags("home, urgent")
                app._page_widgets["sub_add"].insert(0, "buy milk")
                app.page_add_subtask("buy milk")
                app.page_toggle_subtask(0)
                app.page_set(pinned=True)
                app.flush_save()
                task = [t for t in service.list_all(path) if t.id == 1][0]
                self.assertEqual((task.title, task.note, task.priority, task.due, task.repeat),
                                 ("Alpha 2", "remember this", "high", "2030-01-15", "weekly"))
                self.assertEqual(task.tags, ["home", "urgent"])
                self.assertEqual(task.subtasks, [{"text": "buy milk", "done": True}])
                self.assertTrue(task.pinned)
                self.assertTrue(task.created and task.updated)
                app.cal_shift(1)
                app.toggle_calendar()
                root.update()
                app.back_btn.event_generate("<Button-1>", x=2, y=2)   # the real "Geri" click
                root.update()
                self.assertIsNone(app.page_id)
                self.assertIsNone(app.page_id)
                app.search_var.set("work")
                app.on_search()
                rows = [w for w in app.list_frame.winfo_children() if isinstance(w, tk.Canvas)]
                self.assertEqual(len(rows), 1)
                app.search_var.set("")
                app.on_search()
                app.on_delete(2)
                self.assertEqual(len(service.list_all(path)), 1)
                app.undo_delete()
                self.assertEqual(sorted(t.id for t in service.list_all(path)), [1, 2])
                app.open_page(1)
                app.page_duplicate()
                self.assertEqual(len(service.list_all(path)), 3)
                app.page_delete()
                self.assertEqual(len(service.list_all(path)), 2)
                app.on_toggle(2, False)
                app.on_toggle(2, True)
                self.assertFalse([t for t in service.list_all(path) if t.id == 2][0].done)
            finally:
                root.destroy()

    def test_docking_resize_and_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "tasks.json")
            ui = os.path.join(td, "ui.json")
            service.create(path, "Alpha")
            root = tk.Tk()
            try:
                app = StickyApp(root, path, ui_path=ui)
                root.update()
                sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
                for side in ("left", "top", "bottom", "right"):
                    app.redock(side, keep_pos=False)
                    root.update()
                    for widget in (app.tab, app.card):      # both fully inside the window (regression)
                        self.assertGreaterEqual(widget.winfo_x(), 0)
                        self.assertGreaterEqual(widget.winfo_y(), 0)
                        self.assertLessEqual(widget.winfo_x() + widget.winfo_width(), root.winfo_width())
                        self.assertLessEqual(widget.winfo_y() + widget.winfo_height(), root.winfo_height())
                    self.assertEqual(app.side, side)
                    self.assertEqual(app.horizontal, side in ("top", "bottom"))
                    self.assertGreaterEqual(root.winfo_x(), 0)
                    self.assertGreaterEqual(root.winfo_y(), 0)
                    self.assertLessEqual(root.winfo_x() + root.winfo_width(), sw)
                    self.assertLessEqual(root.winfo_y() + root.winfo_height(), sh)
                    app.toggle_collapse(animate=False)
                    root.update()
                    self.assertEqual((root.winfo_width(), root.winfo_height()), app.pill_size())
                    app.toggle_collapse(animate=False)
                app.toggle_collapse(animate=False)
                for scale in (0.7, 1.25, 5.0):
                    app.set_pill_scale(scale)
                    root.update()
                    self.assertEqual((root.winfo_width(), root.winfo_height()), app.pill_size())
                    self.assertLessEqual(max(app.pill_size()), max(sw, sh))
                self.assertLessEqual(app.pill_scale, 1.6)
                app.set_pill_scale(0.8)
                app.toggle_collapse(animate=False)
                app.set_size(300, 520)
                self.assertEqual((app.cw, app.ch), (300, 520))
                app.set_alpha(0.9)
                with open(ui, encoding="utf-8") as f:
                    saved = json.load(f)
                self.assertEqual((saved["side"], saved["cw"], saved["ch"], saved["alpha"]),
                                 ("right", 300, 520, 0.9))
                self.assertEqual(saved["pill"], 0.8)
            finally:
                root.destroy()

    def test_calendar_and_mail_actions(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "tasks.json")
            service.create(path, "Rapor", due="2030-05-06", tags=["is"])
            service.create(path, "No date")
            root = tk.Tk()
            try:
                app = StickyApp(root, path, ui_path=os.path.join(td, "ui.json"))
                opened = []
                app.open_external = opened.append
                app.open_page(1)
                app.page_to_calendar()
                app.page_mail()
                self.assertTrue(opened[0].endswith(".ics"))
                with open(opened[0], encoding="utf-8") as f:
                    text = f.read()
                self.assertIn("BEGIN:VEVENT", text)
                self.assertIn("SUMMARY:Rapor", text)
                self.assertTrue(opened[1].startswith("mailto:?subject=Rapor"))
                app.close_page()
                app.open_page(2)
                app.page_to_calendar()          # no due date: nothing is opened
                self.assertEqual(len(opened), 2)
                app.close_page()
                from unittest import mock
                app.set_provider("calendar", "google")
                app.set_provider("mail", "gmail")
                app.open_page(1)
                with mock.patch("todo.gui.webbrowser.open") as web:
                    app.page_to_calendar()
                    app.page_mail()
                self.assertTrue(web.call_args_list[0].args[0].startswith("https://calendar.google.com/calendar/render?"))
                self.assertTrue(web.call_args_list[1].args[0].startswith("https://mail.google.com/mail/?"))
                self.assertEqual(len(opened), 2)          # the default apps were not used
                app.close_page()
                with open(os.path.join(td, "ui.json"), encoding="utf-8") as f:
                    saved = json.load(f)
                self.assertEqual((saved["calendar"], saved["mail"]), ("google", "gmail"))
                out = os.path.join(td, "all.ics")
                with mock.patch("todo.gui.filedialog.asksaveasfilename", return_value=out):
                    app.export_all_ics()
                with open(out, encoding="utf-8") as f:
                    self.assertEqual(f.read().count("BEGIN:VEVENT"), 1)
            finally:
                root.destroy()


if __name__ == "__main__":
    unittest.main()
