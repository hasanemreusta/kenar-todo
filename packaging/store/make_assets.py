"""Store/MSIX image assets from packaging/logo.png (needs Pillow). Writes packaging/store/Assets/."""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(os.path.dirname(HERE), "logo.png")
OUT = os.path.join(HERE, "Assets")

# name -> (width, height, logo fraction of the shorter side)
ASSETS = {
    "StoreLogo.png": (50, 50, 1.0),
    "Square44x44Logo.png": (44, 44, 1.0),
    "Square44x44Logo.targetsize-16.png": (16, 16, 1.0),
    "Square44x44Logo.targetsize-24.png": (24, 24, 1.0),
    "Square44x44Logo.targetsize-32.png": (32, 32, 1.0),
    "Square44x44Logo.targetsize-48.png": (48, 48, 1.0),
    "Square44x44Logo.targetsize-256.png": (256, 256, 1.0),
    "Square44x44Logo.targetsize-16_altform-unplated.png": (16, 16, 1.0),
    "Square44x44Logo.targetsize-24_altform-unplated.png": (24, 24, 1.0),
    "Square44x44Logo.targetsize-32_altform-unplated.png": (32, 32, 1.0),
    "Square44x44Logo.targetsize-48_altform-unplated.png": (48, 48, 1.0),
    "Square44x44Logo.targetsize-256_altform-unplated.png": (256, 256, 1.0),
    "Square150x150Logo.png": (150, 150, 0.72),
    "Wide310x150Logo.png": (310, 150, 0.72),
    "LargeTile.png": (310, 310, 0.62),
    "SplashScreen.png": (620, 300, 0.6),
    "StoreListingLogo300.png": (300, 300, 1.0),     # for the Partner Center listing, not the package
}


def render(w, h, fraction):
    logo = Image.open(LOGO).convert("RGBA")
    side = round(min(w, h) * fraction)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(logo.resize((side, side), Image.LANCZOS), ((w - side) // 2, (h - side) // 2))
    return canvas


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, (w, h, fraction) in ASSETS.items():
        render(w, h, fraction).save(os.path.join(OUT, name))
    print(f"{len(ASSETS)} assets written to {OUT}")
