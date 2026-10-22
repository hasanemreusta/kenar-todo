"""Build the Windows executables with PyInstaller.

    python packaging/build.py

Outputs dist/Todo.exe (the widget, no console) and dist/Todo-MCP.exe (stdio MCP server for AI assistants).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "packaging")


def pyinstaller(*args):
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
           "--distpath", os.path.join(ROOT, "dist"), "--workpath", os.path.join(ROOT, "build"),
           "--specpath", os.path.join(ROOT, "build"), "--paths", ROOT, *args]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)


if __name__ == "__main__":
    icon = os.path.join(PKG, "todo.ico")
    if not os.path.exists(icon):
        subprocess.run([sys.executable, os.path.join(PKG, "make_icon.py")], check=True)
    pyinstaller("--windowed", "--name", "Todo", "--icon", icon, os.path.join(PKG, "launch_widget.py"))
    pyinstaller("--console", "--name", "Todo-MCP", "--icon", icon, os.path.join(PKG, "launch_mcp.py"))
    print("done: dist/Todo.exe, dist/Todo-MCP.exe")
