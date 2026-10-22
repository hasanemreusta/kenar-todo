"""Draw the app logo and icon: a dark squircle, a green gradient check badge and the docked side pill.

Build-time only (needs Pillow). Writes packaging/todo.ico (multi-size), todo.png (512) and logo.png (1024).
"""
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1024          # master size; everything is drawn 4x larger and scaled down for smooth edges
X = 4


def vertical_gradient(size, top, bottom):
    w, h = size
    grad = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        grad.putpixel((0, y), tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(4)))
    return grad.resize((w, h))


def diagonal_gradient(size, a, b):
    w, h = size
    small = Image.new("RGBA", (64, 64))
    for y in range(64):
        for x in range(64):
            t = (x + y) / 126
            small.putpixel((x, y), tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(4)))
    return small.resize((w, h), Image.BICUBIC)


def mask_of(size, draw_fn):
    m = Image.new("L", size, 0)
    draw_fn(ImageDraw.Draw(m))
    return m


def logo():
    n = S * X
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))

    # squircle base with a soft vertical gradient and a hairline border
    pad, radius = 56 * X, 236 * X
    base_mask = mask_of((n, n), lambda d: d.rounded_rectangle((pad, pad, n - pad, n - pad), radius, fill=255))
    img.paste(vertical_gradient((n, n), (30, 31, 38, 255), (9, 9, 11, 255)), (0, 0), base_mask)
    inner = mask_of((n, n), lambda d: d.rounded_rectangle((pad + 6 * X, pad + 6 * X, n - pad - 6 * X, n - pad - 6 * X),
                                                          radius - 6 * X, fill=255))
    border = ImageChops.subtract(base_mask, inner)
    img.paste((58, 58, 66, 255), (0, 0), border)

    # the docked side pill (the app's signature) on the right
    px0, py0, px1, py1 = 700 * X, 250 * X, 790 * X, 774 * X
    pill = mask_of((n, n), lambda d: d.rounded_rectangle((px0, py0, px1, py1), 45 * X, fill=255))
    img.paste((44, 45, 52, 255), (0, 0), pill)
    for i, color in enumerate(((255, 200, 87, 255), (255, 123, 123, 255), (232, 232, 234, 255))):
        cy = (430 + i * 110) * X
        dot = mask_of((n, n), lambda d, cy=cy: d.ellipse((745 * X - 17 * X, cy - 17 * X, 745 * X + 17 * X, cy + 17 * X),
                                                          fill=255))
        img.paste(color, (0, 0), dot)
    plus = mask_of((n, n), lambda d: d.ellipse((745 * X - 30 * X, 290 * X, 745 * X + 30 * X, 350 * X), fill=255))
    img.paste((52, 210, 123, 255), (0, 0), plus)

    # green gradient check badge with a soft glow
    cx, cy, r = 420 * X, 512 * X, 230 * X
    badge = mask_of((n, n), lambda d: d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255))
    glow = Image.new("RGBA", (n, n), (52, 210, 123, 0))
    glow.putalpha(badge.point(lambda v: v * 90 // 255).filter(ImageFilter.GaussianBlur(60 * X)))
    img = Image.alpha_composite(img, glow)
    img.paste(diagonal_gradient((n, n), (88, 236, 152, 255), (22, 160, 92, 255)), (0, 0), badge)
    check = mask_of((n, n), lambda d: d.line([(cx - 110 * X, cy + 4 * X), (cx - 30 * X, cy + 86 * X),
                                              (cx + 120 * X, cy - 84 * X)], fill=255, width=64 * X, joint="curve"))
    caps = mask_of((n, n), lambda d: [d.ellipse((x - 32 * X, y - 32 * X, x + 32 * X, y + 32 * X), fill=255)
                                      for x, y in ((cx - 110 * X, cy + 4 * X), (cx + 120 * X, cy - 84 * X))])
    img.paste((8, 22, 14, 255), (0, 0), ImageChops.lighter(check, caps))
    return img.resize((S, S), Image.LANCZOS)


if __name__ == "__main__":
    art = logo()
    art.save(os.path.join(HERE, "logo.png"))
    art.resize((512, 512), Image.LANCZOS).save(os.path.join(HERE, "todo.png"))
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
    art.resize((256, 256), Image.LANCZOS).save(os.path.join(HERE, "todo.ico"), sizes=sizes)
    print("logo written")
