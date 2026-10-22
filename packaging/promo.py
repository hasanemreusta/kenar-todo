"""Render promo screenshots: the real widget with demo data, composed on a gradient with captions.

    python packaging/promo.py        -> packaging/promo/*.png   (needs Pillow; Windows, real screen)
"""
import json
import os
import sys
import tempfile
import tkinter as tk
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageGrab  # noqa: E402

from todo import service  # noqa: E402
from todo.gui import StickyApp, enable_dpi_awareness  # noqa: E402

OUT = os.path.join(ROOT, "packaging", "promo")
KEY = (255, 0, 255)
W, H = 1600, 1000
FONTS = "C:/Windows/Fonts/"


def save(image, name):
    """Save with a few retries: a just-written PNG can be briefly locked by a scanner or preview."""
    import time
    for attempt in range(5):
        try:
            image.convert("RGB").save(os.path.join(OUT, name), quality=95)
            return
        except OSError:
            time.sleep(0.5 * (attempt + 1))
    raise OSError("could not write " + name)


def font(name, size):
    return ImageFont.truetype(FONTS + name, size)


def demo_data(path):
    if os.path.exists(path):
        os.remove(path)
    t = date.today()
    d = lambda n: (t + timedelta(days=n)).isoformat()  # noqa: E731
    a = service.create(path, "Haftal\u0131k market al\u0131\u015fveri\u015fi", "medium", d(0), ["ev", "market"])
    service.update(path, a.id, {"pinned": True, "repeat": "weekly",
                                "note": "Ya\u011fs\u0131z s\u00fct, 2 litre.\nTaze ekmek ve mevsim meyveleri.",
                                "subtasks": [{"text": "S\u00fct", "done": True}, {"text": "Yumurta", "done": True},
                                             {"text": "Ekmek", "done": False}, {"text": "Domates", "done": False}]})
    service.create(path, "Sunum slaytlar\u0131n\u0131 bitir", "high", d(-1), ["i\u015f"])
    b = service.create(path, "M\u00fc\u015fteri g\u00f6r\u00fc\u015fmesi notlar\u0131", "high", d(0), ["i\u015f"])
    service.update(path, b.id, {"note": "Fiyat teklifini g\u00fcncelle, teslim tarihini netle\u015ftir."})
    service.create(path, "Spor salonu", "medium", d(1), ["sa\u011fl\u0131k"])
    c = service.create(path, "Kitap: Atomik Al\u0131\u015fkanl\u0131klar", "low", d(4), ["okuma"])
    service.update(path, c.id, {"subtasks": [{"text": "1-5. b\u00f6l\u00fcm", "done": True},
                                             {"text": "6-10. b\u00f6l\u00fcm", "done": False}]})
    service.create(path, "Di\u015f hekimi randevusu", "medium", d(12), ["sa\u011fl\u0131k"])
    done = service.create(path, "Faturalar\u0131 \u00f6de", "medium", d(-2), ["ev"])
    service.set_done(path, done.id, True)


class Shooter:
    def __init__(self):
        enable_dpi_awareness()
        self.td = tempfile.mkdtemp()
        self.data = os.path.join(self.td, "tasks.json")
        demo_data(self.data)
        self.root = tk.Tk()
        self.backdrop = tk.Toplevel(self.root)
        self.backdrop.overrideredirect(True)
        self.backdrop.configure(bg="#ff00ff")
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.backdrop.geometry(f"{sw}x{sh}+0+0")
        self.app = None

    def start(self, side="right", pos=60, cw=380, ch=720, pill=1.0, open_=True):
        ui = os.path.join(self.td, "ui.json")
        with open(ui, "w", encoding="utf-8") as f:
            json.dump({"side": side, "pos": pos, "cw": cw, "ch": ch, "pill": pill,
                       "calendar": "google", "mail": "gmail"}, f)
        for w in self.root.winfo_children():
            if w is not self.backdrop:
                w.destroy()
        self.app = StickyApp(self.root, self.data, ui_path=ui, start_open=open_)
        self.settle()

    def settle(self, ms=500):
        self.root.update()
        self.backdrop.attributes("-topmost", True)     # keep the keyed backdrop right under the widget
        self.backdrop.lift()
        self.root.lift()
        self.root.after(ms, self.root.quit)
        self.root.mainloop()

    def grab(self, widget=None):
        w = widget or self.root
        self.root.update()
        x, y, ww, hh = w.winfo_rootx(), w.winfo_rooty(), w.winfo_width(), w.winfo_height()
        img = ImageGrab.grab((x, y, x + ww, y + hh)).convert("RGBA")
        px = img.load()
        for j in range(img.height):
            for i in range(img.width):
                r, g, b, _ = px[i, j]
                if (r, g, b) == KEY or (r > 240 and g < 20 and b > 240):
                    px[i, j] = (0, 0, 0, 0)
        return img


