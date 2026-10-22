"""Build the Microsoft Store package (unsigned .msix; the Store signs it on submission).

    python packaging/build.py              # first: dist/Todo.exe
    python packaging/store/make_assets.py  # once: tile and logo images
    python packaging/store/build_msix.py   # -> dist/store/Todo.msix

Identity values come from packaging/store/identity.json (copy them from Partner Center > Product identity).
"""
import glob
import json
import os
import shutil
import subprocess
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LAYOUT = os.path.join(ROOT, "build", "msix-layout")
OUT = os.path.join(ROOT, "dist", "store")


def makeappx():
    found = sorted(glob.glob(r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe"))
    if not found:
        raise SystemExit("makeappx.exe not found: install the Windows SDK")
    return found[-1]


def main():
    with open(os.path.join(HERE, "identity.json"), encoding="utf-8") as f:
        identity = {k: escape(v) for k, v in json.load(f).items() if not k.startswith("_")}
    exe = os.path.join(ROOT, "dist", "Todo.exe")
    if not os.path.exists(exe):
        raise SystemExit("dist/Todo.exe missing: run packaging/build.py first")
    shutil.rmtree(LAYOUT, ignore_errors=True)
    os.makedirs(os.path.join(LAYOUT, "Assets"))
    shutil.copy2(exe, LAYOUT)
    for path in glob.glob(os.path.join(HERE, "Assets", "*.png")):
        if not os.path.basename(path).startswith("StoreListing"):
            shutil.copy2(path, os.path.join(LAYOUT, "Assets"))
    with open(os.path.join(HERE, "AppxManifest.template.xml"), encoding="utf-8") as f:
        manifest = f.read().format(**identity)
    with open(os.path.join(LAYOUT, "AppxManifest.xml"), "w", encoding="utf-8") as f:
        f.write(manifest)
    os.makedirs(OUT, exist_ok=True)
    target = os.path.join(OUT, "Todo.msix")
    subprocess.run([makeappx(), "pack", "/d", LAYOUT, "/p", target, "/o"], check=True)
    print("written", target)


if __name__ == "__main__":
    main()