def slide(name, shot, title, subtitle, extra=None):
    bg = Image.new("RGB", (W, H))
    top, bottom = (120, 170, 255), (30, 80, 210)
    draw = ImageDraw.Draw(bg)
    for yy in range(H):
        t = yy / H
        draw.line([(0, yy), (W, yy)], fill=tuple(round(top[k] + (bottom[k] - top[k]) * t) for k in range(3)))
    canvas = bg.convert("RGBA")
    scale = min(1.0, (H - 120) / shot.height)
    if scale < 1:
        shot = shot.resize((round(shot.width * scale), round(shot.height * scale)), Image.LANCZOS)
    x = W - shot.width - 140
    y = (H - shot.height) // 2
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    alpha = shot.split()[3].point(lambda v: 90 if v else 0)
    shadow.paste((10, 20, 60, 255), (x + 10, y + 24), alpha)
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(26)))
    canvas.alpha_composite(shot, (x, y))
    logo = Image.open(os.path.join(ROOT, "packaging", "logo.png")).resize((64, 64), Image.LANCZOS)
    canvas.alpha_composite(logo, (110, 96))
    d = ImageDraw.Draw(canvas)
    d.text((190, 108), "Yapılacaklar", font=font("segoeuib.ttf", 30), fill="white")
    d.text((110, 330), title, font=font("segoeuib.ttf", 64), fill="white")
    d.multiline_text((112, 430), subtitle, font=font("segoeui.ttf", 30), fill=(230, 238, 255), spacing=12)
    if extra:
        d.text((112, 640), extra, font=font("segoeui.ttf", 24), fill=(205, 220, 255))
    save(canvas, name)
    print("saved", name)


def cover():
    bg = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(bg)
    top, bottom = (120, 170, 255), (30, 80, 210)
    for yy in range(H):
        t = yy / H
        draw.line([(0, yy), (W, yy)], fill=tuple(round(top[k] + (bottom[k] - top[k]) * t) for k in range(3)))
    canvas = bg.convert("RGBA")
    logo = Image.open(os.path.join(ROOT, "packaging", "logo.png")).resize((360, 360), Image.LANCZOS)
    canvas.alpha_composite(logo, ((W - 360) // 2, 170))
    d = ImageDraw.Draw(canvas)
    for text, f, y, fill in (("Yapılacaklar", font("segoeuib.ttf", 76), 570, "white"),
                             ("Ekranın kenarında, her an elinin altında.", font("segoeui.ttf", 34), 680,
                              (230, 238, 255)),
                             ("Windows için ücretsiz · kurulum gerektirmez · yapay zekâ desteği (MCP)",
                              font("segoeui.ttf", 24), 750, (205, 220, 255))):
        width = d.textlength(text, font=f)
        d.text(((W - width) / 2, y), text, font=f, fill=fill)
    save(canvas, "0-kapak.png")
    print("saved 0-kapak.png")


def main():
    from todo import autostart
    autostart.is_enabled = lambda: False       # show the default state, not this machine's real setting
    os.makedirs(OUT, exist_ok=True)
    cover()
    s = Shooter()
    s.start()
    slide("1-liste.png", s.grab(), "Yap\u0131lacaklar",
          "Ekran\u0131n kenar\u0131nda duran \u015f\u0131k bir sekme.\nT\u0131kla, g\u00f6revlerin yan\u0131nda a\u00e7\u0131ls\u0131n.",
          "Sabitlenen, gecikmi\u015f, bug\u00fcn, yakla\u015fan: her \u015fey yerli yerinde")

    app = s.app
    app.on_entry_focus()
    app.entry.insert(0, "Rapor cuma !y\u00fcksek #i\u015f")
    app.update_preview()
    s.settle(300)
    slide("2-hizli-ekle.png", s.grab(), "Yaz, gerisini o anlas\u0131n",
          "\u201crapor cuma !y\u00fcksek #i\u015f\u201d, \u201cspor her g\u00fcn\u201d, \u201cdoktor 25 ekim\u201d\nTarih, tekrar, \u00f6ncelik ve etiket kendili\u011finden.",
          "Her yerden ekle: Ctrl+Alt+N")
    app.entry.delete(0, "end")
    app.update_preview()

    pinned = next(t for t in app.tasks if t.pinned)
    app.open_page(pinned.id)
    s.settle(400)
    slide("3-detay.png", s.grab(), "Bir g\u00f6rev, bir not defteri",
          "A\u00e7\u0131klama, alt g\u00f6revler, tarih, tekrar ve etiketler.\nHer de\u011fi\u015fiklik otomatik kaydedilir.")
    app.page_canvas.yview_moveto(0.0)
    app.toggle_calendar()
    s.settle(400)
    slide("4-takvim.png", s.grab(), "Takvim ve mail elinin alt\u0131nda",
          "Mini takvimle tarih se\u00e7, Google Takvim'e ya da\nOutlook'a tek t\u0131kla ekle, Gmail ile g\u00f6nder.")
    app.close_page()

    s.start(side="top", pos=420, cw=420, ch=600, pill=1.0, open_=False)
    slide("5-yatay.png", s.grab(), "Nereye istersen",
          "Sa\u011f, sol, \u00fcst ya da alt kenara s\u00fcr\u00fckle;\nsekmenin boyunu da sen ayarla.")

    s.start()
    s.app.open_menu(s.app.menu_btn)
    s.settle(300)
    s.app._menu.lift()                 # settle() raised the widget above the menu
    s.root.after(400, s.root.quit)
    s.root.mainloop()
    slide("6-ayarlar.png", s.grab(s.app._menu), "Senin d\u00fczenin",
          "Yerle\u015fim, boyut, saydaml\u0131k, takvim ve mail tercihleri.\nYapay zek\u00e2 asistanlar\u0131 i\u00e7in MCP deste\u011fi.")
    s.root.destroy()


if __name__ == "__main__":
    main()
